'''
Widen the raised receiver dots of a terrain-relief STL in place.

Finds every existing dot by its flat top cap, fits the cap's centre (known
radius --old_d / 2, so caps cut by a taller neighbour still fit), and unions a
wider dot on the same centre. The new dot follows the rule of the original
build: top --dot_h above the highest terrain under it (never below the old
top), bottom --sink below the lowest. Terrain heights come from the up-facing
terrain faces only (dot caps and wall-text recesses excluded). Dots are
trimmed to the model outline, so an edge dot never overhangs a wall.

Usage:
    python widen_dots.py IN.stl OUT.stl [--dot_d 0.9] [--old_d 0.7]
        [--dot_h 1.2] [--sink 0.6] [--segs 32]
'''
import argparse
import os
import struct

import manifold3d as m3d
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def load_stl(path):
    '''
    Binary STL to merged vertices and faces, as a slicer reads it.

    Returns:
        tuple: vertices (n, 3), faces (m, 3)
    '''
    with open(path, 'rb') as f:
        f.read(80)
        n   = struct.unpack('<I', f.read(4))[0]
        rec = np.frombuffer(f.read(n * 50), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    u, inv = np.unique(rec['v'].reshape(-1, 3), axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    return u.astype(np.float64), F


def face_nz(V, F):
    '''z component of each unit face normal (0 for degenerate faces).'''
    cr = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    nl = np.linalg.norm(cr, axis=1)
    return np.where(nl > 0, cr[:, 2] / np.maximum(nl, 1e-300), 0.0)


def face_groups(F, n):
    '''Connected components of faces that share an edge.'''
    E   = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    key = np.minimum(E[:, 0], E[:, 1]).astype(np.int64) * n + np.maximum(E[:, 0], E[:, 1])
    fid = np.tile(np.arange(len(F)), 3)
    o   = np.argsort(key)
    k, f = key[o], fid[o]
    same = k[1:] == k[:-1]
    G   = coo_matrix((np.ones(same.sum()), (f[:-1][same], f[1:][same])), shape=(len(F),) * 2)
    return connected_components(G, directed=False)[1]


def fit_centre(p, r, c0):
    '''
    Centre of a circle of known radius through 2D points, ignoring points off it.

    Returns:
        tuple: centre (2,), number of points used
    '''
    c = c0.copy()
    for tol in (0.15, 0.05, 0.01, 0.002):
        for _ in range(10):
            d   = p - c
            rr  = np.linalg.norm(d, axis=1)
            use = np.abs(rr - r) < tol
            if use.sum() < 3:
                return c, int(use.sum())
            J   = -d[use] / rr[use, None]
            c   = c - np.linalg.lstsq(J, rr[use] - r, rcond=None)[0]
    return c, int(use.sum())


def terrain_z(tc, tree, p, k=64):
    '''
    Highest terrain surface above each 2D point (nan where none, e.g. under an old dot).

    Args:
        tc   (array): terrain triangles (m, 3, 3)
        tree (cKDTree): on the triangle centroids (x, y)
        p    (array): query points (n, 2)

    Returns:
        array: z (n,)
    '''
    js   = tree.query(p, k=k)[1]
    A, B, C = tc[js, 0], tc[js, 1], tc[js, 2]
    q    = p[:, None, :] - A[..., :2]
    u, v = B[..., :2] - A[..., :2], C[..., :2] - A[..., :2]
    det  = u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0]
    ok   = np.abs(det) > 1e-14
    det  = np.where(ok, det, 1.0)
    l1   = (q[..., 0] * v[..., 1] - q[..., 1] * v[..., 0]) / det
    l2   = (u[..., 0] * q[..., 1] - u[..., 1] * q[..., 0]) / det
    ins  = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l1 + l2 <= 1 + 1e-9)
    z    = A[..., 2] + l1 * (B[..., 2] - A[..., 2]) + l2 * (C[..., 2] - A[..., 2])
    z    = np.where(ins, z, -np.inf).max(1)
    return np.where(np.isfinite(z), z, np.nan)


