## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Rework the top post of the Epitrochoid refit with designed-in supports
("epi_top" in config/project.json).

1. The Nov 8 plug (25.36 / 19.96) is replaced by the current one from
   "connector" (split ring plug_od / plug_id, plug_len tall, as on the v2 tubes),
   the post's funnel bore under it opened to the plug bore for bore_z mm, the plug top kept
   at plug_z[1]. Its gap faces the exit window: cut from the plug top down
   through the shoulder into the window, its sides on the window's side faces
   (+-slot_half deg) so nothing overhangs, its two top corners rounded to slot_r
   along the ring.
2. The cone under the landing floor, whose point starts in midair, becomes a
   45 deg underside that starts on the exit-side wall at ramp_z0 and rises
   toward the back wall.
3. The slit between the right-hand track wall (looking at the window from
   outside) and the window edge is filled with a web whose top runs flat at
   fin.ztop from the post and then falls 45 deg along the wall until it meets
   the wall top. Each level is the convex hull of the wall section there, the
   window corner and a patch of post wall outside the window; consecutive levels
   are lofted by hull, so the web never reaches into the window or the track.

With "keel" set in the config the piece is first rebuilt by src/epi_keel.py (keel
under the track, tall trees dropped) instead of read from src.

Usage:
    python src/epi_top.py [--src STL] [--out STL] [--plain]
