'''
Receiver dot width sweep on the densest inch of the Kilauea relief.

Finds the tile_mm square of the 190 mm Kilauea model holding the most
stations, rebuilds its bare terrain from the model mesh (dots removed and
filled), then makes one tile per dot width with raised dots at the station
positions, the width cut into the south wall, and all tiles laid out on one
plate as a 3MF.

Usage:
    python dot_width_sweep.py [config.json]
'''
import argparse
import json
import os
import subprocess
import sys

import manifold3d as m3d
import numpy as np
import trimesh
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

rec = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])


def load_stl(path):
    '''
    Read a binary STL and merge bit-identical vertices.

    Args:
        path (str): binary STL

    Returns:
        tuple: vertices (n, 3) [mm], faces (m, 3)
    '''
    raw  = np.fromfile(path, dtype=np.uint8)
    n    = int(raw[80:84].view(np.uint32)[0])
    tri  = np.frombuffer(raw[84:84 + 50 * n].tobytes(), dtype=rec)['v']
    u, i = np.unique(tri.reshape(-1, 3), axis=0, return_inverse=True)
    return u.astype(np.float64), i.reshape(-1, 3)


def load_stations(path, origin, m_per_mm, merge):
    '''
    Station positions in model mm, co-located stations merged.

    Args:
        path     (str):   station meta table (utm_e, utm_n in columns 4, 5)
        origin   (list):  model origin [E, N] [m]
        m_per_mm (float): ground metres per model mm
        merge    (float): stations closer than this become one dot [mm]

    Returns:
        ndarray: (n, 2) positions [mm]
    '''
    utm  = np.genfromtxt(os.path.expanduser(path), comments='#', skip_header=4, usecols=(4, 5))
    xy   = (utm - np.asarray(origin)) / m_per_mm
    keep = np.ones(len(xy), bool)
    for i, j in sorted(cKDTree(xy).query_pairs(merge)):
        if keep[i]:
            keep[j] = False
    return xy[keep]


def densest_window(xy, size, margin, step, extent):
    '''
    Lower-left corner of the size x size square holding the most stations
    at least margin inside its edges.

    Returns:
        tuple: (x0, y0) [mm], station count
    '''
    best = (-1, 0.0, 0.0)
    for x0 in np.arange(0.0, extent - size + 1e-9, step):
        for y0 in np.arange(0.0, extent - size + 1e-9, step):
            k = ((xy[:, 0] > x0 + margin) & (xy[:, 0] < x0 + size - margin) &
                 (xy[:, 1] > y0 + margin) & (xy[:, 1] < y0 + size - margin)).sum()
            if k > best[0]:
                best = (k, x0, y0)
    return (best[1], best[2]), best[0]


def bare_terrain(V, F, x0, y0, size, cell):
    '''
    Terrain heights on a grid over the window with the model's dots removed.
    Dots are the connected groups of vertical faces other than the side wall;
    their top caps are dropped and the gaps filled by linear interpolation.

    Returns:
        tuple: grid x (nx,), grid y (ny,), heights (ny, nx) [mm]
    '''
    cr   = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    nl   = np.linalg.norm(cr, axis=1)
    nz   = np.where(nl > 0, cr[:, 2] / np.maximum(nl, 1e-300), 0.0)
    vert = np.where(np.abs(nz) < 0.02)[0]
    fv   = F[vert]
    G    = coo_matrix((np.ones(3 * len(fv)), (np.r_[fv[:, 0], fv[:, 1], fv[:, 2]],
                                              np.r_[fv[:, 1], fv[:, 2], fv[:, 0]])), shape=(len(V),) * 2)
    _, lab = connected_components(G, directed=False)
    flab   = lab[fv[:, 0]]
    comps, cnt = np.unique(flab, return_counts=True)
    dotv   = np.zeros(len(V), bool)
    dotv[np.unique(fv[flab != comps[cnt.argmax()]])] = True

    ## terrain = upward faces that are not dot caps, inside the window plus a pad
    up   = (nz > 0.1) & ~dotv[F].all(1)
    tv   = np.unique(F[up])
    p    = V[tv]
    pad  = 1.0
    sel  = ((p[:, 0] > x0 - pad) & (p[:, 0] < x0 + size + pad) &
            (p[:, 1] > y0 - pad) & (p[:, 1] < y0 + size + pad))
    p    = p[sel]
    gx   = x0 + np.linspace(0.0, size, int(round(size / cell)) + 1)
    gy   = y0 + np.linspace(0.0, size, int(round(size / cell)) + 1)
    X, Y = np.meshgrid(gx, gy)
    Z    = LinearNDInterpolator(p[:, :2], p[:, 2])(X, Y)
    bad  = np.isnan(Z)
    Z[bad] = NearestNDInterpolator(p[:, :2], p[:, 2])(X[bad], Y[bad])
    return gx, gy, Z