def outline_prism(V, F, height):
    '''Extruded outline of the flat underside (z = 0), for trimming dots.'''
    bf  = F[np.abs(V[F, 2]).max(1) == 0]
    be  = np.concatenate([bf[:, [0, 1]], bf[:, [1, 2]], bf[:, [2, 0]]])
    bk  = np.minimum(be[:, 0], be[:, 1]).astype(np.int64) * len(V) + np.maximum(be[:, 0], be[:, 1])
    _, bi, bc = np.unique(bk, return_index=True, return_counts=True)
    nxt = {int(p): int(q) for p, q in be[bi[bc == 1]]}
    loop = [next(iter(nxt))]
    while nxt[loop[-1]] != loop[0]:
        loop.append(nxt[loop[-1]])
    cs = m3d.CrossSection([V[loop, :2]], m3d.FillRule.EvenOdd)
    return m3d.Manifold.extrude(cs, height + 2).translate((0, 0, -1)), len(loop)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inp')
    ap.add_argument('out')
    ap.add_argument('--dot_d', type=float, default=0.9)     # [mm] new dot diameter
    ap.add_argument('--old_d', type=float, default=0.7)     # [mm] existing dot diameter
    ap.add_argument('--dot_h', type=float, default=1.2)     # [mm] dot top above the highest terrain under it
    ap.add_argument('--sink' , type=float, default=0.6)     # [mm] dot bottom below the lowest terrain under it
    ap.add_argument('--segs' , type=int  , default=32)      # sides of each dot
    a = ap.parse_args()

    V, F = load_stl(a.inp)
    nz   = face_nz(V, F)
    print(f'input: {len(F)} tris, bbox {np.round(V.max(0) - V.min(0), 2)} mm')

    ## dot caps: flat up faces whose every vertex drops down a vertical wall by more than 0.5 mm
    vert = np.abs(nz) < 0.02
    zlow = np.full(len(V), np.inf)
    for i in range(3):
        np.minimum.at(zlow, F[vert, i], V[F[vert], 2].min(1))
    drop = V[:, 2] - zlow > 0.5
    cap  = (nz > 0.999) & drop[F].all(1)
    cf   = F[cap]
    lab  = face_groups(cf, len(V))
    frag = [np.unique(cf[lab == g]) for g in range(lab.max() + 1)]
    nall = len(frag)
    frag = [f for f in frag if np.ptp(V[f, :2], axis=0).max() < a.old_d + 0.01]     # wall-text faces are bigger

    ## a taller neighbour can cut one cap into pieces: pool pieces at the same height within one dot width
    fz   = np.array([V[f[0], 2] for f in frag])
    fm   = np.array([V[f, :2].mean(0) for f in frag])
    pr   = cKDTree(fm).query_pairs(a.old_d, output_type='ndarray')
    pr   = pr[fz[pr[:, 0]] == fz[pr[:, 1]]]
    G    = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(frag),) * 2)
    dot  = connected_components(G, directed=False)[1]

    ## centre from the surviving rim points; a dot with too few keeps the centre of its exposed piece
    r0   = a.old_d / 2
    rin  = a.dot_d / 2 * np.cos(np.pi / a.segs)
    ctr  = []
    nfit = []
    for g in range(dot.max() + 1):
        p    = V[np.concatenate([frag[i] for i in np.where(dot == g)[0]]), :2]
        c, n = fit_centre(p, r0, p.mean(0))
        if n < 3 or np.linalg.norm(p - c, axis=1).max() > r0 + 0.005:
            c, n = p.mean(0), 0
        assert np.linalg.norm(p - c, axis=1).max() < rin, f'old dot at {c} is not inside the new one'
        ctr.append((c[0], c[1], fz[dot == g][0]))
        nfit.append(n)
    ctr  = np.array(ctr)
    nfit = np.array(nfit)
    print(f'old dot caps: {len(frag)} pieces ({nall - len(frag)} larger flat faces skipped) in {len(ctr)} dots; '
          f'{(nfit == 0).sum()} dots mostly covered by '
          f'taller neighbours keep the centre of their exposed piece; rim points per fitted dot: '
          f'min {nfit[nfit > 0].min()}, median {np.median(nfit[nfit > 0]):.0f}')

    ## terrain: up faces that are not caps; where two surfaces overlap (wall text) take the top one
    terr = (nz > 0.1) & ~cap
    tc   = V[F[terr]]
    tree = cKDTree(tc.mean(1)[:, :2])
    ang  = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    ring = np.r_[[[0.0, 0.0]], np.c_[np.cos(ang), np.sin(ang)] * a.dot_d / 2,
                 np.c_[np.cos(ang), np.sin(ang)] * a.dot_d / 4]
    P    = (ctr[:, None, :2] + ring[None]).reshape(-1, 2)
    Z    = terrain_z(tc, tree, P).reshape(len(ctr), -1)
    nhit = np.isfinite(Z).sum(1)
    assert nhit.min() > 0, 'a dot has no terrain around it'
    zt   = np.maximum(np.nanmax(Z, 1) + a.dot_h, ctr[:, 2])
    zb   = np.nanmin(Z, 1) - a.sink
    print(f'terrain samples per dot: min {nhit.min()} of {Z.shape[1]}; new tops raised to the old top '
          f'on {(np.nanmax(Z, 1) + a.dot_h < ctr[:, 2]).sum()} dots (up to '
          f'{max(0, (ctr[:, 2] - np.nanmax(Z, 1) - a.dot_h).max()):.3f} mm)')

    ## union the wider dots, trimmed to the outline
    M    = m3d.Manifold(m3d.Mesh(vert_properties=V.astype(np.float32), tri_verts=F.astype(np.uint32)))
    assert M.status() == m3d.Error.NoError, M.status()
    vol0 = M.volume()
    dots = [m3d.Manifold.cylinder(float(t - b), a.dot_d / 2, a.dot_d / 2, a.segs).translate((float(x), float(y), float(b)))
            for (x, y, _), t, b in zip(ctr, zt, zb)]
    D    = m3d.Manifold.batch_boolean(dots, m3d.OpType.Add)
    pr, nl = outline_prism(V, F, V[:, 2].max() + 10)
    Dt   = D ^ pr
    M    = M + Dt
    print(f'outline: {nl} vertices; dot volume outside it trimmed: {D.volume() - Dt.volume():.4f} mm3')

    ## write, merging float32 vertices so the STL is watertight as read
    mm   = M.to_mesh()
    res  = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
    v32  = np.asarray(res.vertices, np.float32)
    uu, ii = np.unique(v32, axis=0, return_inverse=True)
    f    = ii.reshape(-1)[np.asarray(res.faces).ravel()].reshape(-1, 3)
    f    = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    res  = trimesh.Trimesh(uu.astype(np.float64), f, process=False)
    res.export(a.out)
    dd   = cKDTree(ctr[:, :2]).query(ctr[:, :2], k=2)[0][:, 1]
    print(f'dots: {len(ctr)} x {a.dot_d} mm wide; nearest-neighbour spacing min {dd.min():.2f} mm, '
          f'{(dd < a.dot_d).mean() * 100:.0f}% touch a neighbour')
    print(f'added volume {M.volume() - vol0:.1f} mm3 | out tris {len(res.faces)}, watertight {res.is_watertight}, '
          f'bbox {np.round(res.extents, 2)} mm, {os.path.getsize(a.out) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
