'''
Refit imported Marbleworks pieces to the measured set ("refit" in config/project.json).

Each piece keeps its track. The run between its two posts is stretched or squeezed
to a measured span, heights are scaled from the source pitch to tube_pitch, and the
sockets and plugs are swapped for the fit-ladder connector. Options per piece or
post make undersides print without supports: a 45 deg keel under the track, a cone
ceiling in a socket nothing passes through, and a 45 deg pointed top on a window.

Usage:
    python src/refit.py [--pieces twopost_1loop clicky_5_half] [--span long] [--out stl/custom]
'''
import argparse
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import POST_OD, POST_ID, PLUG_ID, PLUG_LEN, SHOULDER, Piece, cyl, union, add_plug
from project import load_cfg, out_dirs


def span_map(s, s0, s1, ds, blend):
    '''
    Shift positions along the post-to-post axis: unchanged before s0, moved by ds
    after s1. The extra stretch ramps up over blend, holds, and ramps back down,
    so the track bends nowhere.

    Args:
        s     (ndarray): positions along the axis
        s0    (float):   start of the stretched run
        s1    (float):   end of the stretched run
        ds    (float):   change in length of the run, negative to squeeze
        blend (float):   length of each ramp

    Returns:
        ndarray: the new positions
    '''
    run = s1 - s0
    g   = ds / (run - blend)
    t   = np.clip(s - s0, 0, run)
    up  = np.clip(t, 0, blend)
    mid = np.clip(t - blend, 0, run - 2 * blend)
    dn  = np.clip(t - (run - blend), 0, blend)
    return s + g * (up ** 2 / (2 * blend) + mid + dn - dn ** 2 / (2 * blend))


def load_body(path):
    '''
    Largest shell of an imported STL, facing outward (the imports carry stray slivers).

    Args:
        path (str): STL file

    Returns:
        trimesh.Trimesh: the main body
    '''
    body = max(trimesh.load(path).split(only_watertight=False), key=lambda b: abs(b.volume))
    if body.volume < 0:
        body.invert()
    return body


def warp(body, pa, pb, span, zs, rigid, blend):
    '''
    Stretch a body along the axis pa -> pb to a new post spacing and scale its heights.

    Args:
        body  (trimesh.Trimesh): source body
        pa    (ndarray): first post axis (x, y)
        pb    (ndarray): second post axis (x, y), moves away from or toward pa
        span  (float):   new centre-to-centre spacing
        zs    (float):   height scale
        rigid (float):   distance from each post axis left unstretched
        blend (float):   ramp length of the stretch

    Returns:
        Manifold: the warped body, with pa unmoved
    '''
    dist = np.linalg.norm(pb - pa)
    u    = (pb - pa) / dist
    v    = np.array(body.vertices, float)
    s    = (v[:, :2] - pa) @ u
    v[:, :2] += np.outer(span_map(s, rigid, dist - rigid, span - dist, blend) - s, u)
    v[:, 2]  *= zs
    return Manifold(Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(body.faces, np.uint32)))


def to_tm(m):
    '''
    Manifold as a trimesh, for ray casts.
    '''
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts), process=False)


def under(tm, pts, z_from):
    '''
    Height of the first surface above z_from at each point.

    Args:
        tm     (trimesh.Trimesh): piece
        pts    (ndarray): (n, 2) points in plan
        z_from (float):   height the rays start from

    Returns:
        ndarray: heights, inf where nothing is above
    '''
    o = np.c_[pts, np.full(len(pts), z_from)]
    loc, ir, _ = tm.ray.intersects_location(o, np.tile((0.0, 0.0, 1.0), (len(o), 1)), multiple_hits=False)
    z = np.full(len(pts), np.inf)
    z[ir] = loc[:, 2]
    return z


def despike(z, jump=0.5):
    '''
    Height grid with lone outliers replaced by the median of their neighbours. A ray
    that lands exactly on a mesh edge misses it and reports the next surface up, or none.

    Args:
        z    (ndarray): 2D height grid, inf where nothing was hit
        jump (float):   how far above its neighbours a value must sit to be replaced

    Returns:
        ndarray: the cleaned grid
    '''
    big = 1e6
    zf  = np.where(np.isfinite(z), z, big)
    med = ndimage.median_filter(zf, size=3, mode='nearest')
    out = np.where((zf - med > jump) & (med < big / 2), med, zf)
    return np.where(out < big / 2, out, np.inf)