'''
import argparse
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, OpType
from shapely.geometry import MultiPoint, box

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rounds import slot_cutter
from project import load_cfg, root

SEG = 360


def to_manifold(path):
    t = trimesh.load(path)
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                         tri_verts=np.asarray(t.faces, np.uint32)))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))


def plug_parts(c, con):
    '''
    Cut and add that swap the old plug for the current one, shoulder top at plug_z[0].

    Returns:
        tuple: (cut, add) Manifolds
    '''
    p0, p1 = c['plug_z']
    rp     = con['plug_id'] / 2
    e      = 0.01
    ## old ring off; the post's funnel bore is kept and only its last step in, to the
    ## old 19.96 plug bore, is opened to the current plug bore
    cut = (Manifold.cylinder(p1 - p0 + 1, con['post_od'] / 2 + 1, con['post_od'] / 2 + 1, SEG).translate((0, 0, p0))
           + Manifold.cylinder(c['bore_z'] + e, rp, rp, SEG).translate((0, 0, p0 - c['bore_z'])))
    add = (Manifold.cylinder(p1 - p0 + e, con['plug_od'] / 2, con['plug_od'] / 2, SEG)
           - Manifold.cylinder(p1 - p0 + 1, con['plug_id'] / 2, con['plug_id'] / 2, SEG).translate((0, 0, -0.5))).translate((0, 0, p0 - e))
    return cut, add


def gap_cutter(c, con):
    '''
    New plug gap with radial sides at +-slot_half deg about the exit, the same
    angle as the window's side faces, so the window runs straight up through the
    shoulder and plug with no ledge. The profile is laid out along the ring
    (s = plug radius * angle) and wrapped, which gives the two top corners a slot_r
    round measured on the outside of the plug.
    '''
    zb, zt = c['slot_zb'], c['plug_z'][1]
    rr     = c['post_ri'] + 2.0 + 1.0
    rf     = con['plug_od'] / 2
    s0     = rf * np.radians(c['slot_half'])
    wrap   = slot_cutter(con['plug_id'] / 2 - 1.0, rr, 0.0, zb, zt, 2 * s0, c['slot_r'])
    wrap   = wrap.refine_to_length(0.4)
    wrap   = wrap.warp_batch(lambda v: np.c_[v[:, 0] * np.cos(v[:, 1] / rf),
                                             v[:, 0] * np.sin(v[:, 1] / rf), v[:, 2]])
    return wrap.rotate((0, 0, c['exit']))


def ramp_parts(c):
    '''
    Cut (cone below the new underside) and fill (above it, up to cone_top) for the landing floor.

    The underside is the plane z = ramp_z0 + post_ri + u, u running from the exit-side
    wall (u = -post_ri) to the back wall (u = +post_ri).
    '''
    ri, e = c['post_ri'], c['embed']
    z0    = c['ramp_z0']
    z1    = z0 + 2 * ri + 1.0
    a     = np.radians(c['exit'])
    ## plane through (exit-side wall, z0) rising 45 deg away from the exit
    n     = np.array([np.cos(a), np.sin(a), 1.0]) / np.sqrt(2)
    off   = (z0 + ri) / np.sqrt(2)
    ## the cut stops 0.05 short of the wall (no coincident faces); the fill reaches embed into it
    rc    = ri + c.get('cut_r', -0.05)
    cut   = Manifold.cylinder(z1 - z0 + 2, rc, rc, SEG).translate((0, 0, z0 - 1))
    cyl   = Manifold.cylinder(z1 - z0 + 2, ri + e, ri + e, SEG).translate((0, 0, z0 - 1))
    below = cut.trim_by_plane(-n, -off)
    above = cyl.trim_by_plane(n, off) ^ Manifold.cube((60, 60, c['cone_top'] - z0 + 1)).translate((-30, -30, z0 - 1))
    return below, above


def under_floor(m, c):
    '''
    Fill the gap between the landing floor's underside and the 45 deg ramp plane
    (the floor dips to about 14 deg there): inside the bore, above the plane and
    below floor_top, everything is made solid except the landing space over the
    floor (the empty piece holding the point land_u mm toward the exit at height
    land_z), which is kept with its outline moved seam mm down, so the fill ends
    inside the floor and the floor top and window are unchanged.
    '''
    ri, z0, zt = c['post_ri'], c['ramp_z0'], c['floor_top']
    a      = np.radians(c['exit'])
    n      = np.array([np.cos(a), np.sin(a), 1.0]) / np.sqrt(2)
    off    = (z0 + ri) / np.sqrt(2)

    def region(top, rr):
        r = Manifold.cylinder(top - z0 + 1, rr, rr, SEG).translate((0, 0, z0 - 1)).trim_by_plane(n, off)
        return r ^ Manifold.cube((60, 60, top - z0 + 1)).translate((-30, -30, z0 - 1))

    lx, ly = c['land_u'] * np.cos(a), c['land_u'] * np.sin(a)
    probe  = Manifold.cube((0.2, 0.2, 0.2)).translate((lx - 0.1, ly - 0.1, c['land_z'] - 0.1))
    ## the landing space is found in a wider and taller region, so its outline never lies on the fill's
    land   = [p for p in (region(zt + 2 * c['seam'], ri + c['embed'] + 1.0) - m).decompose() if (p ^ probe).volume() > 1e-6]
    if not land:
        return Manifold()
    return region(zt, ri + c['embed']) - land[0].translate((0, 0, -c['seam']))


def exit_bracket(c, t):
    '''
    Bracket under the flat start of the track outside the exit window: in the sector
    ang (deg) and out to r_out, under every bit of track underside lower than z_max
    (found by rays up from z_from on a grid), solid up to embed mm into the track, its
    underside the 45 deg cone z = z_top - r_out + r about the post axis, so it grows
    out of the post wall and needs no support.
    '''
    b      = c['bracket']
    h, ro  = b['grid'], c['post_ro']
    xs     = np.arange(-b['r_out'], b['r_out'] + h, h)
    gx, gy = np.meshgrid(xs, xs, indexing='ij')
    r      = np.hypot(gx, gy)
    ang    = np.degrees(np.arctan2(gy, gx))
    sel    = (r > ro - b['embed']) & (r < b['r_out']) & (ang > b['ang'][0]) & (ang < b['ang'][1])
    P      = np.c_[gx[sel], gy[sel], np.full(sel.sum(), b['z_from'])]
    loc, ir, _ = t.ray.intersects_location(P, np.tile((0, 0, 1.0), (len(P), 1)), multiple_hits=False)
    zb     = np.full(len(P), np.inf); zb[ir] = loc[:, 2]
    k      = zb < b['z_max']
    if not k.any():
        return Manifold()
    za     = b['z_top'] - b['r_out']

    def columns(e):
        return Manifold.batch_boolean([Manifold.cube((h, h, z1 + e - b['z_from'])).translate((x - h / 2, y - h / 2, b['z_from']))
                                       for (x, y, _), z1 in zip(P[k], zb[k])], OpType.Add)

    ## up to the track underside, plus embed mm only where that is inside the piece (never through a thin floor)
    m      = Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    cols   = columns(0.0) + (columns(b['embed']) ^ m)
    ## inside the cone opening upward from (0, 0, za) at 45 deg
    zc     = b['z_max'] + 5.0
    cone   = Manifold.cylinder(zc - za, 0.0, zc - za, SEG).translate((0, 0, za))
    ## never inside the post wall above keep_z, so the window sill stays where it was
    wall   = Manifold.cylinder(zc - b['keep_z'] + 1, ro + b['wall_gap'], ro + b['wall_gap'], SEG).translate((0, 0, b['keep_z']))
    return (cols ^ cone) - wall


def fin(c, t):
    '''
    Web filling the slit between the track wall and the window edge (see module notes).

    Args:
        c (dict):            the epi_top config
        t (trimesh.Trimesh): the piece after the gap cut, for the wall sections

    Returns:
        Manifold: the web, in mesh coordinates
    '''
    f      = c['fin']
    a      = np.radians(c['exit'])
    rot    = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])     # xy -> (w, v)
    w0, w1, v0, v1 = f['box']
    ro     = c['post_ro']
    sd     = np.sign(f['side_deg'])
    ## window outer corner, then a patch of post wall just outside the window
    post   = [(r * np.cos(np.radians(d)), r * np.sin(np.radians(d))) for r, d in
              [(ro, sd * c['slot_half']), (ro, f['side_deg']), (ro - 1.3, f['side_deg'])]]
    wa     = post[0][0]
    zs     = np.arange(f['z0'], f['ztop'] + 1e-6, f['dz'])
    last   = None
    lv     = []
    for z in zs:
        pts = []
        s   = t.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if s is not None:
            for p in s.discrete:
                q = p[:, :2] @ rot.T
                k = ((q[:, 0] >= w0) & (q[:, 0] <= w1) & (q[:, 1] >= v0) & (q[:, 1] <= v1)
                     & (np.hypot(q[:, 0], q[:, 1]) >= ro))
                pts.append(q[k])
        pts  = np.vstack(pts) if pts else np.zeros((0, 2))
        last = pts if len(pts) else last
        ## hull of post patch and wall, cut at the 45 deg top: nothing farther out than wt at this height
        wt   = wa + (f['ztop'] - z)
        hp   = MultiPoint(np.vstack([post, last])).convex_hull & box(-50.0, -50.0, wt, 50.0)
        q    = np.asarray(hp.exterior.coords)[:-1]
        lv.append(np.c_[q, np.full(len(q), z)])
    parts = [Manifold.hull_points(np.vstack([lv[i], lv[i + 1]])) for i in range(len(lv) - 1)]
    web   = Manifold.batch_boolean(parts, OpType.Add)
    ## back from (w, v) to mesh xy
    return web.rotate((0, 0, c['exit']))


def main():
    cfg = load_cfg()
    c   = cfg['epi_top']
    ap  = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join(root, c['src']))
    ap.add_argument('--out', default=os.path.join(root, c['out']))
    ap.add_argument('--plain', action='store_true', help='no keel or trees, even with keel set (for slicer supports)')
    a   = ap.parse_args()

    if c.get('keel') and not a.plain:
        import epi_keel
        m, info = epi_keel.build(cfg)
        print('keel %.2f cm3, deepest %.2f mm, %d trees kept' % (info['keel_cm3'], info['deepest'], info['trees']))
    else:
        m = to_manifold(a.src)
    print('source volume %.2f cm3' % (m.volume() / 1000))

    below, above = ramp_parts(c)
    m = (m - below) + above
    if 'floor_top' in c:
        m = m + under_floor(m, c)
    if 'bracket' in c:
        m = m + exit_bracket(c, to_trimesh(m))
    con = cfg['connector']
    cut, add = plug_parts(c, con)
    m = (m - cut) + add
    m = m - gap_cutter(c, con)
    m = m + fin(c, to_trimesh(m))
    ## drop zero-volume slivers left where a tree tip meets the keel
    m = Manifold.batch_boolean([p for p in m.decompose() if p.volume() > 1.0], OpType.Add)
    print('new volume %.2f cm3, genus %d' % (m.volume() / 1000, m.genus()))

    t    = to_trimesh(m)
    f    = t.faces
    t.update_faces((f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2]))
    t.remove_unreferenced_vertices()
    t.export(a.out)
    print('wrote %s, %d faces, watertight %s, bounds %s' % (a.out, len(t.faces), t.is_watertight, np.round(t.bounds, 2).tolist()))


if __name__ == '__main__':
    main()