def heightfield_solid(gx, gy, Z):
    '''
    Watertight solid: heightfield top, flat underside at z = 0, vertical walls.

    Returns:
        m3d.Manifold
    '''
    ny, nx = Z.shape
    X, Y   = np.meshgrid(gx, gy)
    top    = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
    bot    = np.c_[X.ravel(), Y.ravel(), np.zeros(nx * ny)]
    idx    = np.arange(nx * ny).reshape(ny, nx)
    a, b   = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel()
    c, d   = idx[1:, :-1].ravel(), idx[1:, 1:].ravel()
    ft     = np.r_[np.c_[a, b, d], np.c_[a, d, c]]
    off    = nx * ny
    fb     = ft[:, ::-1] + off
    ## walls: walk the boundary counter-clockwise seen from above
    ring   = np.r_[idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]
    r2     = np.roll(ring, -1)
    fw     = np.r_[np.c_[ring, r2 + off, r2], np.c_[ring, ring + off, r2 + off]]
    Vs     = np.r_[top, bot].astype(np.float32)
    Fs     = np.r_[ft, fb, fw].astype(np.uint32)
    M      = m3d.Manifold(m3d.Mesh(vert_properties=Vs, tri_verts=Fs))
    assert M.status() == m3d.Error.NoError, M.status()
    return M


def add_dots(M, xy, zfun, size, width, h, sink, segs):
    '''
    Union raised dots onto the tile, trimmed to the tile footprint. Each dot
    top sits h above the highest terrain under it, its bottom sink below the
    lowest.

    Returns:
        m3d.Manifold
    '''
    ang  = np.linspace(0.0, 2.0 * np.pi, 16, endpoint=False)
    ring = np.c_[np.cos(ang), np.sin(ang)] * width / 2.0
    dots = []
    for c in xy:
        zs = zfun(np.r_[[c], c + ring])
        zb = zs.min() - sink
        zt = zs.max() + h
        dots.append(m3d.Manifold.cylinder(float(zt - zb), width / 2.0, width / 2.0, segs)
                    .translate((float(c[0]), float(c[1]), float(zb))))
    D    = m3d.Manifold.batch_boolean(dots, m3d.OpType.Add)
    box  = m3d.Manifold.cube((size, size, 1000.0)).translate((0.0, 0.0, -1.0))
    return M + (D ^ box)