def slab(xs, ys, zb, zt):
    '''
    Solid between two height grids over the rectangle xs x ys.

    Args:
        xs, ys (ndarray): increasing grid coordinates
        zb, zt (ndarray): (len(xs), len(ys)) bottom and top heights, zb < zt everywhere

    Returns:
        Manifold: the solid
    '''
    nx, ny = len(xs), len(ys)
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    v      = np.vstack([np.c_[gx.ravel(), gy.ravel(), zb.ravel()], np.c_[gx.ravel(), gy.ravel(), zt.ravel()]])
    n      = nx * ny
    k      = np.arange(n).reshape(nx, ny)
    a, b, c, d = k[:-1, :-1].ravel(), k[1:, :-1].ravel(), k[1:, 1:].ravel(), k[:-1, 1:].ravel()
    f      = [np.c_[a, c, b], np.c_[a, d, c], np.c_[a, b, c] + n, np.c_[a, c, d] + n]
    ## side walls: (first corner, second corner, flip) along each edge of the grid
    for p, q, flip in ((k[:-1, 0], k[1:, 0], False), (k[:-1, -1], k[1:, -1], True),
                       (k[0, :-1], k[0, 1:], True), (k[-1, :-1], k[-1, 1:], False)):
        p, q = (q, p) if flip else (p, q)
        f   += [np.c_[p, q, q + n], np.c_[p, q + n, p + n]]
    return Manifold(Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(np.vstack(f), np.uint32)))


def wedge(x, y, direction, half, z0, z1, r):
    '''
    Sector of a cylinder about a post axis: directions direction +/- half degrees, radius r.
    '''
    a0, a1 = np.radians(direction - half), np.radians(direction + half)
    far    = 1.1 * r / np.cos(np.radians(half))
    tri    = Manifold.hull_points(np.array([(x + k * np.cos(a), y + k * np.sin(a), z)
                                            for z in (z0, z1) for k, a in ((0, a0), (far, a0), (far, a1))]))
    return tri ^ cyl(z1 - z0, r, x, y, z0)


def connector(x, y, z0, z1, slot, src_id, socket_len, lead=True, relief=None):
    '''
    Fit-ladder connector for one post of a warped body.

    Args:
        x, y       (float): post axis
        z0         (float): post bottom
        z1         (float): post body top, where the plug starts
        slot       (float): direction of the plug slot, degrees from +x
        src_id     (float): socket bore of the source piece
        socket_len (float): length of the narrowed socket
        lead       (bool):  45 deg lead-out on top of the socket sleeve
        relief     (float): half width in degrees of a gap left in the shoulder, where the source
                            slot opens into a window below it, so the slot runs on to the top

    Returns:
        tuple: (cut, add) manifolds: the source plug to remove, the sleeve and plug to add
    '''
    e    = 0.01
    ## source plug: all of it outside the new plug bore, so a floor curve reaching up inside the bore stays
    cut  = cyl(PLUG_LEN + 20, POST_OD / 2 + 1, x, y, z1) - cyl(PLUG_LEN + 22, PLUG_ID / 2, x, y, z1 - 1)
    pc   = Piece()
    add_plug(pc, 0, 0, z1)
    plug = union(pc.late).rotate((0, 0, slot)).translate((x, y, 0))
    if relief:
        plug = plug - wedge(x, y, slot, relief, z1 - SHOULDER - e, z1 + e, POST_OD)
    ## sleeve narrowing the source socket to the fit-ladder bore, 45 deg lead-out on top so nothing catches or overhangs
    ro   = src_id / 2 + 0.1
    top  = ro - POST_ID / 2 if lead else 0.0
    slv  = cyl(socket_len + top, ro, x, y, z0) - cyl(socket_len + 2 * e, POST_ID / 2, x, y, z0 - e)
    if lead:
        slv = slv - cyl(top + e, POST_ID / 2, x, y, z0 + socket_len, r2=ro + e)
    return cut, plug + slv


