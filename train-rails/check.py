## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Checks: one closed body per part with a clean mesh, bed fit, layer heights, dimensions measured off the
built straight, and the fit of each joint against stand-in models of the ORIGINAL connector ends built
from the measurements (worst case where a measurement was uncertain). Joints: printed male into original
female, original male into printed female, printed into printed, on the straight, the curve and the test piece.

Stand-ins for the originals (worst case marked *):
  male: last tie 7.4 x 35 x 2.2 with no ends; rails raised 1.0 underneath for 13.5 *, inner edge 12.75 *;
        plate 1.0 thick, 22 wide *, 5.3 long; block 15.2 x 8.7 x 3.0 from 5.3 to 14.0; first full tie at 14.7
  female: bridge 5.0 long *; recess under it 1.0 tall *, 20.4 wide *, 5.5 deep; window 10.5 long *, 16.4 wide;
          prongs 25.5 apart, 46 outside, 13.5 past the end, 1.0 plate past the rail ends and an L-shaped
          2.1 raised part (3.0 rib plus the root inside the piece); deck 2.2 tall
"""
import math
import numpy as np
from manifold3d import Manifold
import track as T

BED = 220.0


def orig_male_stub(L=40.0, plate_half=11.0):
    """Original tab end as a straight stub, male end at the origin heading +x.
    plate_half 11.0 is the widest the plate could be (worst case for a printed female);
    10.15 matches the photos and is used when the two stand-ins are checked against each other."""
    p = T.Path(L)
    body = T.union([
        T.prism(T.rect(0, L, 15.9, 17.5), 0, 7.0, p), T.prism(T.rect(0, L, -17.5, -15.9), 0, 7.0, p),
        T.prism(T.rect(0, 7.4, -17.5, 17.5), 0, 2.2, p),
        T.prism(T.rect(14.7, 22.1, -23, 23), 0, 2.2, p),
        T.prism(T.rect(0, L, 10, 15.95), 0, 1.4, p), T.prism(T.rect(0, L, -15.95, -10), 0, 1.4, p),
        T.prism(T.rect(-5.3, 0.5, -plate_half, plate_half), 0, 1.0, p),
        T.prism(T.rect(-14.0, -5.3, -7.6, 7.6), 0, 3.0, p)])
    cuts = [T.prism(T.rect(-0.1, 13.5, 12.75, 30), -1, 1.0, p), T.prism(T.rect(-0.1, 13.5, -30, -12.75), -1, 1.0, p)]
    return T.diff(body, cuts)


def orig_female_stub(L=40.0):
    """Original prong end as a straight stub, female end at s = L."""
    p = T.Path(L)
    body = [T.prism(T.rect(0, L, 15.9, 17.5), 0, 7.0, p), T.prism(T.rect(0, L, -17.5, -15.9), 0, 7.0, p),
            T.prism(T.rect(L - 25, L, -17.5, 17.5), 0, 2.2, p)]
    for sg in (1, -1):
        thin = T.rect(L - 0.3, L + 13.5, 12.75, 20.0)        # thin plate only past the rail ends
        rib = T.rect(L - 5.5, L + 13.5, 20.0, 23.0)
        root = T.rect(L - 5.5, L, 17.4, 20.0)               # L-shaped raised part inside the piece
        if sg < 0:
            thin, rib, root = ([(s, -t) for s, t in q] for q in (thin, rib, root))
        body += [T.prism(thin, 0, 1.0, p), T.prism(rib, 0, 2.1, p), T.prism(root, 0, 2.1, p)]
    cuts = [T.prism(T.rect(L - 15.5, L - 5.0, -8.2, 8.2), -1, 10, p),
            T.prism(T.rect(L - 5.5, L + 0.1, -10.2, 10.2), -1, 1.0, p)]
    return T.diff(T.union(body), cuts)


def overlap(a, b):
    return (a ^ b).volume()


def bed_fit(m):
    """Smallest square footprint over rotations about z (degrees); fits if both sides <= BED."""
    best = None
    for ang in np.arange(0, 180, 1.0):
        b = m.rotate((0, 0, float(ang))).bounding_box()
        w, d = b[3] - b[0], b[4] - b[1]
        if best is None or max(w, d) < max(best[1], best[2]):
            best = (float(ang), w, d)
    return max(best[1], best[2]) <= BED, best


def layer_heights():
    """Every height in the model should land on a 0.2 mm layer boundary."""
    hs = {"rail": T.RAIL_H, "tie": T.TIE_H, "web": T.WEB_H, "end": T.END_H, "plate": T.PLATE_T,
          "male recess": T.M_RECESS_H, "female recess": T.F_RECESS_H, "prong plate": T.PRONG_THIN_H,
          "prong rib": T.PRONG_RIB_H, "block chamfer start": T.END_H - T.BLOCK_CH,
          "tie grain bottom": T.TIE_H - T.GRAIN_D, "plank grain bottom": T.END_H - T.GRAIN_D}
    return {k: (v, abs(v / 0.2 - round(v / 0.2)) < 1e-6) for k, v in hs.items()}


def play(fem, male_at_rest, path_f):
    """Free travel of the male piece relative to the female piece before they touch, in the joint frame:
    sideways (+/-), pulling apart (the block catches), lifting the male (the plate meets the bridge) and
    lifting the female (the prongs meet the male's rail ends)."""
    p, ang = path_f.frame(path_f.L)
    tx, ty = math.cos(ang), math.sin(ang)
    dirs = {"side +": (-ty, tx, 0), "side -": (ty, -tx, 0), "pull apart": (tx, ty, 0),
            "male up": (0, 0, 1), "female up": (0, 0, -1)}
    out = {}
    for k, d in dirs.items():
        d = np.array(d, float)
        hit = None
        for step in np.arange(0.05, 3.0001, 0.05):        # sweep, so a part cannot jump past an obstacle
            if overlap(fem, male_at_rest.translate(tuple(step * d))) > 1e-3:
                hit = step
                break
        if hit is None:
            out[k] = ">3"
            continue
        lo, hi = hit - 0.05, hit
        for _ in range(8):
            mid = (lo + hi) / 2
            if overlap(fem, male_at_rest.translate(tuple(mid * d))) < 1e-3:
                lo = mid
            else:
                hi = mid
        out[k] = f"{lo:.2f}"
    return out


def joint_checks(path_mine, mine):
    """mine: piece built on path_mine (male end at origin, female end at path_mine.L).
    Returns {joint: (overlap mm3, play dict)}."""
    res = {}
    of_path = T.Path(40.0)
    om, of = orig_male_stub(), orig_female_stub()
    om_on_mine = T.attach(om, path_mine)
    res["original male -> printed female"] = (overlap(mine, om_on_mine), play(mine, om_on_mine, path_mine))
    mine_on_of = T.attach(mine, of_path)
    res["printed male -> original female"] = (overlap(of, mine_on_of), play(of, mine_on_of, of_path))
    nxt = T.attach(mine, path_mine)
    res["printed male -> printed female"] = (overlap(mine, nxt), play(mine, nxt, path_mine))
    om2 = T.attach(orig_male_stub(plate_half=10.15), of_path)
    res["original -> original (stand-ins)"] = (overlap(of, om2), play(of, om2, of_path))
    return res


def rail_alignment(path):
    """Inner rail faces of a piece and the next one at the joint: lateral mismatch (should be 0)."""
    p, ang = path.frame(path.L)
    n = np.array([-math.sin(ang), math.cos(ang)])
    a = p + T.RAIL_IN * n
    q, ang2 = T.Path(10).frame(0.0)
    c, s = math.cos(ang), math.sin(ang)
    b = p + np.array([[c, -s], [s, c]]) @ (q + np.array([0, T.RAIL_IN]))
    return float(np.linalg.norm(a - b))


def probe(m, s0, s1, t0, t1, z0, z1):
    """Bounding box (s0, t0, z0, s1, t1, z1) of the part of m inside a probe box (straight piece coordinates)."""
    box = Manifold.cube((s1 - s0, t1 - t0, z1 - z0)).translate((s0, t0, z0))
    b = (m ^ box).bounding_box()
    return tuple(round(v, 3) for v in b)


def dimensions(st):
    """Measure the built straight (independent of the parameters) against the target numbers."""
    L = T.STRAIGHT_L
    out = []
    # gauge: between ties, above the ties, only the rails are present
    left = probe(st, 69, 71, 0, 30, 4, 6); right = probe(st, 69, 71, -30, 0, 4, 6)
    out.append(("gauge (inside rail to inside rail)", left[1] - right[4], 31.8))
    out.append(("rail thickness", left[4] - left[1], 1.7))
    out.append(("rail height", st.bounding_box()[5], 7.0))
    out.append(("tie top", probe(st, T.tie_centers(L)[3] - 1, T.tie_centers(L)[3] + 1, -1, 1, 0, 10)[5], 2.2))
    out.append(("tie length", probe(st, T.tie_centers(L)[3] - 1, T.tie_centers(L)[3] + 1, -30, 30, 0, 1)[4]
                - probe(st, T.tie_centers(L)[3] - 1, T.tie_centers(L)[3] + 1, -30, 30, 0, 1)[1], 46.0))
    out.append(("rail end to rail end", probe(st, -1, L + 1, 15.95, 17.55, 4, 6)[3] - probe(st, -1, L + 1, 15.95, 17.55, 4, 6)[0], 164.0))
    out.append(("tab plate thickness", probe(st, -4, -1, -1, 1, -1, 5)[5], 0.8))
    blk = probe(st, -20, -1, -12, 12, 1.5, 2.5)          # above the plate, below the chamfer
    out.append(("block length", blk[3] - blk[0], T.BLOCK_S1 - T.BLOCK_S0))
    out.append(("block width", blk[4] - blk[1], 15.1))
    out.append(("block reaches past the end face", -blk[0], 13.9))
    pr = probe(st, L + 1, L + 20, 0, 30, 0.2, 0.6)
    out.append(("prong inner edge (half gap)", pr[1], 13.1))
    out.append(("prong outer edge (half width)", pr[4], 23.0))
    out.append(("prong reaches past the end face", pr[3] - L, 13.3))
    out.append(("prong plate thickness", probe(st, L + 3, L + 5, 14, 19, -1, 5)[5], 0.8))
    out.append(("prong rib height", probe(st, L + 3, L + 5, 21, 22, -1, 5)[5], 2.2))
    # window: the gap in the deck along the centerline between the bridge and the far wall
    bridge = probe(st, L - 6, L + 1, -2, 2, 1.6, 2.2)      # between the recess and the end-face chamfer
    out.append(("bridge length (end face to window)", bridge[3] - bridge[0], 4.6))
    far = probe(st, L - 20, L - 8, -2, 2, 1.6, 2.2)
    out.append(("window length", bridge[0] - far[3], 11.0))
    side = probe(st, L - 10, L - 9, 0, 12, 1.6, 2.2)
    out.append(("window half width", side[1], 8.2))
    out.append(("recess under the bridge, height", probe(st, L - 2, L - 1, -1, 1, 0, 5)[2], 1.4))
    out.append(("recess under the male rail ends, height", probe(st, 9, 11, 16.0, 17.5, 0, 8)[2], 1.4))
    out.append(("male recess length", probe(st, 0, 30, 16.0, 17.5, 0, 0.5)[0], 14.2))
    return out


def mesh_quality(m):
    """Exported mesh: zero-area triangles, and whether it is still closed after an STL round trip (float32)."""
    import trimesh
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)
    v = tm.vertices.astype(np.float32).astype(float)
    t2 = trimesh.Trimesh(vertices=v[tm.faces].reshape(-1, 3), faces=np.arange(len(tm.faces) * 3).reshape(-1, 3), process=False)
    t2.merge_vertices()
    return int((tm.area_faces < 1e-10).sum()), bool(tm.is_watertight and t2.is_watertight)


