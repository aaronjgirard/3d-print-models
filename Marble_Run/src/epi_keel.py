## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
45 deg keel under the whole Epitrochoid track, plus the designed-in trees that are
kept ("epi_keel" in config/project.json).

Rays cast up through a plan grid give every layer of track over each cell (its
underside and top). For each underside the keel bottom is the deepest point from
which a 45 deg ray, in every one of a fan of directions, still meets the same
layer of track (followed cell to cell, so a turn passing over another is tracked
on its own). That is the clicky keel in 2D: a V under each track, as deep as half
its width. A keel never comes closer than clear mm to the layer below it (marble
room over a channel floor, a hood, a lower turn); where it would, that cell keeps
its old underside. Trees from the bed taller than keep_top and every tree that
does not reach the bed are dropped unless keep_struts.

Usage:
    python src/epi_keel.py [--out STL]      # writes the keeled piece without the epi_top changes
'''
import argparse
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, OpType

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_cfg, root


def layers(t, h, pad=1.0, kmax=8):
    '''
    Undersides and tops of every solid layer over a plan grid.

    Args:
        t    (trimesh.Trimesh): piece
        h    (float): [mm] grid spacing
        pad  (float): [mm] margin around the piece
        kmax (int):   most layers kept per cell

    Returns:
        tuple: xs, ys (grid axes), D, U ((nx, ny, kmax) undersides and tops, inf where none)
    '''
    lo, hi = t.bounds[0][:2] - pad, t.bounds[1][:2] + pad
    xs, ys = np.arange(lo[0], hi[0], h), np.arange(lo[1], hi[1], h)
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    o      = np.c_[gx.ravel(), gy.ravel(), np.full(gx.size, t.bounds[0][2] - 1.0)]
    loc, ir, it = t.ray.intersects_location(o, np.tile((0.0, 0.0, 1.0), (len(o), 1)), multiple_hits=True)
    nz     = t.face_normals[it, 2]
    k      = np.abs(nz) > 1e-6
    loc, ir, nz = loc[k], ir[k], nz[k]
    srt    = np.lexsort((loc[:, 2], ir))
    loc, ir, nz = loc[srt], ir[srt], nz[srt]
    D = np.full((gx.size, kmax), np.inf)
    U = np.full((gx.size, kmax), np.inf)
    st = np.searchsorted(ir, np.arange(gx.size + 1))
    for c in range(gx.size):
        a, b = st[c], st[c + 1]
        if a == b:
            continue
        inside, n, z0 = False, 0, 0.0
        for z, s in zip(loc[a:b, 2], nz[a:b]):
            if s < 0 and not inside:
                inside, z0 = True, z
            elif s > 0 and inside:
                inside = False
                if n < kmax and z - z0 > 1e-3:
                    D[c, n], U[c, n] = z0, z
                    n += 1
    return xs, ys, D.reshape(len(xs), len(ys), kmax), U.reshape(len(xs), len(ys), kmax)


def keel_bottom(D, h, reach, ndir, jump):
    '''
    Keel bottom under every underside: max over directions of the min over the
    same layer along that direction of (underside - distance).

    Args:
        D     (ndarray): (nx, ny, k) undersides, inf where none
        h     (float):   [mm] grid spacing
        reach (float):   [mm] how far each ray is followed
        ndir  (int):     number of directions
        jump  (float):   [mm] largest step in underside height between neighbouring cells of one layer

    Returns:
        ndarray: keel bottom per (cell, layer), inf where no underside
    '''
    nx, ny, km = D.shape
    Df   = D.reshape(-1, km)
    nc, nk = np.nonzero(np.isfinite(Df))
    nd   = Df[nc, nk]
    ix, iy = nc // ny, nc % ny
    best = np.full(len(nd), -np.inf)
    ar   = np.arange(len(nd))
    for th in np.linspace(0, 2 * np.pi, ndir, endpoint=False):
        m, cur, alive = np.full(len(nd), np.inf), nd.copy(), np.ones(len(nd), bool)
        for s in range(1, int(round(reach / h)) + 1):
            jx = ix + int(round(s * np.cos(th)))
            jy = iy + int(round(s * np.sin(th)))
            inb   = (jx >= 0) & (jx < nx) & (jy >= 0) & (jy < ny)
            alive &= inb
            cand  = Df[np.where(inb, jx * ny + jy, 0)]
            j     = np.argmin(np.abs(cand - cur[:, None]), axis=1)
            nb    = cand[ar, j]
            alive &= np.abs(nb - cur) < jump
            if not alive.any():
                break
            m   = np.where(alive, np.minimum(m, nb - s * h), m)
            cur = np.where(alive, nb, cur)
        best = np.maximum(best, m)
    zk = np.full(Df.shape, np.inf)
    zk[nc, nk] = np.minimum(best, nd)
    return zk.reshape(D.shape)


def keel_mesh(xs, ys, D, Z, embed, jump, min_depth):
    '''
    Closed solid between each underside (raised by embed) and its keel bottom: one
    quad per grid square whose four corners lie on one layer, side walls round the edge.

    Args:
        xs, ys (ndarray): grid axes
        D      (ndarray): (nx, ny, k) undersides, inf where none
        Z      (ndarray): keel bottoms, same shape
        embed  (float):   [mm] how far the top runs into the track
        jump   (float):   [mm] largest step between corners of one quad
        min_depth (float): [mm] squares with no corner deeper than this are left out

    Returns:
        Manifold: the keel
    '''
    nx, ny, km = D.shape
    Df  = D.reshape(-1, km)
    ## corner 0 of each quad, every layer
    i0, j0, k0 = np.nonzero(np.isfinite(D[:-1, :-1]))
    d0  = D[i0, j0, k0]
    ids = [(i0 * ny + j0) * km + k0]
    ok  = np.ones(len(d0), bool)
    for di, dj in [(1, 0), (1, 1), (0, 1)]:
        cand = D[i0 + di, j0 + dj]
        k    = np.argmin(np.abs(cand - d0[:, None]), axis=1)
        dd   = cand[np.arange(len(d0)), k]
        ok  &= np.abs(dd - d0) < jump
        ids.append(((i0 + di) * ny + j0 + dj) * km + k)
    q = np.stack(ids, axis=1)[ok]
    ## each corner node must also agree with its neighbours in the quad
    dq = Df.ravel()[q]
    zq = Z.reshape(-1, km).ravel()[q]
    q  = q[(np.ptp(dq, axis=1) < jump) & ((dq - zq).max(axis=1) > min_depth)]
    ## squares built twice from two close layers share a directed edge, and a corner where
    ## two squares touch only at that point gives a side-wall edge four faces: drop the
    ## squares involved until neither is left
    big = Df.size + 1
    while True:
        e   = np.vstack([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 3]], q[:, [3, 0]]])
        key = e[:, 0] * big + e[:, 1]
        u, cnt = np.unique(key, return_counts=True)
        dup = np.isin(key, u[cnt > 1]).reshape(4, -1).any(axis=0)
        rev = e[:, 1] * big + e[:, 0]
        bs  = e[~np.isin(key, rev), 0]
        u, cnt = np.unique(bs, return_counts=True)
        pin = np.isin(q, u[cnt > 1]).any(axis=1)
        if not (dup.any() or pin.any()):
            break
        q = q[~(dup | pin)]
    used, inv = np.unique(q.ravel(), return_inverse=True)
    q   = inv.reshape(q.shape)
    cell, lay = used // km, used % km
    gx, gy = xs[cell // ny], ys[cell % ny]
    top = np.c_[gx, gy, Df.ravel()[used] + embed]
    ## corners with no keel sit just under the underside, so no face lies on it
    bot = np.c_[gx, gy, np.minimum(Z.reshape(-1, km).ravel()[used], Df.ravel()[used] - 0.05)]
    n   = len(used)
    a, b, c, d = q.T
    f   = [np.c_[a, b, c], np.c_[a, c, d], np.c_[a, c, b] + n, np.c_[a, d, c] + n]
    ## boundary edges: directed quad edges whose reverse is not used
    e   = np.vstack([np.c_[a, b], np.c_[b, c], np.c_[c, d], np.c_[d, a]])
    key = e[:, 0].astype(np.int64) * n + e[:, 1]
    rev = e[:, 1].astype(np.int64) * n + e[:, 0]
    bd  = e[~np.isin(key, rev)]
    p0, p1 = bd[:, 0], bd[:, 1]
    f  += [np.c_[p0, p0 + n, p1 + n], np.c_[p0, p1 + n, p1]]
    v   = np.vstack([top, bot])
    return Manifold(Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(np.vstack(f), np.uint32)))


def kept_supports(path, keep_top, keep_struts):
    '''
    Tree bodies kept: those standing on the bed no taller than keep_top, and the
    ones that do not reach the bed when keep_struts.
    '''
    s    = trimesh.load(path)
    keep = []
    for p in s.split(only_watertight=False):
        lo, hi = p.bounds[0][2], p.bounds[1][2]
        if (lo < 0.5 and hi <= keep_top) or (lo >= 0.5 and keep_struts):
            keep.append(p)
    return keep


def to_manifold(t):
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def build(cfg):
    '''
    Base track + keel + kept trees.

    Returns:
        tuple: Manifold of the piece, dict of numbers for the report
    '''
    k    = cfg['epi_keel']
    base = trimesh.load(os.path.join(root, k['base']))
    xs, ys, D, U = layers(base, k['grid'])
    ## nothing in or on the post
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    D[np.hypot(gx, gy) < k['post_r']] = np.inf
    Z = keel_bottom(D, k['grid'], k['reach'], k['ndir'], k['jump'])
    ## clearance from the layer below (the bed for the lowest layer)
    below = np.concatenate([np.zeros(D.shape[:2] + (1,)), U[:, :, :-1] + k['clear']], axis=2)
    below[:, :, 0] = 0.0
    Z[:, :, 0] = np.maximum(Z[:, :, 0], 0.0)
    Z  = np.where(Z < below, D, Z)
    Z  = np.where(Z < k['bed_snap'], 0.0, Z)
    Z  = np.minimum(Z, D)
    keel = keel_mesh(xs, ys, D, Z, k['embed'], k['jump'], k['min_depth'])
    sup  = kept_supports(os.path.join(root, k['supports']), k['keep_top'], k['keep_struts'])
    m    = Manifold.batch_boolean([to_manifold(base), keel] + [to_manifold(p) for p in sup], OpType.Add)
    fin  = np.isfinite(D)
    info = {'keel_cm3': keel.volume() / 1000, 'deepest': float((D[fin] - Z[fin]).max()), 'trees': len(sup)}
    return m, info


def main():
    cfg = load_cfg()
    ap  = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(root, 'Epitrochoid_keel_only.stl'))
    a   = ap.parse_args()
    m, info = build(cfg)
    print(info)
    mesh = m.to_mesh()
    trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts)).export(a.out)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