def wall_sector(m, x, y, z0, z1, direction, half, turn):
    '''
    A sector of post wall to close an opening with: the post's own wall from turn
    degrees away, swung to face direction.

    Args:
        m         (Manifold): warped body with the source plug removed
        x, y      (float):    post axis
        z0, z1    (float):    height range of the sector
        direction (float):    direction of the opening, degrees from +x
        half      (float):    half width of the sector, degrees
        turn      (float):    where the wall is taken from, degrees before direction

    Returns:
        Manifold: the wall sector, to be added to m
    '''
    r    = POST_OD / 2 + 3
    zone = (m ^ cyl(z1 - z0, r, x, y, z0)).translate((-x, -y, 0)).rotate((0, 0, turn)).translate((x, y, 0))
    return zone ^ wedge(x, y, direction, half, z0, z1, r)


def gable(x, y, direction, zp, drop, notch, depth, r):
    '''
    The two halves of a 45 deg pointed window top facing direction, peak at zp.

    Args:
        x, y      (float): post axis
        direction (float): direction the window faces, degrees from +x
        zp        (float): height of the peak
        drop      (float): how far below the peak the two lines run
        notch     (float): half width of the shape under them
        depth     (float): how far below the peak the shape under them runs
        r         (float): how far from the axis it reaches

    Returns:
        tuple: (above, below) manifolds: everything over the two 45 deg lines up to
               zp + 2, and what lies under them within notch of the centre line
    '''
    top   = zp + 2.0
    quad  = [(0, zp), (drop, zp - drop), (drop, top), (0, top)]
    above = union([Manifold.hull_points(np.array([(k, s * t, z) for k in (0, r) for t, z in quad])) for s in (-1, 1)])
    below = Manifold.hull_points(np.array([(k, t, z) for k in (0, r) for t, z in
                                           ((0, zp), (-notch, zp - notch), (notch, zp - notch), (-notch, zp - depth), (notch, zp - depth))]))
    place = lambda g: g.rotate((0, 0, direction)).translate((x, y, 0))
    return place(above), place(below)


def ceiling(m, x, y, z_sock, src_id, cc):
    '''
    45 deg cone ceiling over a socket nothing passes through, from the socket wall at
    z_sock to a point on the axis: solid above the cone up to the underside that was
    there, and that underside cut back where the cone runs above it.

    Args:
        m      (Manifold): piece with its connectors
        x, y   (float):    post axis
        z_sock (float):    height where the cone leaves the socket wall
        src_id (float):    bore of the source piece
        cc     (dict):     "ceiling" block of the config

    Returns:
        tuple: (fill, cut) manifolds: add the fill, then remove the cut
    '''
    rw     = src_id / 2 + 0.1
    ri     = POST_ID / 2
    g      = np.arange(-rw - cc['step'], rw + cc['step'] + 1e-9, cc['step'])
    gx, gy = np.meshgrid(g, g, indexing='ij')
    rr     = np.hypot(gx, gy)
    tm     = to_tm(m)
    o      = np.c_[gx.ravel() + x, gy.ravel() + y, np.full(gx.size, z_sock + 0.2)]
    loc, ir, _ = tm.ray.intersects_location(o, np.tile((0.0, 0.0, 1.0), (len(o), 1)), multiple_hits=True)
    ## first surface above the socket is the underside, the second is the top of the floor over it
    zl, zt = np.full(gx.size, np.inf), np.full(gx.size, np.inf)
    for i in np.unique(ir):
        z = np.sort(loc[ir == i, 2])
        zl[i], zt[i] = z[0], z[1] if len(z) > 1 else np.inf
    zl, zt = despike(zl.reshape(gx.shape)), despike(zt.reshape(gx.shape))
    ## outside the bore the rays start in the wall: take the nearest value from inside
    ok     = (rr < ri - 0.3) & np.isfinite(zl)
    near   = tuple(ndimage.distance_transform_edt(~ok, return_distances=False, return_indices=True))
    zl     = zl[near]
    cone   = z_sock + ri - rr
    left   = (zt - np.maximum(cone, zl))[ok & np.isfinite(zt)]
    if left.min() < cc['floor']:
        raise ValueError(f'cone ceiling would leave only {left.min():.2f} mm of floor')
    fill   = slab(g + x, g + y, np.minimum(cone, zl) - 0.5, zl + cc['embed']) ^ cyl(4 * rw, rw, x, y, z_sock - 2)
    return fill, Manifold.cylinder(ri, ri, 0).translate((x, y, z_sock))


