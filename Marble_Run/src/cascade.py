## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Switchback cascade on the long span ("cascade" in config/project.json).

The marble leaves the raised post, runs down three ramps stacked in one plane,
dropping through a hole at each turn, and enters the low post. A back plate
stands on the bed and carries every ramp on a 45 deg shelf, so only the raised
post needs support. Both windows are open to the top: from their widest point
the sides run straight up through the shoulder and the plug, which is a C ring.

Usage:
    python src/cascade.py [--span 183.8] [--out stl/custom] [--prev preview] [--name cascade_l]
'''
import argparse
import os
import sys

import numpy as np
import trimesh
from scipy.optimize import brentq
from manifold3d import Manifold, CrossSection, FillRule

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rounds import slot_cutter
from parts import POST_OD, POST_ID, PLUG_OD, PLUG_ID, PLUG_LEN, PLUG_SLOT_R, SHOULDER, SOCKET, MARBLE, CH_R, CH_WALL, CH_H
from parts import Piece, cyl, box, union, export
from project import load_cfg, out_dirs

RO = CH_R + CH_WALL     # [mm] outer radius of the channel round


def arc(cy, cz, r, a0, a1, n=24):
    '''
    Points on a circle in the (y, z) plane from angle a0 to a1 [deg].
    '''
    a = np.radians(np.linspace(a0, a1, n))
    return np.c_[cy + r * np.cos(a), cz + r * np.sin(a)]


def profiles(yp):
    '''
    Ramp cross-sections in (y, z) with z = 0 at the channel floor.

    Args:
        yp (float): y of the back plate face

    Returns:
        tuple: outer (CrossSection), inner cut (CrossSection)
    '''
    ## 45 deg shelf tangent to the outer round, running down to the plate face
    t  = np.array([RO * np.sin(np.pi / 4), CH_R - RO * np.cos(np.pi / 4)])
    zp = t[1] - (t[0] - yp)
    out = np.vstack([[RO, CH_H], arc(0, CH_R, RO, 0, -45), [yp, zp], [yp, CH_H]])
    inn = np.vstack([arc(0, CH_R, CH_R, 0, -180, 48), [-CH_R, CH_H + 0.05], [CH_R, CH_H + 0.05]])
    cs  = lambda p: CrossSection([np.asarray(p, float)], FillRule.EvenOdd)
    return cs(out), cs(inn)


def ramp(cs, x0, x1, f0, k):
    '''
    Extrude a cross-section along +x from x0 to x1 with its floor falling at slope k.

    Args:
        cs (CrossSection): profile in (y, z)
        x0 (float): start
        x1 (float): end
        f0 (float): floor height at x = 0 of the line z = f0 - k x
        k  (float): fall per mm along +x (negative rises)

    Returns:
        Manifold: the sheared prism
    '''
    m = cs.extrude(x1 - x0)
    return m.warp_batch(lambda v: np.c_[x0 + v[:, 2], v[:, 0], f0 - k * (x0 + v[:, 2]) + v[:, 1]])


def window(x, d, sill, w, top, r0):
    '''
    Window open to the top: round bottom of width w at the sill, straight sides above.

    Args:
        x    (float): post axis x
        d    (int):   +1 faces +x, -1 faces -x
        sill (float): bottom of the window
        w    (float): width
        top  (float): height the slot runs to
        r0   (float): distance from the axis the cut starts at
    '''
    r1 = POST_OD / 2 + 1
    xa, xb = sorted((x + d * r0, x + d * r1))
    rnd = Manifold.cylinder(xb - xa, w / 2).rotate((0, 90, 0)).translate((xa, 0, sill + w / 2))
    return rnd + box(xa, xb, -w / 2, w / 2, sill + w / 2, top)


def plug_open(pc, x, top, d, w):
    '''
    Shoulder and plug with the window slot through them (its top corners rounded), added late so no cut can notch them.
    '''
    e  = 0.01
    sh = (cyl(SHOULDER, POST_OD / 2, x, 0, top - SHOULDER)
          - cyl(SHOULDER + 2 * e, POST_ID / 2 + e, x, 0, top - SHOULDER - e, r2=PLUG_ID / 2 - e))
    rg = cyl(PLUG_LEN, PLUG_OD / 2, x, 0, top) - cyl(PLUG_LEN + 2, PLUG_ID / 2, x, 0, top - 1)
    xa, xb = sorted((x, x + d * (POST_OD / 2 + 1)))
    pc.late.append((sh + rg) - slot_cutter(xa, xb, 0, top - SHOULDER - 1, top + PLUG_LEN, w, PLUG_SLOT_R))


def plate_wedges(par, yp, pairs, xB, xT, mingap=5.0):
    '''
    Rows of triangular openings through the back plate between stacked ramps.

    Each row fills the wedge between the top of the lower ramp wall and the shelf-plate corner of
    the upper ramp, both pulled in by a rib. Every opening has its apex up and 45 deg sides, so it
    closes from both sides and the plate above it needs no support.

    Args:
        par   (dict): cascade block; "rib" is the margin around the rows, "rib_w" the web between
                      openings, "hole_h" the tallest opening [mm]
        yp    (float): y of the plate face
        pairs (list): (upper floor line, lower floor line) per row; lower None means the bed
        xB    (float): x of the lower turn
        xT    (float): x of the upper turn

    Returns:
        Manifold: the cut
    '''
    rib, rw, hmax = par['rib'], par.get('rib_w', 4.0), par.get('hole_h', 25.0)
    zp  = CH_R - RO * np.cos(np.pi / 4) - (RO * np.sin(np.pi / 4) - yp)    # shelf-plate corner under the floor
    cut = []
    for k, (up, lo) in enumerate(pairs):
        lo_l = (lambda x: rib) if lo is None else (lambda x, lo=lo: lo(x) + CH_H + rib)
        up_l = lambda x, up=up: up(x) + zp - rib
        l0   = lo_l(0.0)
        sl   = lo_l(1.0) - l0
        za   = lambda x: min(up_l(x), lo_l(x) + hmax)
        xl   = lambda xc: (l0 + xc - za(xc)) / (1 - sl)       # left base corner of the 45 deg triangle
        xr   = lambda xc: (za(xc) + xc - l0) / (1 + sl)       # right base corner
        cur  = xB
        while cur < xT:
            try:
                xc = brentq(lambda v: xl(v) - cur, cur, cur + 400)
            except ValueError:
                cur += 1.0
                continue
            if za(xc) - lo_l(xc) < mingap:
                cur += 1.0
                continue
            if xr(xc) > xT:
                break
            tri = [(xl(xc), lo_l(xl(xc))), (xr(xc), lo_l(xr(xc))), (xc, za(xc))]
            cs  = CrossSection([np.array(tri, float)], FillRule.EvenOdd).extrude(4.0)
            cut.append(cs.rotate((90, 0, 0)).translate((0, yp + 0.15 + 0.5, 0)))
            cur = xr(xc) + rw
    return union(cut)


def plate_wedges_full(par, yp, pairs, xB, xT, mingap=3.0):
    '''
    Full wedge openings through the back plate between stacked ramps, top edge chamfered 45 deg
    toward the back. The long sloped top edge starts in the air, so the slicer adds trees under it.

    Args:
        par   (dict): cascade block; "rib" is the margin above each opening, "rib_lo" the margin
                      below it (0 trims the plate to the lower rim), "pillar_x" the x the openings start at;
                      the opening under the lowest ramp takes the plate away down to the bed
        yp    (float): y of the plate face
        pairs (list): (upper floor line, lower floor line) per wedge; lower None means the bed
        xB    (float): x of the lower turn
        xT    (float): x of the upper turn

    Returns:
        Manifold: the cut
    '''
    rib, rlo = par['rib'], par.get('rib_lo') or 0.0
    xmin = par.get('pillar_x') or xB
    zp  = CH_R - RO * np.cos(np.pi / 4) - (RO * np.sin(np.pi / 4) - yp)
    yf  = yp + 0.15
    cut = []
    for k, (up, lo) in enumerate(pairs):
        bed = lo is None
        zlo = (lambda x: -1.0) if bed else (lambda x, lo=lo: lo(x) + CH_H - 0.3 + rlo)
        if k == 1 and par.get('low_strip'):
            ## drop the bottom edge to a strip hugging the back of the lowest ramp, so the opening can start at the pillar
            zlo = lambda x, lo=lo: lo(x) + zp + 0.3 + par['low_strip']
        zup = (lambda x, up=up: up(x) + zp + 0.3) if bed else (lambda x, up=up: up(x) + zp - rib)
        xs  = np.linspace(par['plate_xl'] if bed else xmin, par['span'] if bed else par.get('plate_xr', xT), 400)
        ok  = np.array([zup(x) - zlo(x) >= (0.5 if bed else mingap) for x in xs])
        if not ok.any():
            continue
        x0, x1 = xs[ok][0] - (1.0 if bed else 0.0), xs[ok][-1]
        v = []
        for y in (yf + 0.5, yf - 3.5):
            dz = 0.0 if bed else yf - y
            v += [(x0, y, zlo(x0)), (x1, y, zlo(x1)), (x1, y, zup(x1) + dz), (x0, y, zup(x0) + dz)]
        cut.append(Manifold.hull_points(np.array(v, float)))
    return union(cut)


def cascade(par):
    '''
    Build the piece.

    Args:
        par (dict): "cascade" block of the config plus span and pitch

    Returns:
        tuple: Manifold, list of marble centres, dict of key heights
    '''
    S, P, w, d = par['span'], par['pitch'], par['win_w'], par['drop']
    rb, rp     = POST_ID / 2, POST_OD / 2
    ## posts: emit (raised, window +x) at x = 0, receive (on the bed, window -x) at x = S
    z0e  = par['levels'] * P
    se   = z0e + par['sill_e']
    sr   = par['sill_r']
    xs   = rb                                           # ramp 1 floor at the emit bore wall
    xr   = S - rb                                       # ramp 3 floor at the receive bore wall
    xT   = S - rp - par['gap'] - par['hole_r'] - par['end']
    xB   = rp + par['gap'] + par['hole_r'] + par['end']
    run  = (xT - xs) + (xT - xB) + (xr - xB)
    k    = (se - sr - 2 * d) / run
    f1   = lambda x: se - k * (x - xs)
    f2   = lambda x: f1(xT) - d - k * (xT - x)
    f3   = lambda x: f2(xB) - d - k * (x - xB)
    a1, a3   = se + k * xs, f3(0)                       # floor heights of the lines at x = 0
    a2       = f2(0)
    ce       = par['hole_r'] + par['end']               # [mm] hole centre to ramp end
    yp       = -(RO - 1.0)                              # plate face
    out, inn = profiles(yp)

    pc = Piece()
    ## ramps: outer shells, inner channels, drop holes
    pc.solid += [ramp(out, 0.0, xT + ce, a1, k), ramp(out, xB - ce, xT + ce, a2, -k), ramp(out, xB - ce, S, a3, k)]
    ## channels stop at the post walls; the windows carry the marble through them
    pc.cut   += [ramp(inn, rp, xT + par['hole_r'], a1, k),
                 ramp(inn, xB - par['hole_r'], xT + par['hole_r'], a2, -k),
                 ramp(inn, xB - par['hole_r'], S - rp, a3, k)]
    ## drop holes run out through the front wall: a round hole through the 45 deg shelf
    ## leaves a shallow arch on its front side that the slicer bridges with a tree
    hr = par['hole_r']
    pc.cut   += [box(xT - hr, xT + hr, -hr, RO + 1, f2(xT) + CH_H + 0.1, f1(xT) + CH_H + 1),
                 box(xB - hr, xB + hr, -hr, RO + 1, f3(xB) + CH_H + 0.1, f2(xB) + CH_H + 1)]

    ## back plate on the bed, top along the highest ramp, 45 deg edge up to the raised post
    ## edges sit 0.3 mm inside the ramp faces so no faces coincide
    xe   = xT + ce - 0.3
    xl   = rp + par['gap']
    ze   = z0e - 2.0
    zw   = CH_H - 0.3
    top1 = [(x, f1(x) + zw) for x in np.linspace(xe, 3.0, 2)]
    pts  = [(xl, 0), (S, 0), (S, f3(S) + zw), (xe, f3(xe) + zw)] + top1 + [(3.0, ze + xl - 3.0), (xl, ze)]
    if par.get('pillar_r'):
        ## plate ends at the ramp ends, so the wall beside the receive post is one narrow pillar
        pts = [(xl, 0), (xe, 0)] + top1 + [(3.0, ze + xl - 3.0), (xl, ze)]
        par['plate_xr'] = xe - par['pillar_r']
    pl   = CrossSection([np.array(pts, float)], FillRule.EvenOdd).extrude(par['plate'])
    pl = pl.rotate((90, 0, 0)).translate((0, yp + 0.15, 0))
    par['plate_xl'] = xl
    if par.get('rib'):
        pl = pl - (plate_wedges_full if par.get('wedge') else plate_wedges)(par, yp, [(f1, f2), (f2, f3), (f3, None)], xB, xT)
    pc.solid.append(pl)

    ## emit post: socket under a 45 deg cone, floor tilted toward the window, open window
    zt = z0e + P
    pc.solid.append(cyl(P, rp, 0, 0, z0e))
    pc.cut.append(cyl(SOCKET + 0.01, rb, 0, 0, z0e - 0.01) + cyl(rb, rb, 0, 0, z0e + SOCKET, r2=0.0))
    s   = par['floor_tilt']
    fl  = lambda x: se + s * (rb - x)
    hp  = [(x, y, z) for x in (-rb - 1, rb + 1) for y in (-rb - 1, rb + 1) for z in (fl(x), zt + 2)]
    pc.cut.append(cyl(zt + 1 - se + 8, rb, 0, 0, se - 8) ^ Manifold.hull_points(np.array(hp, float)))
    we = par.get('win_w_e') or w
    wt = par.get('win_top') or we                        # width above the round bottom: the post wall beside the window goes
    pc.cut.append(window(0.0, +1, se, we, zt + 1, rb - 1.8))
    pc.cut.append(box(rb - 1.8, rp, -wt / 2, wt / 2, se + we / 2, zt + 1))
    plug_open(pc, 0.0, zt, +1, wt)

    ## receive post: open bore, open window
    pc.solid.append(cyl(P, rp, S, 0, 0))
    pc.cut.append(cyl(P + 0.02, rb, S, 0, -0.01))
    pc.cut.append(window(S, -1, sr, w, P + 1, 0.0))
    plug_open(pc, S, P, -1, w)

    m  = pc.build() ^ box(-50, S + 50, -50, 50, 0, 400)
    mr = MARBLE / 2
    lift = lambda f: f + mr
    mb = [(60.0, 0.0, lift(f1(60.0))), (xT, 0.0, (f1(xT) + f2(xT)) / 2 + 2), (100.0, 0.0, lift(f2(100.0))), (130.0, 0.0, lift(f3(130.0)))]
    info = {'k_deg': np.degrees(np.arctan(k)), 'xT': xT, 'xB': xB, 'sill_e': se, 'sill_r': sr, 'z0e': z0e,
            'f1T': f1(xT), 'f2T': f2(xT), 'f2B': f2(xB), 'f3B': f3(xB), 'top': zt + PLUG_LEN}
    return m, mb, info


def main():
    cfg  = load_cfg()
    dirs = out_dirs(cfg)
    par  = dict(cfg['cascade'])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--span', type=float, default=par['span'])    # [mm] post centre to centre
    ap.add_argument('--out' , default=dirs['custom'])            # printable STL
    ap.add_argument('--prev', default=dirs['preview'])           # marbles
    ap.add_argument('--name', default='cascade_l')
    ap.add_argument('--rib' , type=float, default=0.0)           # [mm] margin around plate openings, 0 = none
    ap.add_argument('--wedge', action='store_true')              # full wedge openings instead of triangles
    ap.add_argument('--rib_lo', type=float, default=None)        # [mm] plate left above the lower rim, default 0 = trimmed to the rim
    ap.add_argument('--pillar_x', type=float, default=None)      # [mm] x the openings start at, default = lower turn
    ap.add_argument('--win_w_e', type=float, default=None)       # [mm] width of the emit (raised post) window
    ap.add_argument('--win_top', type=float, default=None)       # [mm] emit window width above its round bottom
    ap.add_argument('--low_strip', type=float, default=None)     # [mm] plate left above the lowest ramp's shelf corner
    ap.add_argument('--pillar_r', type=float, default=None)      # [mm] width of the plate pillar beside the receive post
    a = ap.parse_args()
    par.update(span=a.span, pitch=cfg['tube_pitch'], rib=a.rib, wedge=a.wedge, rib_lo=a.rib_lo, pillar_x=a.pillar_x, win_w_e=a.win_w_e, win_top=a.win_top, low_strip=a.low_strip, pillar_r=a.pillar_r)
    m, mb, info = cascade(par)
    t = export(m, os.path.join(a.out, a.name + '.stl'))
    if a.rib:
        ## drop the zero-thickness slivers the plate cut leaves against the ramp ends
        t = max(t.split(only_watertight=False), key=lambda b: len(b.faces))
        t.export(os.path.join(a.out, a.name + '.stl'))
    ms = [trimesh.creation.icosphere(subdivisions=3, radius=MARBLE / 2).apply_translation(p) for p in mb]
    trimesh.util.concatenate(ms).export(os.path.join(a.prev, a.name + '_marble.stl'))
    print(a.name, 'watertight', t.is_watertight, 'bodies', len(t.split(only_watertight=False)),
          'extents', np.round(t.extents, 1), 'volume', round(t.volume / 1000, 1), 'cm3')
    print(' '.join(f'{k}={v:.2f}' for k, v in info.items()))


if __name__ == '__main__':
    main()