def grain_check(m, r=0.24):
    """Wood grain at the groove bands (z 2.0 on ties, 2.8 on the end planks): grooves cut, no plastic land
    and no groove narrower than 2r (a morphological opening / closing of the slice loses or fills them).
    Returns {band: (groove area mm2, largest thin-land piece mm2, largest narrow-groove piece mm2)}."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def section(z):
        polys = [Polygon(p) for p in m.slice(z).to_polygons()]
        out = Polygon()
        for p in polys:                       # even-odd: contours alternate outer / hole
            out = out.symmetric_difference(p)
        return out

    res = {}
    for name, z_cut, z_below in (("ties", T.TIE_H - 0.2, T.TIE_H - T.GRAIN_D - 0.2),
                                 ("planks", T.END_H - 0.2, T.END_H - T.GRAIN_D - 0.2)):
        top, below = section(z_cut), section(z_below)
        grooves = below.difference(top)
        if name == "planks":                  # only count grooves on the planks, not the ties' tops below
            grooves = grooves.intersection(section(T.END_H - 0.1).buffer(2.0))
        thin = top.difference(top.buffer(-r).buffer(r))
        narrow = top.buffer(r).buffer(-r).difference(top)
        big = lambda g: max([q.area for q in getattr(g, "geoms", [g]) if not q.is_empty] + [0.0])
        res[name] = (grooves.area, big(thin), big(narrow))
    return res


def main():
    parts = {"straight": (T.straight(), T.Path(T.STRAIGHT_L)), "curve": (T.curve(), T.curve_path()),
             "test piece": (T.test_piece(), T.Path(T.TEST_L))}
    ok_all = True
    for name, (m, path) in parts.items():
        b = m.bounding_box()
        fits, (ang, w, d) = bed_fit(m)
        bodies = len(m.decompose())
        print(f"\n{name}: {b[3] - b[0]:.1f} x {b[4] - b[1]:.1f} x {b[5] - b[2]:.1f} mm, "
              f"{bodies} body, volume {m.volume() / 1000:.2f} cm3, bed {'fits' if fits else 'TOO BIG'} "
              f"({w:.0f} x {d:.0f} at {ang:.0f} deg)")
        ok_all &= bodies == 1 and fits and b[2] > -1e-6
        deg, closed = mesh_quality(m)
        ok_all &= deg == 0 and closed
        print(f"  mesh: {deg} zero-area triangles, {'closed' if closed else 'OPEN'} after an STL round trip")
        for k, (ov, pl) in joint_checks(path, m).items():
            flag = "ok" if ov < 1e-3 else "OVERLAP"
            ok_all &= ov < 1e-3
            print(f"  {k:34s} overlap {ov:7.3f} mm3 {flag:7s} play: " + ", ".join(f"{a} {b}" for a, b in pl.items()))
        print(f"  rail inner faces across the joint: {rail_alignment(path):.4f} mm apart")
    print("\nwood grain (lands and grooves narrower than 0.48 mm would show up as pieces > 0.25 mm2):")
    for name, (m, path) in parts.items():
        for band, (ga, thin, narrow) in grain_check(m).items():
            has_ties = bool(T.tie_centers(path.L, path.R))          # the test piece has no full ties
            ok = (ga > 1.0 or (band == "ties" and not has_ties)) and thin < 0.25 and narrow < 0.25
            ok_all &= ok
            print(f"  {name:10s} {band:6s} groove area {ga:6.1f} mm2, largest thin land {thin:5.3f}, "
                  f"largest narrow groove {narrow:5.3f}  {'ok' if ok else 'PROBLEM'}")
    print("\nstraight measured from the model (target in brackets):")
    for k, v, tgt in dimensions(parts["straight"][0]):
        ok = abs(v - tgt) < 0.02
        ok_all &= ok
        print(f"  {k:42s} {v:7.2f}  [{tgt}]  {'ok' if ok else 'MISMATCH'}")
    print("\nlayer heights (0.2 mm layers):")
    for k, (v, ok) in layer_heights().items():
        print(f"  {k:20s} {v:4.1f}  {'ok' if ok else 'OFF-LAYER'}")
        ok_all &= ok
    c = T.curve_path()
    print(f"\ncurve: R {T.CURVE_R} centerline, arc {c.L:.2f}; end to end {2 * T.CURVE_R * math.sin(math.radians(T.CURVE_DEG / 2)):.1f} "
          f"at the centerline, {2 * (T.CURVE_R + 17.5) * math.sin(math.radians(T.CURVE_DEG / 2)):.1f} at the outer rail; "
          f"8 curves {2 * (T.CURVE_R + 17.5) / 10:.1f} cm across at the outer rails")
    print("\nALL OK" if ok_all else "\nPROBLEMS FOUND")


if __name__ == "__main__":
    main()
