## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Arch fins and struts under the Epitrochoid keel ("struts" in "epi_keel" of
config/project.json).

The 45 deg V keel under the C-section track is only about 4 mm deep, and its
ridge falls along the track at about 1 in 12, so a ridge left on its own grows
a few mm out into the air each layer (the v4 print hung loops of it, Aaron
2026-11-25). Here a thin fin is hung under the ridge of every run of track and
its bottom edge is made a chain of 45 deg arches between struts, so every layer
of fin, ridge and V grows out of the one below by no more than a layer height.

Each strut stands on the back of the outer (tall, curled) wall of a lower turn,
outside the C so the marble channel stays clear (Aaron 2026-11-25), or on the
bed. It leans no more than lean_deg, its last few mm are vertical, and its
bottom follows the top of the wall under it, so it joins only the wall.

Runs: the V keel splits into one band per run of track (post to post). Along each
the ridge is the lowest V keel bottom across the band (not the lowest underside:
on banked and curving track the two are mm apart, and a fin off the V bottom
leaves the V beside it with nothing to climb from), binned by distance along the
band from its top end, smoothed, with tangent t and w = z x t, which points to
the inner wall (the C opening).
'''
import numpy as np
from manifold3d import Manifold, OpType
from scipy.ndimage import uniform_filter1d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

SEG = 24


def find_runs(xs, ys, D, Z, q, min_depth, min_nodes):
    '''
    Ridge lines of the keel band, one per run of track.

    Args:
        xs, ys    (ndarray): grid axes
        D, Z      (ndarray): (nx, ny, k) undersides and V keel bottoms
        q         (ndarray): squares from epi_keel.squares
        min_depth (float):   [mm] keel shallower than this is not band
        min_nodes (int):     smallest band component taken as a run

    Returns:
        list: per run a dict of s (arc length), xy, D (C bottom), Zv (V bottom), t, w, nodes
    '''
    nx, ny, km = D.shape
    n      = D.size
    h      = xs[1] - xs[0]
    with np.errstate(invalid='ignore'):
        band = (np.isfinite(D) & (D - Z > min_depth)).ravel()
    qq     = q[band[q].all(1)]
    a, b, c, d = qq.T
    e      = np.vstack([np.c_[a, b], np.c_[b, c], np.c_[c, d], np.c_[d, a], np.c_[a, c], np.c_[b, d]])
    ln     = np.r_[np.full(4 * len(qq), h), np.full(2 * len(qq), h * np.sqrt(2))]
    g      = coo_matrix((ln, (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    g      = g.maximum(g.T)
    nc, lab = connected_components(g, directed=False)
    cnt    = np.bincount(lab[np.unique(qq.ravel())], minlength=nc)
    cell   = np.arange(n) // km
    gx, gy = xs[cell // ny], ys[cell % ny]
    Df, Zf = D.ravel(), Z.ravel()
    runs   = []
    for ci in np.nonzero(cnt >= min_nodes)[0]:
        nodes = np.nonzero((lab == ci) & band)[0]
        top   = nodes[np.argmax(Df[nodes])]
        bi    = np.round(dijkstra(g, indices=top)[nodes]).astype(int)
        r     = []
        for k in range(bi.max() + 1):
            m = nodes[bi == k]
            if len(m) >= 3:
                j = m[np.argmin(Zf[m])]
                r.append((gx[j], gy[j], Df[j], Zf[j]))
        r = np.array(r)
        for col in range(4):
            r[:, col] = uniform_filter1d(r[:, col], 7, mode='nearest')
        t = np.gradient(r[:, :2], axis=0)
        t /= np.linalg.norm(t, axis=1)[:, None]
        w = np.c_[-t[:, 1], t[:, 0]]
        s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(r[:, :2], axis=0), axis=1))]
        ## bottom of the C (its centre is c_ro above): lowest underside across the band, square to the ridge
        p   = np.c_[gx[nodes], gy[nodes]]
        kd  = cKDTree(p)
        cb  = np.zeros((len(r), 3))
        for i in range(len(r)):
            m  = np.array(kd.query_ball_point(r[i, :2], 14.0))
            dv = p[m] - r[i, :2]
            m  = m[np.abs(dv @ t[i]) < 0.6]
            j  = nodes[m[np.argmin(Df[nodes[m]])]]
            cb[i] = gx[j], gy[j], Df[j]
        for col in range(3):
            cb[:, col] = uniform_filter1d(cb[:, col], 7, mode='nearest')
        runs.append({'s': s, 'xy': r[:, :2], 'D': r[:, 2], 'Zv': r[:, 3], 't': t, 'w': w,
                     'cxy': cb[:, :2], 'cD': cb[:, 2], 'nodes': nodes})
    runs.sort(key=lambda r: -r['D'][0])
    return runs


def fin_nodes(xs, ys, D, runs, half):
    '''
    Band nodes within half mm (plan) of their run's ridge line: the fin.
    '''
    nx, ny, km = D.shape
    fin  = np.zeros(D.size, bool)
    cell = np.arange(D.size) // km
    for r in runs:
        ## ridge densified to 0.25 mm
        u    = np.arange(0, r['s'][-1], 0.25)
        p    = np.c_[np.interp(u, r['s'], r['xy'][:, 0]), np.interp(u, r['s'], r['xy'][:, 1])]
        nd   = r['nodes']
        dd, _ = cKDTree(p).query(np.c_[xs[cell[nd] // ny], ys[cell[nd] % ny]])
        fin[nd[dd <= half]] = True
    return fin.reshape(D.shape)


class Lander:
    '''
    Strut landings: the back of every run's outer wall at land_deg round the C
    (0 = the inner wall side, 90 = top), or the bed, reached by a strut that
    leans no more than lean_deg and keeps clear of every C and the post.
    '''

    def __init__(self, runs, c, post_ro, xs, ys, U):
        self.runs = runs
        self.c    = c
        self.xs, self.ys, self.U = xs, ys, U
        self.ro   = c['c_ro']
        self.rs   = c['strut_d'] / 2
        self.post = post_ro
        th        = np.radians(c['land_deg'])
        ## centerlines and landing points, with their run numbers and indices
        self.cl   = np.vstack([np.c_[r['cxy'], r['cD'] + self.ro, np.full(len(r['s']), n)] for n, r in enumerate(runs)])
        self.kd   = cKDTree(self.cl[:, :3])
        self.lp   = np.vstack([np.c_[r['cxy'] + self.ro * np.cos(th) * r['w'], r['cD'] + self.ro + self.ro * np.sin(th),
                                     np.full(len(r['s']), n)] for n, r in enumerate(runs)])

    def clear(self, X, run_land, bot):
        '''
        True when the points X keep clear of every C (except the landing run near
        bot, where the strut joins it) and of the post.
        '''
        dd, ii = self.kd.query(X, k=8)
        near   = np.linalg.norm(X - bot, axis=1) < self.c['vert'] + self.rs
        for j in range(8):
            bad = dd[:, j] < self.ro + self.rs + self.c['gap']
            bad &= ~((self.cl[ii[:, j], 3] == run_land) & near)
            if bad.any():
                return False
        return not (np.hypot(X[:, 0], X[:, 1]) < self.post + self.rs + self.c['gap']).any()

    def seated(self, bot):
        '''
        True when every grid cell under the strut end has a solid top within
        vert mm of bot (the wall is really there, not only on the smoothed ridge).
        '''
        h      = self.xs[1] - self.xs[0]
        gx, gy = np.meshgrid(np.arange(-self.rs, self.rs + h, h), np.arange(-self.rs, self.rs + h, h), indexing='ij')
        k      = np.hypot(gx, gy) <= self.rs
        i      = np.clip(np.round((bot[0] + gx[k] - self.xs[0]) / h).astype(int), 0, len(self.xs) - 1)
        j      = np.clip(np.round((bot[1] + gy[k] - self.ys[0]) / h).astype(int), 0, len(self.ys) - 1)
        u      = np.where(np.isfinite(self.U[i, j]), self.U[i, j], 1e9)
        return bool((np.abs(u - bot[2]).min(axis=1) < self.c['vert'] - 1.0).all())

    def path(self, top, bot, run_land):
        '''
        Strut axis: lean from top to vert mm over bot, then straight down. None if blocked.
        '''
        ## a short strut (low track over the bed) keeps half its height for the vertical end
        knee = bot + np.r_[0.0, 0.0, min(self.c['vert'], (top[2] - bot[2]) / 2)]
        dz   = top[2] - knee[2]
        if dz <= 0 or np.hypot(*(top[:2] - knee[:2])) > np.tan(np.radians(self.c['lean_deg'])) * dz:
            return None
        n    = max(int(np.linalg.norm(top - knee) / 0.5), 2)
        X    = np.vstack([top + np.linspace(0, 1, n)[:, None] * (knee - top),
                          knee + np.linspace(0, 1, 9)[:, None] * (bot - knee)])
        return [top, knee, bot] if self.clear(X, run_land, bot) else None

    def land(self, top, run_top):
        '''
        Shortest clear strut from top: onto a lower run's outer wall, else the bed.

        Returns:
            dict or None: kind ('wall' or 'bed'), run, i (landing index), axis points, length
        '''
        lp   = self.lp
        dz   = top[2] - lp[:, 2]
        hz   = np.hypot(lp[:, 0] - top[0], lp[:, 1] - top[1])
        k    = np.nonzero((dz > self.c['vert'] + 1.0) & (hz <= np.tan(np.radians(self.c['lean_deg'])) * dz)
                          & (lp[:, 3] != run_top))[0]
        k    = k[np.argsort(np.hypot(hz[k], dz[k]))][:self.c['tries']]
        for j in k:
            run = int(lp[j, 3])
            if not self.seated(lp[j, :3]):
                continue
            ax  = self.path(top, lp[j, :3], run)
            if ax:
                i = int(j - sum(len(r['s']) for r in self.runs[:run]))
                return {'kind': 'wall', 'run': run, 'i': i, 'axis': ax, 'len': float(np.linalg.norm(top - lp[j, :3]))}
        bed = np.r_[top[:2], 0.0]
        ax  = self.path(top, bed, -1)
        if ax:
            return {'kind': 'bed', 'run': -1, 'i': -1, 'axis': ax, 'len': float(top[2])}
        return None


def plan(runs, lander, ridge_b, ridge_floor, c):
    '''
    Struts along every run so that the arches from them and from what already
    holds the keel up (ridge_b, the flood without struts) cover the whole ridge.

    Args:
        runs        (list):    from find_runs
        lander      (Lander):  landing search
        ridge_b     (list):    per run, keel bottom on the ridge from the flood without struts
        ridge_floor (list):    per run, lowest a fin may reach on the ridge (clearance, bed)
        c           (dict):    the struts config

    Returns:
        list: struts, each a dict of run, s, top (xyz) and the landing
    '''
    lh     = c['span'] / 2
    struts = []
    for n, r in enumerate(runs):
        s, zv = r['s'], r['Zv']
        cov   = ridge_b[n] < zv + c['tol']
        rr    = np.hypot(r['xy'][:, 0], r['xy'][:, 1])
        cov  |= rr < c['post_zone']
        i     = 0
        while True:
            un = np.nonzero(~cov[i:])[0]
            if not len(un):
                break
            i  = i + un[0]
            su = s[i]
            done = False
            ## from half a span ahead back to the gap itself
            for sp in np.arange(min(su + lh, s[-1]), su - lh / 2, -1.0):
                p  = np.argmin(np.abs(s - sp))
                if rr[p] < c['post_zone']:
                    continue
                win = np.abs(s - s[p]) <= lh
                zt  = np.min(zv[win] - np.abs(s[win] - s[p])) - c['tol']
                zt  = max(zt, ridge_floor[n][p])
                if zt + abs(su - s[p]) > zv[i] + c['tol']:
                    continue
                top = np.r_[r['xy'][p], zt]
                ## a fin this low simply stands on the bed
                ld  = {'kind': 'fin', 'run': -1, 'i': -1, 'axis': [top, top, np.r_[top[:2], 0.0]], 'len': 0.0} if zt <= c['bed_fin'] else lander.land(top, n)
                if ld and ld['kind'] == 'fin':
                    zt = top[2] = 0.0
                if ld:
                    struts.append({'run': n, 's': float(s[p]), 'p': int(p), 'top': top, 'ridge_d': float(r['D'][p]), 'land': ld})
                    cov |= zt + np.abs(s - s[p]) <= zv + c['tol']
                    done = True
                    break
            if not done:
                cov[i] = True
    return struts


def anchor_nodes(xs, ys, D, fin, struts, rs):
    '''
    Fin nodes over each strut top (within rs of it, plan), with the strut top height.
    '''
    nx, ny, km = D.shape
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    out    = []
    for st in struts:
        x, y, z = st['top']
        m = fin & ((np.hypot(gx - x, gy - y) <= rs)[:, :, None]) & (np.abs(D - st['ridge_d']) < 3.0)
        out.append((np.nonzero(m.ravel())[0], z))
    return out


def strut_mesh(st, c, xs, ys, U, end=True):
    '''
    One strut: a round rod along its axis, its top embed mm up into the fin, and
    either a flared foot on the bed or, on a wall, a vertical end whose bottom
    follows the top of the wall under it (U, the solid tops over the plan grid),
    sink mm into it, so nothing of it reaches inside the C. Struts that share a
    landing meet at its knee; end=False leaves the shared end to the first one.
    '''
    rs   = c['strut_d'] / 2
    top, knee, bot = [np.asarray(p, float) for p in st['land']['axis']]
    top  = top + np.r_[0.0, 0.0, c['embed']]

    def rod(a, b, ra, rb):
        sa = Manifold.cylinder(1e-3, ra, ra, SEG).translate(tuple(a))
        sb = Manifold.cylinder(1e-3, rb, rb, SEG).translate(tuple(b))
        return Manifold.batch_hull([sa, sb])

    if st['land']['kind'] == 'fin':
        return None
    parts = [rod(knee, top, rs, rs)]
    if st['land']['kind'] == 'bed':
        fz = c['foot_d'] / 2 - rs
        parts += [rod(np.r_[bot[:2], fz], knee, rs, rs), rod(np.r_[bot[:2], 0.0], np.r_[bot[:2], fz], c['foot_d'] / 2, rs)]
        return Manifold.batch_boolean(parts, OpType.Add)
    if not end:
        return parts[0]
    z0   = bot[2] - 3.0
    h    = xs[1] - xs[0]

    ## the end, z0 to the knee, is stretched per point so its bottom sits sink under the wall top
    def warp(v):
        v = v.copy()
        i = np.clip(np.round((v[:, 0] - xs[0]) / h).astype(int), 0, len(xs) - 1)
        j = np.clip(np.round((v[:, 1] - ys[0]) / h).astype(int), 0, len(ys) - 1)
        u = U[i, j]
        u = u[np.arange(len(i)), np.argmin(np.abs(np.where(np.isfinite(u), u, 1e9) - bot[2]), axis=1)]
        zb = np.where(np.abs(u - bot[2]) < c['vert'], u, bot[2]) - c['sink']
        v[:, 2] = zb + (v[:, 2] - z0) * (knee[2] - zb) / (knee[2] - z0)
        return v

    end = (Manifold.cylinder(knee[2] - z0, rs, rs, SEG).translate((bot[0], bot[1], z0))
           .refine_to_length(0.4).warp_batch(warp))
    parts.append(end)
    return Manifold.batch_boolean(parts, OpType.Add)


def sleeves(m, runs, c, post_ro):
    '''
    Tapered sleeves around every freestanding column (bed tree, strut) taller than
    c['sleeve']['warn'] (Aaron 2026-11-25: three 4.8 mm bed trees 68+ mm tall were
    knocked over by the nozzle in the v4 print). The piece is cut every dz mm; an
    island is part of a column while it is small (under big mm2) and sits on exactly
    one small island. Each column of height H gets a cone from r_base = H / slender
    (clamped to r_min..r_max) at its foot to r_top at its top, following its centre,
    kept gap mm off every other big island at that height, off every C (c_ro + gap
    from the centerlines) and off the post, and growing by no more than grow mm per mm
    upward so its sides print without support.

    Returns:
        tuple: list of sleeve Manifolds, list of (H, foot xyz, r_base used) per sleeve
    '''
    from shapely.geometry import Point, Polygon
    from shapely.strtree import STRtree
    s    = c['sleeve']
    ro   = c['c_ro']
    cl   = np.vstack([np.c_[r['cxy'], r['cD'] + ro] for r in runs])
    kd   = cKDTree(cl)
    zmax = m.bounding_box()[5]
    zs   = np.arange(s['dz'] / 2, zmax, s['dz'])

    def islands(z):
        out = []
        for part in m.slice(z).decompose():
            rings = [np.asarray(p) for p in part.to_polygons()]
            area  = [Polygon(r).area for r in rings]
            k     = int(np.argmax(area))
            out.append(Polygon(rings[k], [r for i, r in enumerate(rings) if i != k]).buffer(0))
        return out

    cols, live, prev = [], {}, []
    for z in zs:
        cur  = islands(z)
        tree = STRtree(prev) if prev else None
        nxt  = {}
        pars = [[j for j in (tree.query(p) if tree else []) if prev[j].intersects(p)] for p in cur]
        kids = {}
        for i, par in enumerate(pars):
            for j in par:
                kids[j] = kids.get(j, 0) + 1
        for i, p in enumerate(cur):
            par = pars[i]
            if p.area >= s['big']:
                continue
            if not par:
                if z > s['dz']:
                    continue
                col = {'bed': True, 'pts': []}
                cols.append(col)
            elif len(par) == 1 and kids[par[0]] == 1 and par[0] in live:
                col = live[par[0]]
            else:
                ## a new column where one stands on a big island, merges or splits
                col = {'bed': False, 'pts': []}
                cols.append(col)
            col['pts'].append((z, p))
            nxt[i] = col
        ## big islands at this height, for the clearance
        for col in nxt.values():
            col.setdefault('big', {})[z] = [q for q in cur if q.area >= s['big']]
        live, prev = nxt, cur

    parts, info = [], []
    for col in cols:
        pts = col['pts']
        H   = pts[-1][0] - pts[0][0]
        if H < s['warn']:
            continue
        rb  = float(np.clip(H / s['slender'], s['r_min'], s['r_max']))
        rr, xyz = [], []
        for k, (z, p) in enumerate(pts):
            ctr = np.array(p.centroid.coords[0])
            r   = rb + (s['r_top'] - rb) * (z - pts[0][0]) / H
            big = col['big'].get(z, [])
            if big:
                r = min(r, min(q.distance(Point(*ctr)) for q in big) - s['gap'])
            X   = np.r_[ctr, z]
            d, _ = kd.query(X)
            r   = min(r, d - ro - s['gap'], np.hypot(*ctr) - post_ro - s['gap'])
            if rr:
                r = min(r, rr[-1] + s['grow'] * s['dz'])
            elif not col['bed']:
                ## starts no wider than the column itself, so it never overhangs what is under it
                r = min(r, np.sqrt(p.area / np.pi))
            rr.append(max(r, 0.0)); xyz.append(X)
        rr = np.array(rr)
        ## a sleeve only where it is wider than the column itself
        keep = rr > s['r_top'] * 0.5
        if keep.sum() < 2:
            continue
        if col['bed']:
            xyz[0] = np.r_[xyz[0][:2], 0.0]
        disks = [Manifold.cylinder(1e-3, r, r, SEG).translate(tuple(X)) for X, r in zip(xyz, rr)]
        parts += [Manifold.batch_hull([disks[i], disks[i + 1]]) for i in range(len(disks) - 1) if keep[i] and keep[i + 1]]
        info.append((H, xyz[0], rr[0], col['bed']))
    return parts, info