def to_trimesh(M):
    mm = M.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config', nargs='?', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'))
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(args.config))
    par  = json.load(open(args.config))
    rel  = lambda p: os.path.normpath(os.path.join(here, os.path.expanduser(p)))
    out  = rel(par['out_dir'])
    os.makedirs(out, exist_ok=True)

    L      = par['tile_mm']
    xy     = load_stations(par['stations'], par['origin_utm'], par['m_per_mm'], par['merge_mm'])
    (x0, y0), k = densest_window(xy, L, par['edge_margin_mm'], par['search_step_mm'], 190.0)
    inwin  = (xy[:, 0] > x0) & (xy[:, 0] < x0 + L) & (xy[:, 1] > y0) & (xy[:, 1] < y0 + L)
    wxy    = xy[inwin] - (x0, y0)
    nn     = cKDTree(wxy).query(wxy, k=2)[0][:, 1]
    print(f'window: x {x0:.1f}-{x0 + L:.1f}, y {y0:.1f}-{y0 + L:.1f} mm of the model '
          f'(E {par["origin_utm"][0] + x0 * par["m_per_mm"]:.0f}, N {par["origin_utm"][1] + y0 * par["m_per_mm"]:.0f}); '
          f'{inwin.sum()} dots, nearest-neighbour spacing min {nn.min():.2f}, median {np.median(nn):.2f} mm')

    V, F       = load_stl(rel(par['mesh']))
    gx, gy, Z  = bare_terrain(V, F, x0, y0, L, par['cell_mm'])
    zmin, zmax = Z.min(), Z.max()
    Z          = (Z - zmin) * par['ve_to'] / par['ve_from'] + par['base_mm']
    gx, gy     = gx - x0, gy - y0
    print(f'terrain in model z {zmin:.2f}-{zmax:.2f} mm; tile z {Z.min():.2f}-{Z.max():.2f} mm '
          f'(exaggeration {par["ve_from"]:g}x -> {par["ve_to"]:g}x, lowest ground at {par["base_mm"]:g} mm)')

    zfun  = lambda p: bilinear(gx, gy, Z, p)
    base  = heightfield_solid(gx, gy, Z)
    ncol  = par['cols']
    nrow  = int(np.ceil(len(par['widths_mm']) / ncol))
    pitch = L + par['gap_mm']
    cx0   = par['bed_center_mm'][0] - (ncol * pitch - par['gap_mm']) / 2.0
    cy0   = par['bed_center_mm'][1] + (nrow * pitch - par['gap_mm']) / 2.0 - L
    scene = trimesh.Scene()
    rows  = []
    for i, w in enumerate(par['widths_mm']):
        tag  = f'{par["name"]}_{w:.1f}mm'
        raw  = os.path.join(out, tag + '_nolabel.stl')
        stl  = os.path.join(out, tag + '.stl')
        T    = add_dots(base, wxy, zfun, L, w, par['dot_h_mm'], par['dot_sink_mm'], par['dot_segs'])
        to_trimesh(T).export(raw)
        subprocess.run([sys.executable, rel(par['wall_text']), raw, stl, '--text', f'{w:.1f}',
                        '--side', par['label_side'], '--cap', str(par['label_cap_mm']),
                        '--depth', str(par['label_depth_mm']), '--zc', str(par['label_zc_mm'])],
                       check=True, stdout=subprocess.DEVNULL)
        os.remove(raw)
        tm   = trimesh.load(stl, process=True)
        assert tm.is_watertight, tag
        touch = (nn < w).mean()
        rows.append((w, touch, len(tm.faces), tm.volume))
        print(f'  {w:.1f} mm: {100 * touch:3.0f}% of dots touch a neighbour, {len(tm.faces)} tris, '
              f'{tm.volume / 1000:.2f} cm3, watertight {tm.is_watertight}')
        r, c = divmod(i, ncol)
        tm.apply_translation((cx0 + c * pitch, cy0 - r * pitch, 0.0))
        scene.add_geometry(tm, node_name=tag, geom_name=tag)
    p3 = os.path.join(out, par['name'] + '.3mf')
    scene.export(p3)
    print(f'plate: {len(rows)} tiles, {ncol} x {nrow}, {p3}')


def bilinear(gx, gy, Z, p):
    '''
    Bilinear interpolation of the heightfield at points p (n, 2), clamped to the grid.
    '''
    fx = np.clip((p[:, 0] - gx[0]) / (gx[1] - gx[0]), 0, len(gx) - 1.000001)
    fy = np.clip((p[:, 1] - gy[0]) / (gy[1] - gy[0]), 0, len(gy) - 1.000001)
    ix, iy = fx.astype(int), fy.astype(int)
    tx, ty = fx - ix, fy - iy
    return ((1 - tx) * (1 - ty) * Z[iy, ix] + tx * (1 - ty) * Z[iy, ix + 1] +
            (1 - tx) * ty * Z[iy + 1, ix] + tx * ty * Z[iy + 1, ix + 1])


if __name__ == '__main__':
    main()
