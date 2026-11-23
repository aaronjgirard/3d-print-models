#!/usr/bin/env python3
## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Terrain-relief STL with blind receiver holes -> same relief with RAISED receiver dots, optionally
re-scaling the vertical exaggeration. Works on the STL alone (no DEM needed).

  python3 -I stl_holes_to_dots.py IN.stl OUT.stl [--ve_from 3 --ve_to 2] [--dot_d 0.7 --dot_h 1.2]
          [--dots DOTS.csv] [--raise_mm 10.214]

--dots takes a CSV (station,x_mm,y_mm,...) of dot positions to use instead of the hole centres.
--raise_mm adds a constant to every height above the underside after rescaling (for example, to put
Z=0 at sea level). Dots are trimmed to the model outline, so a station on the edge never overhangs a wall.

Steps: (1) find each blind hole (vertical cylinder wall + flat floor) and delete it; (2) cap the opening
with a patch whose interior follows a quadratic surface fitted to the surrounding terrain; (3) scale all
heights above the lowest terrain point by ve_to/ve_from, so the thinnest point keeps its thickness and the
flat underside, outline and side walls are unchanged; (4) add a raised dot at every former hole centre,
as in build_kilauea_print.py: top = highest terrain under the dot + dot_h, bottom sunk 0.6 mm below the
lowest terrain under it. +X east, +Y north, Z up; Z=0 is the flat underside.
"""
import argparse, os, struct
import numpy as np, trimesh
import manifold3d as m3d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--ve_from", type=float, default=3.0); ap.add_argument("--ve_to", type=float, default=3.0)
ap.add_argument("--dot_d", type=float, default=0.7); ap.add_argument("--dot_h", type=float, default=1.2)
ap.add_argument("--sink", type=float, default=0.6)
ap.add_argument("--dots", type=str, default="", help="CSV station,x_mm,y_mm: dot positions instead of hole centres")
ap.add_argument("--raise_mm", type=float, default=0.0, help="added to all heights above the underside after rescaling")
a = ap.parse_args()

# ---- load, merging bit-identical float32 vertices as a slicer does
with open(a.inp, "rb") as f:
    f.read(80); n = struct.unpack("<I", f.read(4))[0]
    rec = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
u, inv = np.unique(rec["v"].reshape(-1, 3), axis=0, return_inverse=True)
V = u.astype(np.float64); F = inv.reshape(-1, 3)
F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
assert trimesh.Trimesh(V, F, process=False).is_watertight, "input is not watertight"
cr = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); nl = np.linalg.norm(cr, axis=1)
nz = np.where(nl > 0, cr[:, 2] / np.maximum(nl, 1e-300), 0.0)
print(f"input: {len(F)} tris, bbox {np.round(V.max(0) - V.min(0), 2)} mm")

# ---- holes = connected groups of vertical faces other than the outer side wall
# (|nz| < 0.02 is steeper than 88.9 deg; the terrain itself never gets that steep)
vert = np.where(np.abs(nz) < 0.02)[0]
fv = F[vert]
G = coo_matrix((np.ones(3 * len(fv)), (np.r_[fv[:, 0], fv[:, 1], fv[:, 2]], np.r_[fv[:, 1], fv[:, 2], fv[:, 0]])),
               shape=(len(V),) * 2)
_, lab = connected_components(G, directed=False)
flab = lab[fv[:, 0]]
comps, cnt = np.unique(flab, return_counts=True)
outer = comps[cnt.argmax()]
holes = []
for k in comps[comps != outer]:
    wf = vert[flab == k]
    wv = np.unique(F[wf])
    zf = V[wv, 2].min()
    ring = wv[V[wv, 2] == zf]
    c = V[ring, :2].mean(0); r = np.linalg.norm(V[ring, :2] - c, axis=1).mean()
    holes.append(dict(walls=wf, c=c, r=r, zf=zf))
print(f"holes found: {len(holes)}, diameter {2*min(h['r'] for h in holes):.2f}..{2*max(h['r'] for h in holes):.2f} mm")

# pocket faces: every vertex belongs to that hole's wall (the flat floor uses only the wall's bottom ring)
owner = np.full(len(V), -1)
for i, h in enumerate(holes):
    owner[np.unique(F[h["walls"]])] = i
fo = owner[F]
dead = (fo[:, 0] >= 0) & (fo[:, 0] == fo[:, 1]) & (fo[:, 1] == fo[:, 2])
for i, h in enumerate(holes):
    h["nfloor"] = int(((fo[:, 0] == i) & dead & (V[F[:, 0], 2] == h["zf"]) & (V[F[:, 1], 2] == h["zf"]) & (V[F[:, 2], 2] == h["zf"])).sum())
assert all(h["nfloor"] > 0 for h in holes)
F2 = F[~dead]

# ---- cap each opening: rim -> two interior rings -> centre, heights from a local quadratic fit
E = np.concatenate([F2[:, [0, 1]], F2[:, [1, 2]], F2[:, [2, 0]]])
key = np.minimum(E[:, 0], E[:, 1]).astype(np.int64) * len(V) + np.maximum(E[:, 0], E[:, 1])
uk, idx, kc = np.unique(key, return_index=True, return_counts=True)
bnd = E[idx[kc == 1]]                                   # directed as in the surviving faces
print(f"open edges after removing pockets: {len(bnd)}")
bmid = V[bnd].mean(1)[:, :2]
own = cKDTree(np.array([h["c"] for h in holes])).query(bmid)[1]
topv = np.unique(F2[nz[~dead] > 0.1])                  # vertices of upward faces
vtree = cKDTree(V[topv, :2])
newV = []; newF = []; nv = len(V)
ts = (2 / 3, 1 / 3, 0.0)
for i, h in enumerate(holes):
    e = bnd[own == i]
    rim = np.unique(e)
    near = topv[vtree.query_ball_point(h["c"], h["r"] + 1.0)]
    d = V[near, :2] - h["c"]
    A = np.c_[np.ones(len(d)), d, d[:, 0] ** 2, d[:, 0] * d[:, 1], d[:, 1] ** 2]
    coef = np.linalg.lstsq(A, V[near, 2], rcond=None)[0]
    zq = lambda p: coef[0] + coef[1] * p[:, 0] + coef[2] * p[:, 1] + coef[3] * p[:, 0] ** 2 + coef[4] * p[:, 0] * p[:, 1] + coef[5] * p[:, 1] ** 2
    h["fit_rms"] = np.sqrt(np.mean((A @ coef - V[near, 2]) ** 2))
    resid = V[rim, 2] - zq(V[rim, :2] - h["c"])             # blend toward the true rim so the cap meets it exactly
    ringid = {}
    for t in ts[:-1]:
        pts = h["c"] + t * (V[rim, :2] - h["c"])
        ids = nv + np.arange(len(rim)); nv += len(rim)
        newV.append(np.c_[pts, zq(pts - h["c"]) + t * resid])
        ringid[t] = dict(zip(rim, ids))
    cidx = nv; nv += 1
    newV.append(np.array([[h["c"][0], h["c"][1], zq(np.zeros((1, 2)))[0]]]))
    for p, q in e:                                       # surviving face runs p->q, so the cap runs q->p
        a1, b1 = ringid[ts[0]][p], ringid[ts[0]][q]
        a2, b2 = ringid[ts[1]][p], ringid[ts[1]][q]
        newF += [(q, p, a1), (q, a1, b1), (b1, a1, a2), (b1, a2, b2), (b2, a2, cidx)]
V = np.vstack([V] + newV); F = np.vstack([F2, np.array(newF)])
mesh = trimesh.Trimesh(V, F, process=False)
print(f"capped: watertight {mesh.is_watertight}, winding {mesh.is_winding_consistent}; "
      f"local quadratic fit rms median {np.median([h['fit_rms'] for h in holes]):.3f}, max {max(h['fit_rms'] for h in holes):.3f} mm")
assert mesh.is_watertight and mesh.is_winding_consistent

# ---- vertical exaggeration: scale heights above the lowest terrain point
cr = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); nl = np.linalg.norm(cr, axis=1)
up = np.where(nl > 0, cr[:, 2] / np.maximum(nl, 1e-300), 0.0) > 0.1     # terrain only (wall slivers can read ~0.04)
zref = V[np.unique(F[up]), 2].min()
k = a.ve_to / a.ve_from
ztop0 = V[:, 2].max()
hi = V[:, 2] > zref
V[hi, 2] = zref + (V[hi, 2] - zref) * k
print(f"vertical exaggeration {a.ve_from:g}x -> {a.ve_to:g}x (relief x{k:.4f} above z = {zref:.3f} mm): "
      f"tallest {ztop0:.2f} -> {V[:, 2].max():.2f} mm, thinnest stays {zref:.2f} mm")
if a.raise_mm:
    V[V[:, 2] > 0, 2] += a.raise_mm
    print(f"raised everything above the underside by {a.raise_mm:.3f} mm: thinnest {zref + a.raise_mm:.2f} mm, "
          f"tallest {V[:, 2].max():.2f} mm")

# ---- raised dots at the former hole centres (or at --dots positions)
tc = V[F[up]]; ttree = cKDTree(tc.mean(1)[:, :2])
def zat(p):
    js = ttree.query(p, k=64)[1]
    for j in js:
        A_, B_, C_ = tc[j]
        m = np.array([[B_[0] - A_[0], C_[0] - A_[0]], [B_[1] - A_[1], C_[1] - A_[1]]])
        l1, l2 = np.linalg.solve(m, p - A_[:2])
        if l1 >= -1e-9 and l2 >= -1e-9 and l1 + l2 <= 1 + 1e-9:
            return A_[2] + l1 * (B_[2] - A_[2]) + l2 * (C_[2] - A_[2])
    A_, B_, C_ = tc[js[0]]                               # just outside the outline: extend the nearest facet
    m = np.array([[B_[0] - A_[0], C_[0] - A_[0]], [B_[1] - A_[1], C_[1] - A_[1]]])
    l1, l2 = np.linalg.solve(m, p - A_[:2])
    return A_[2] + l1 * (B_[2] - A_[2]) + l2 * (C_[2] - A_[2])
if a.dots:
    rows = [l.strip().split(",") for l in open(a.dots) if l.strip() and not l.lower().startswith("station")]
    for h, r in zip(holes, rows):
        h["c"] = np.array([float(r[1]), float(r[2])])
    assert len(rows) == len(holes), f"{a.dots} has {len(rows)} positions for {len(holes)} holes"
    print(f"dot positions from {a.dots}")
# outline of the flat underside, to trim dots that sit on an edge
bf = F[(np.abs(V[F, 2]).max(1) == 0)]
be = np.concatenate([bf[:, [0, 1]], bf[:, [1, 2]], bf[:, [2, 0]]])
bk = np.minimum(be[:, 0], be[:, 1]).astype(np.int64) * len(V) + np.maximum(be[:, 0], be[:, 1])
_, bi, bc = np.unique(bk, return_index=True, return_counts=True)
nxt = {int(p): int(q) for p, q in be[bi[bc == 1]]}
loop = [next(iter(nxt))]
while nxt[loop[-1]] != loop[0]:
    loop.append(nxt[loop[-1]])
prism = m3d.Manifold.extrude(m3d.CrossSection([V[loop, :2]], m3d.FillRule.EvenOdd), V[:, 2].max() + 10).translate((0, 0, -1))
ang = np.linspace(0, 2 * np.pi, 8, endpoint=False)
dots = []; info = []
for h in holes:
    zs = [zat(h["c"])] + [zat(h["c"] + a.dot_d / 2 * np.array([np.cos(t), np.sin(t)])) for t in ang]
    zb, zt = min(zs) - a.sink, max(zs) + a.dot_h
    dots.append(m3d.Manifold.cylinder(float(zt - zb), a.dot_d / 2, a.dot_d / 2, 16)
                .translate((float(h["c"][0]), float(h["c"][1]), float(zb))))
    info.append((h["c"][0], h["c"][1], zs[0], max(zs) - min(zs)))
info = np.array(info)
M = m3d.Manifold(m3d.Mesh(vert_properties=V.astype(np.float32), tri_verts=F.astype(np.uint32)))
assert M.status() == m3d.Error.NoError, M.status()
vol0 = M.volume()
D = m3d.Manifold.batch_boolean(dots, m3d.OpType.Add)
Dt = D ^ prism
print(f"outline: {len(loop)} vertices; dot volume outside it trimmed: {D.volume() - Dt.volume():.4f} mm3")
M = M + Dt
mm = M.to_mesh()
res = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
v32 = np.asarray(res.vertices, np.float32); uu, ii = np.unique(v32, axis=0, return_inverse=True)
f = ii.reshape(-1)[np.asarray(res.faces).ravel()].reshape(-1, 3)
f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
res = trimesh.Trimesh(uu.astype(np.float64), f, process=False)
res.export(a.out)
dd = cKDTree(info[:, :2]).query(info[:, :2], k=2)[0][:, 1]
print(f"dots: {len(dots)} x {a.dot_d} mm wide, {a.dot_h} mm above the highest terrain under each "
      f"(terrain drop across a dot up to {info[:, 3].max():.2f} mm); nearest-neighbour spacing min {dd.min():.2f} mm")
print(f"added volume {M.volume() - vol0:.1f} mm3 | out tris {len(res.faces)}, watertight {res.is_watertight}, "
      f"bbox {np.round(res.extents, 2)} mm, {os.path.getsize(a.out) / 1e6:.1f} MB")
np.save(os.path.splitext(a.out)[0] + "_dots.npy", info)