def keel(m, pa, u, span, r_post, kc):
    '''
    45 deg keel under the track between the posts: at each station the space below the
    underside from which both 45 deg rays across the track still meet it.

    Args:
        m      (Manifold): piece with its connectors
        pa     (ndarray):  first post axis (x, y)
        u      (ndarray):  unit vector from the first post to the second
        span   (float):    centre-to-centre spacing of the posts
        r_post (float):    outer radius of the posts
        kc     (dict):     "keel" block of the config

    Returns:
        Manifold: the keel, to be added to m
    '''
    n      = np.array((-u[1], u[0]))
    ss     = np.arange(r_post + 0.3, span - r_post - 0.3 + 1e-9, kc['step'])
    ts     = np.arange(-kc['reach'], kc['reach'] + 1e-9, 0.4)
    gs, gt = np.meshgrid(ss, ts, indexing='ij')
    zl     = despike(under(to_tm(m), pa + gs.reshape(-1, 1) * u + gt.reshape(-1, 1) * n, -1.0).reshape(gs.shape))
    inf    = np.full((len(ss), 1), np.inf)
    gp     = np.c_[np.minimum.accumulate((zl - ts)[:, ::-1], axis=1)[:, ::-1][:, 1:], inf] + ts
    gm     = np.c_[inf, np.minimum.accumulate(zl + ts, axis=1)[:, :-1]] - ts
    zk     = np.maximum(gp, gm)
    on     = np.isfinite(zl) & (zk < zl - 0.05)
    half   = max(np.abs(ts[r]).max() for r in on if r.any())
    sel    = np.abs(ts) <= half + 1e-9
    zl, zb = zl[:, sel], np.minimum(zk, zl)[:, sel]
    if not np.isfinite(zl).all():
        raise ValueError('track underside not found across the whole keel width')
    ## run the ends a little way into the post walls along the local slope, so the keel is one with them
    k      = int(np.ceil((0.3 + kc['into']) / kc['step']))
    j      = np.arange(1, k + 1)[:, None]
    mid    = sel.sum() // 2
    d0, d1 = (zl[6, mid] - zl[0, mid]) / 6, (zl[-1, mid] - zl[-7, mid]) / 6
    ss     = np.r_[ss[0] - j[::-1, 0] * kc['step'], ss, ss[-1] + j[:, 0] * kc['step']]
    zl     = np.vstack([zl[0] - d0 * j[::-1], zl, zl[-1] + d1 * j])
    zb     = np.vstack([zb[0] - d0 * j[::-1], zb, zb[-1] + d1 * j])
    if zb.min() < 0.6:
        raise ValueError('keel reaches the bed')
    out = slab(ss, ts[sel], zb, zl + kc['embed'])
    return out.rotate((0, 0, float(np.degrees(np.arctan2(u[1], u[0]))))).translate((pa[0], pa[1], 0))


