## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Concept pieces: racing finish, peg trays, combiners.

Usage:
    python src/pieces.py [race] [plinko] [comb] [--out stl/custom] [--prev preview]
"""
import argparse, os, sys, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import *
from project import out_dirs

ORD = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]

## ---------------------------------------------------------------- racing finish
def racing_finish(style="raised", n=10, slope_deg=2.5, depth=1.0):
    pc = Piece()
    sill = 14.0
    ## foot post: plug on top, no socket (it sits on the floor)
    pc.solid.append(cyl(PITCH, POST_OD / 2))
    add_plug(pc, 0, 0, PITCH)
    pc.cut.append(cyl(PITCH - sill + 0.01, POST_ID / 2, z=sill))
    w = Manifold.hull(box(-POST_ID / 2, -POST_ID / 2 + .1, -POST_ID / 2, POST_ID / 2, 0, 9)
                      + box(POST_ID / 2 - .1, POST_ID / 2, -POST_ID / 2, POST_ID / 2, 0, .1))
    pc.late.append((w ^ cyl(9, POST_ID / 2)).translate((0, 0, sill)))
    pc.cut.append(box(0, POST_OD / 2 + 4, -WIN_W / 2, WIN_W / 2, sill, sill + WIN_H))
    pc.solid.append(cyl(4, 32))                                   # round foot pad under the post
    ## lane block
    x0 = POST_ID / 2 - 1
    gap = 22.0                                                     # run-in before the last place
    x_end = x0 + gap + n * MARBLE + 2                             # inside end wall
    top = 24.0
    ledge = 26.0
    yl0, yl1 = -(CH_R + CH_WALL + ledge), CH_R + CH_WALL
    pc.solid.append(box(5, x_end + 4, yl0, yl1, 0, top))
    s = np.tan(np.radians(slope_deg))
    z_at = lambda x: sill - (x - x0) * s
    a = np.array([x0, 0, z_at(x0)]); b = np.array([x_end - CH_R, 0, z_at(x_end - CH_R)])
    up = np.array([0, 0, CH_R])
    pc.cut.append(Manifold.hull(union([Manifold.sphere(CH_R).translate(tuple(p + up + np.array([0, 0, dz])))
                                       for p in (a, b) for dz in (0, top + 1 - 2 * CH_R - p[2])])))
    ## place labels on the ledge; place 1 sits against the end wall
    yc = (yl0 + (-CH_R - CH_WALL)) / 2
    txt, ticks = [], []
    for k in range(n):
        xc = x_end - MARBLE / 2 - k * MARBLE
        txt.append(text_cs(ORD[k], 4.2, xc, yc))
        xt = xc - MARBLE / 2
        if True:
            ticks.append(CrossSection.square((0.8, ledge - 6)).translate((xt - 0.4, yl0 + 3)))
    ticks.append(CrossSection.square((0.8, ledge - 6)).translate((x_end - 0.4, yl0 + 3)))
    marks = txt + ticks
    cs = marks[0]
    for c in marks[1:]:
        cs = cs + c
    if style == "raised":
        pc.late.append(Manifold.extrude(cs, depth).translate((0, 0, top)))
    else:
        pc.cut.append(Manifold.extrude(cs, depth + 0.01).translate((0, 0, top - depth)))
    m = pc.build()
    marbles = [((x_end - MARBLE / 2 - k * MARBLE), 0, z_at(x_end - MARBLE / 2 - k * MARBLE) + MARBLE / 2)
               for k in range(4)]
    return m, marbles

## ---------------------------------------------------------------- peg tray (plinko)
def plinko(outlets=(0.0,), theta=30.0, half_w=45.0, wall_h=18.0, wall=2.4, floor=3.0):
    pc = Piece()
    E = (0.0, 0.0); zE = 100.0
    sill = post(pc, *E, zE, "emit", dirs=[0])
    O = np.array([POST_ID / 2 - 1, 0.0, sill])
    Lr = 150.0
    if len(outlets) == 1:
        poly = [(0, -half_w), (Lr, -half_w), (Lr + 34, -11), (Lr + 34, 11), (Lr, half_w), (0, half_w)]
        u_out = Lr + 34
    else:
        poly = [(0, -half_w), (Lr, -half_w), (Lr + 30, -39), (Lr + 30, -17), (Lr + 14, 0),
                (Lr + 30, 17), (Lr + 30, 39), (Lr, half_w), (0, half_w)]
        u_out = Lr + 30
    P = CrossSection([np.array(poly, float)])
    tray_out = Manifold.extrude(P.offset(wall, JoinType_round()), floor + wall_h).translate((0, 0, -floor))
    tray_in = Manifold.extrude(P, wall_h + 1)
    ## pegs: triangles pointing uphill (-u); wall deflectors on alternate rows
    pegs = []
    rows = [30, 58, 86, 114, 142]
    def tri(pts):
        return Manifold.extrude(CrossSection([np.array(pts, float)]), 14).translate((0, 0, -0.5))
    for i, u in enumerate(rows):
        if i % 2 == 0:
            for v in (-16, 16):
                pegs.append(tri([(u - 6, v), (u + 5, v - 5.5), (u + 5, v + 5.5)]))
        else:
            pegs.append(tri([(u - 6, 0), (u + 5, -5.5), (u + 5, 5.5)]))
            for sg in (-1, 1):
                pts = [(u - 10, sg * half_w), (u + 4, sg * (half_w - 12)), (u + 4, sg * half_w)]
                if sg < 0:
                    pts = pts[::-1]
                pegs.append(tri(pts))
    place = lambda m: m.rotate((0, theta, 0)).translate(tuple(O))
    pc.solid.append(place(tray_out))
    pc.cut.append(place(tray_in))
    pc.late.append(place(union(pegs)))
    ## outlet channels to receiver posts
    c, s_ = np.cos(np.radians(theta)), np.sin(np.radians(theta))
    recvs = []
    for v in outlets:
        F = O + np.array([(u_out - 4) * c, v, -(u_out - 4) * s_])
        yR = 0.0 if len(outlets) == 1 else np.sign(v) * 42.0
        xR = F[0] + 40
        toward_F = np.degrees(np.arctan2(F[1] - yR, F[0] - xR))
        sillR = post(pc, xR, yR, 0.0, "recv", dirs=[toward_F])
        channel(pc, [F, (xR, yR, sillR)])
        recvs.append((xR, yR))
    m = pc.build()
    ## marbles: one at the inlet, two bouncing among the pegs
    def loc(u, v, w=MARBLE / 2):
        return tuple(O + np.array([u * c + w * s_, v, -u * s_ + w * c]))
    marbles = [loc(14, 0), loc(44, -1), loc(100, 28)]
    return m, marbles

def JoinType_round():
    from manifold3d import JoinType
    return JoinType.Round

## ---------------------------------------------------------------- switchback cascade
def cascade(x=0.0, half=40.0):
    """Marble zigzags down three stacked ramps, dropping through a hole at each turn."""
    pc = Piece()
    yE, yR = -half - 28, half + 28
    sillE = post(pc, x, yE, 2 * PITCH, "emit", dirs=[90])
    sillR = post(pc, x, yR, 0.0, "recv", dirs=[-90])
    levels = [
        [(x, yE + POST_ID / 2 - 2, sillE), (x, half, sillE - 14)],
        [(x, half + 3, sillE - 44), (x, -half, sillE - 59)],
        [(x, -half - 3, sillE - 89), (x, yR, sillR)],
    ]
    for i, pts in enumerate(levels):
        channel(pc, pts, cut_h=16)
        if i < len(levels) - 1:
            ex, ey, ez = pts[-1]
            pc.cut.append(cyl(8, CH_R - 0.3, ex, ey, ez - 5))
    ## back plate ties the ramps and both posts together
    xb = x + CH_R + CH_WALL - 1.0
    pc.solid.append(box(xb, xb + 3, -half - 18, half + 18, sillE - 101, sillE + 12))
    m = pc.build()
    zf = lambda y: sillE - 14 * (y - (yE + 11.5)) / (half - (yE + 11.5))
    marbles = [(x, -15, zf(-15) + MARBLE / 2 + 0.6), (x, 10, sillE - 44 - 15 * (half - 10) / (2 * half) + MARBLE / 2 + 0.6)]
    return m, marbles

## ---------------------------------------------------------------- combiners
def combiner_y():
    pc = Piece()
    R = np.array([0.0, 0.0])
    M = np.array([-48.0, 0.0])
    Es = [np.array([-125.0, 46.0]), np.array([-125.0, -46.0])]
    sillR = post(pc, *R, 0.0, "recv", dirs=[180])
    zM = None
    for E in Es:
        d = M - E; ang = np.degrees(np.arctan2(d[1], d[0]))
        sillE = post(pc, *E, PITCH, "emit", dirs=[ang])
        start = E + d / np.linalg.norm(d) * (POST_ID / 2 - 2)
        L1 = np.linalg.norm(M - start); L2 = np.linalg.norm(R - M)
        zM = sillE - (sillE - sillR) * L1 / (L1 + L2)
        channel(pc, [(*start, sillE), (*M, zM), (*R, sillR)])
    m = pc.build()
    return m, [(-80, 27, 0)]  # marble placed later by caller

def combiner_opposite():
    pc = Piece()
    sillR = post(pc, 0, 0, 0.0, "recv", dirs=[0, 180])
    for x, ang in ((-105.0, 0), (105.0, 180)):
        sillE = post(pc, x, 0, PITCH, "emit", dirs=[ang])
        start = np.array([x + np.cos(np.radians(ang)) * (POST_ID / 2 - 2), 0])
        channel(pc, [(*start, sillE), (0, 0, sillR)])
    return pc.build(), []

def save(name, m, marbles, out, prev):
    t = export(m, f"{out}/{name}.stl")
    ms = []
    for p in marbles:
        s = trimesh.creation.icosphere(subdivisions=3, radius=MARBLE / 2); s.apply_translation(p); ms.append(s)
    if ms:
        trimesh.util.concatenate(ms).export(f"{prev}/{name}_marble.stl")
    print(name, "watertight", t.is_watertight, "extents", np.round(t.extents, 1))
    return t

def main():
    dirs = out_dirs()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("which" , nargs="*", default=["race", "plinko", "comb"])
    ap.add_argument("--out" , default=dirs["custom"])     # printable STLs
    ap.add_argument("--prev", default=dirs["preview"])    # marbles
    a = ap.parse_args()
    which, sv = a.which, lambda n, m, mb: save(n, m, mb, a.out, a.prev)
    if "race" in which:
        for st in ("raised", "inset"):
            m, mb = racing_finish(st); sv(f"finish_{st}", m, mb)
    if "plinko" in which:
        m, mb = plinko((0.0,)); sv("plinko_1out", m, mb)
        m, mb = plinko((-28.0, 28.0)); sv("plinko_2out", m, mb)
        m, mb = cascade(); sv("cascade", m, mb)
    if "comb" in which:
        m, _ = combiner_y(); sv("merge_y", m, [])
        m, _ = combiner_opposite(); sv("merge_opp", m, [])

if __name__ == "__main__":
    main()
