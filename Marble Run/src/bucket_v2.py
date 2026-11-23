## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Concept B, revision 3: drop down the post onto a concave fillet that runs tangent into a floor
sloped away from the post, slot open from floor to shoulder, bore-wide at the post and wider into the bucket,
larger bottom curve at the far end, rounded rim with inward lip, flared base.

Usage:
    python src/bucket_v2.py [--out stl/custom] [--prev preview] [--post_h 47.3] [--w 145.4] [--tilt 6] [--r_end 45] [--fil_rise 25]
"""
import argparse, os, sys, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stand import (Manifold, CrossSection, SEG, POST_OD, POST_ID, MALE_OD, MALE_ID, MALE_LEN,
                   MARBLE, cyl, box, bowl_cavity, post, export)
from project import load_cfg, out_dirs

def rrect_slab(hx, hy, rc, z0, z1):
    """Rounded-rectangle slab, half sizes hx, hy, vertical corner radius rc."""
    return Manifold.batch_hull([cyl(z1 - z0, rc, z0, sx * (hx - rc), sy * (hy - rc))
                                for sx in (-1, 1) for sy in (-1, 1)])

def bead(hx, hy, rc, z, r):
    """Round bead of radius r swept along a rounded-rectangle path centred at height z."""
    parts = []
    lx, ly = 2 * (hx - rc), 2 * (hy - rc)
    for sy in (-1, 1):   # straight runs along x
        parts.append(Manifold.cylinder(lx, r, r, SEG).rotate((0, 90, 0)).translate((-lx / 2, sy * hy, z)))
    for sx in (-1, 1):   # straight runs along y
        parts.append(Manifold.cylinder(ly, r, r, SEG).rotate((-90, 0, 0)).translate((sx * hx, -ly / 2, z)))
    q = Manifold.revolve(CrossSection.circle(r, SEG).translate((rc, 0)), SEG, 90.0)
    for i, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        parts.append(q.rotate((0, 0, 90 * i)).translate((sx * (hx - rc), sy * (hy - rc), z)))
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out

def end_cavity(w, d, floor, R, r_end, top):
    """bowl_cavity with a larger bottom radius r_end at the far (+x) end in the x-z section; rim plan unchanged."""
    s = []
    for y in (-d / 2 + R, d / 2 - R):
        s.append(Manifold.sphere(R, SEG).translate((-w / 2 + R, y, floor + R)))
        s.append(Manifold.sphere(1.0, SEG).scale((r_end, R, r_end)).translate((w / 2 - r_end, y, floor + r_end)))
        for x in (-w / 2 + R, w / 2 - R):
            s.append(cyl(1, R, top, x, y))
    return Manifold.batch_hull(s)

def floor_z(x, w, R, wall, tilt):
    """Height of the sloped floor at x: wall at the far (+x) end of the flat, rising tilt over the flat toward the post."""
    xf = w / 2 - R
    return wall + tilt * (xf - x) / (w - 2 * R)

def above_floor(x0, x1, yh0, yh1, z1, w, R, wall, tilt):
    """Prism from x0 to x1, half width yh0 at x0 widening to yh1 at x1, bottom on the sloped floor plane, top at z1."""
    return Manifold.hull_points(np.array([(x, y, z) for x, yh in ((x0, yh0), (x1, yh1)) for y in (-yh, yh)
                                          for z in (floor_z(x, w, R, wall, tilt), z1)]))

def house(x, hw, hf, z0, zt):
    """Slot section at x: half width hw from z0 up, closing at 45 deg to a flat of half width hf at the top zt."""
    zs = zt - (hw - hf)
    return [(x, sy * y, z) for sy in (-1, 1) for y, z in ((hw, z0), (hw, zs), (hf, zt))]

def side_bucket_v2(w=145.4, d=90, H=50, R=30, r_end=45, wall=4.0, post_h=70.0,
                   bead_r=3.5, lip=2.5, flare=10.0, flare_h=12.0,
                   ramp_gap=5.0, ramp_len=30.0, tilt=6.0, fil_rise=25.0, lintel_w=15.0, cheek=3.0):
    ox, oy, orc = w / 2 + wall, d / 2 + wall, R + wall          # outer half sizes, corner radius
    ## cavity sheared so its floor falls tilt over the flat, away from the post; vertical walls stay vertical
    k     = tilt / (w - 2 * R)
    shear = [[1, 0, 0, 0], [0, 1, 0, 0], [-k, 0, 1, k * (w / 2 - R)]]
    cav   = end_cavity(w, d, wall, R, r_end, H + 5).transform(shear)
    px = -w / 2 - wall - POST_OD / 2 + 9
    ## walls stop under the bead; bead sits on top and overhangs inward by `lip`
    zb = H - bead_r
    walls = rrect_slab(ox, oy, orc, 0, zb)
    hx, hy, hrc = w / 2 + bead_r - lip, d / 2 + bead_r - lip, R + bead_r - lip
    rim = bead(hx, hy, hrc, zb, bead_r)
    ## flared base: one smooth hull around bucket and post
    base = Manifold.batch_hull([
        rrect_slab(ox + flare, oy + flare, orc + flare, 0, 1.5),
        rrect_slab(ox, oy, orc, flare_h, flare_h + 0.1),
        cyl(1.5, POST_OD / 2 + flare + 6, 0, px, 0),
        cyl(0.1, POST_OD / 2, flare_h + 8, px, 0),
    ])
    ## only the post body and its shoulder + plug are used; the bore and slot are cut down to the floor plane below
    solid, _, wedge, _ = post(px, 0, 0, post_h, wall, +1)
    m = walls + base + rim
    m = m - cav
    ## rim flat at the post top out to ramp_gap past the post, then ramps up to H over ramp_len, so pieces on the post clear it
    if post_h < H:
        xa, xb, xl, yb, zt = px + POST_OD / 2 + ramp_gap, px + POST_OD / 2 + ramp_gap + ramp_len, px - POST_OD, oy + flare + 10, H + 10
        m = m - Manifold.hull_points(np.array([(x, y, z) for y in (-yb, yb) for x, z in
                                               ((xl, post_h), (xl, zt), (xa, post_h), (xb, H), (xb, zt))]))
    ## bore and slot cut down to the floor plane. the slot is never narrower than the bore: bore width at the post axis,
    ## widening to the flat-floor width (over two marbles) at the bucket wall, so a pair locked across the bore meets
    ## no jamb and comes apart. its top closes at 45 deg to a lintel_w flat under the shoulder, a short straight bridge
    xp, xe, xw = px + POST_OD / 2, -w / 2 + R, -w / 2
    hb, hl = POST_ID / 2, lintel_w / 2
    hc   = max(d / 2 - R, hb)
    sh_z = post_h - (POST_ID - MALE_ID) / 2
    fz   = lambda x: floor_z(x, w, R, wall, tilt)
    bore = cyl(post_h + 0.01, POST_ID / 2, 0, px, 0) ^ above_floor(px - POST_OD, px + POST_OD, POST_OD, POST_OD, post_h + 0.01, w, R, wall, tilt)
    slot = (Manifold.hull_points(np.array(house(px, hb, hl, fz(px), sh_z) + house(xw, hc, hl, fz(xw), sh_z)))
            + Manifold.hull_points(np.array(house(xw, hc, hl, fz(xw), sh_z) + house(xe, hc, hl, fz(xe), sh_z))))
    ## cheeks: the post blended into the bucket end wall and carried to the post front, so the wide slot has walls and the shoulder is supported
    neck = Manifold.batch_hull([cyl(post_h, POST_OD / 2, 0, px, 0), box(-w / 2 - wall, xp, -hc - cheek, hc + cheek, 0, post_h)])
    ## concave fillet from fil_rise up the back of the bore, tangent to the floor at xe: a falling marble strikes it
    ## at roughly 35-45 deg, keeps most of its speed along the surface, and leaves the post rolling with no step to catch on
    xb  = px - POST_ID / 2
    a0  = 2 * np.arctan(fil_rise / (xe - xb))                    # [rad] surface angle where it meets the back wall
    rc  = (xe - xb) / np.sin(a0)                                 # [mm] fillet radius
    fil = (box(xb - 1, xe, -POST_OD, POST_OD, wall - 1, wall + fil_rise)
           - Manifold.cylinder(2 * POST_OD, rc, rc, 4 * SEG).rotate((90, 0, 0)).translate((xe, POST_OD, wall + rc))).transform(shear)
    plug = wedge ^ box(px - POST_OD, px + POST_OD, -POST_OD, POST_OD, sh_z - 0.01, post_h + MALE_LEN + 1)
    m = m + solid + neck
    m = m - bore - slot
    m = m + (fil ^ (bore + slot)) + plug
    ## drop slivers and sealed voids left where the cuts meet (the main body has by far the largest volume)
    m = max(m.decompose(), key=lambda p: p.volume())
    rm = rc - MARBLE / 2                                         # [mm] radius of a marble centre's path on the fillet
    info = dict(cav_w=w, cav_d=d, depth=H - wall, R=R, r_end=r_end, tilt=tilt, slot_w=(2 * hb, 2 * hc), lintel_w=lintel_w, post_x=round(px, 1),
                fil_r=round(rc, 1), fil_a0=round(np.degrees(a0), 1),
                hit_deg=[round(np.degrees(np.arcsin((xe - x) / rm)), 1) for x in (px + 3.6, px, px - 3.6)],
                post_marble_z=round(wall + rc - rm * np.cos(np.arcsin((xe - px) / rm)) + k * (w / 2 - R - px), 1),
                foot=np.round(m.bounding_box()[3:5], 1), height=post_h + MALE_LEN,
                marble_at=(w / 2 - r_end, 0, floor_z(w / 2 - r_end, w, R, wall, tilt) + MARBLE / 2))
    return m, info

def main():
    cfg  = load_cfg()
    dirs = out_dirs(cfg)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out" , default=dirs["custom"])     # printable STLs
    ap.add_argument("--prev", default=dirs["preview"])    # cut-aways and marbles
    ap.add_argument("--post_h", type=float, default=cfg["tube_pitch"])  # [mm] post body height, plug on top
    ap.add_argument("--w"     , type=float, default=145.4)              # [mm] cavity length along x, 200 overall
    ap.add_argument("--tilt"  , type=float, default=6.0)                # [mm] floor rise at the post end
    ap.add_argument("--r_end" , type=float, default=45.0)               # [mm] bottom radius at the far end
    ap.add_argument("--fil_rise", type=float, default=25.0)             # [mm] height of the post fillet on the back wall
    a = ap.parse_args()
    out, prev = a.out, a.prev
    m, info = side_bucket_v2(w=a.w, post_h=a.post_h, tilt=a.tilt, r_end=a.r_end, fil_rise=a.fil_rise)
    k = "bucket_side2"
    t = export(m, f"{out}/{k}.stl")
    tc = export(m.trim_by_plane((0, 1, 0), 0.0), f"{prev}/{k}_cut.stl")
    cap = (np.abs(tc.triangles_center[:, 1]) < 0.01) & (tc.face_normals[:, 1] < -0.99)
    trimesh.Trimesh(tc.vertices, tc.faces[cap]).export(f"{prev}/{k}_cut_face.stl")
    for suf, y in (("", 18.0), ("_cut", 0.0)):
        mb = trimesh.creation.icosphere(subdivisions=3, radius=MARBLE / 2)
        ## first marble at the low (far) end, second on the fillet at the bottom of the post
        mx, _, mz = info["marble_at"]
        mb2 = mb.copy(); mb.apply_translation((mx, y, mz))
        mb2.apply_translation((info["post_x"], 0.0, info["post_marble_z"]))
        trimesh.util.concatenate([mb, mb2]).export(f"{prev}/{k}{suf}_marble.stl")
    print(k, "watertight", t.is_watertight, "extents", np.round(t.extents, 1),
          "vol cm3", round(t.volume / 1000, 1), info)

if __name__ == "__main__":
    main()