def refit(path, piece, span, pitch, rf):
    '''
    Refit one imported piece.

    Args:
        path  (str):   source STL
        piece (dict):  its entry in the "refit" block: two posts and options
        span  (float): new centre-to-centre spacing of the two posts
        pitch (float): height of one level in the measured set
        rf    (dict):  "refit" block of the config

    Returns:
        tuple: (Manifold, dict of the new post axes and levels)
    '''
    pa, pb = (np.array(p['xy'], float) for p in piece['posts'])
    u      = (pb - pa) / np.linalg.norm(pb - pa)
    zs     = pitch / rf['src_pitch']
    r_post = rf['src_od'] / 2
    m      = warp(load_body(path), pa, pb, span, zs, rf['rigid'], rf['blend'])
    posts  = [dict(p, xy=tuple(q), z0=p['levels'][0] * pitch, z1=p['levels'][1] * pitch)
              for p, q in zip(piece['posts'], (pa, pa + u * span))]
    cuts, adds = [], []
    for p in posts:
        dead = p.get('ceiling', False)
        c, a = connector(*p['xy'], p['z0'], p['z1'], p['slot'], rf['src_socket'], rf['socket_len'],
                         lead=not dead, relief=None if p['slot_depth'] else rf['open_half'])
        cuts.append(c)
        adds.append(a)
    m = m - union(cuts)
    ## a source plug slot that ends in the wall below the plug base is closed, or the new shoulder bridges a hole
    sf    = rf['slot_fill']
    fills = [wall_sector(m, *p['xy'], p['z1'] - p['slot_depth'] * zs, p['z1'], p['slot'], sf['half'], sf['turn'])
             for p in posts if p['slot_depth']]
    ## a window top becomes a 45 deg point just under the shoulder: wall added over the two lines, cut away under them
    for p in posts:
        if 'gable' in p:
            d, half, turn, drop, notch = p['gable']
            zp = p['z1'] - SHOULDER - 1.0
            above, below = gable(*p['xy'], d, zp, drop, notch, notch, r_post + 1)
            fills.append(wall_sector(m, *p['xy'], zp - drop, zp + 2.0, d, half, turn) ^ above)
            m = m - (below ^ wedge(*p['xy'], d, half, zp - notch, zp, r_post + 1) - cyl(notch + 1, POST_ID / 2 - 2.5, *p['xy'], zp - notch - 0.5))
    ## a round window top that runs into the open slot: its shallow shoulders are cut back to 45 deg lines
    for p in posts:
        if 'arch' in p:
            d, rise, half_w, depth = p['arch']
            cap = p['z1'] - SHOULDER
            _, below = gable(*p['xy'], d, p['z1'] + rise, 0.0, half_w, depth, r_post + 1)
            m = m - (below ^ cyl(cap - (p['z1'] + rise - depth), r_post + 1, *p['xy'], p['z1'] + rise - depth) - cyl(depth + 1, POST_ID / 2 - 2.5, *p['xy'], p['z1'] + rise - depth - 0.5))
    m = m + union(fills + adds)
    for p in posts:
        if p.get('ceiling', False):
            fill, cut = ceiling(m, *p['xy'], p['z0'] + rf['socket_len'], rf['src_socket'], rf['ceiling'])
            m = m + fill - cut
    if piece.get('keel', False):
        m = m + keel(m, pa, u, span, r_post, rf['keel'])
    ## drop slivers left where the cuts meet the source surface
    m = max(m.decompose(), key=lambda p: p.volume())
    return m, dict(posts=[tuple(np.round(p['xy'], 2)) for p in posts], span=span, pitch=pitch)


def save(m, path):
    '''
    Export a manifold as STL and return the mesh as a slicer will read it.

    Args:
        m    (Manifold): piece to export
        path (str):      STL file to write

    Returns:
        trimesh.Trimesh: the exported mesh
    '''
    mesh = m.to_mesh()
    t    = trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))
    ## vertex merging can collapse a sliver face onto an edge (a repeated vertex): drop those
    f = t.faces
    t.update_faces((f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2]))
    t.remove_unreferenced_vertices()
    t.export(path)
    return t


def main():
    cfg  = load_cfg()
    dirs = out_dirs(cfg)
    rf   = cfg['refit']
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pieces', nargs='+', default=list(rf['pieces']))        # imported piece names
    ap.add_argument('--span'  , default='long', choices=[k for k in cfg['spans'] if not k.startswith('_')])
    ap.add_argument('--src'   , default=dirs['marbleworks'])                  # imported STLs
    ap.add_argument('--out'   , default=dirs['custom'])                       # printable STLs
    a = ap.parse_args()
    sp = cfg['spans'][a.span]
    if 'centre' not in sp:
        ap.error(f'span "{a.span}" has no centre spacing in the config yet')
    for name in a.pieces:
        m, info = refit(os.path.join(a.src, name + '.stl'), rf['pieces'][name], sp['centre'], cfg['tube_pitch'], rf)
        k = name + sp['suffix']
        t = save(m, f'{a.out}/{k}.stl')
        print(k, 'watertight', t.is_watertight, 'bodies', len(t.split(only_watertight=False)),
              'extents', np.round(t.extents, 1), 'vol cm3', round(t.volume / 1000, 1), info)


if __name__ == '__main__':
    main()
