## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Bucket-stand concepts for a Marbleworks-style marble run. Units: mm, z up.

Usage:
    python src/stand.py [--out stl/custom] [--prev preview]
"""
import argparse, os, sys, numpy as np, trimesh
from manifold3d import Manifold, CrossSection, JoinType

SEG = 96
Manifold.set_circular_segments(SEG) if hasattr(Manifold, "set_circular_segments") else None
try:
    from manifold3d import set_circular_segments
    set_circular_segments(SEG)
except Exception:
    pass

## connector sizes from the fit ladder (config/project.json)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_cfg
CFG = load_cfg()
CON = CFG["connector"]
POST_OD, POST_ID = CON["post_od"], CON["socket_id"]      # post body
MALE_OD, MALE_ID, MALE_LEN = CON["plug_od"], CON["plug_id"], CON["plug_len"]  # split-ring end that slides into a tube socket
MALE_SLOT = CON["plug_slot"]                              # split-ring gap, faces +x
MARBLE = CFG["marble"]

def cyl(h, r, z=0, x=0, y=0, r2=None):
    return Manifold.cylinder(h, r, r if r2 is None else r2, SEG).translate((x, y, z))

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))

def rounded_box(x0, x1, y0, y1, z0, z1, rv, rb):
    """Vertical corner radius rv, bottom-edge radius rb (flat bottom, square top)."""
    pts = []
    for x in (x0 + rv, x1 - rv):
        for y in (y0 + rv, y1 - rv):
            pts.append(cyl(z1 - z0 - rb, rv, z0 + rb, x, y))
            pts.append(Manifold.sphere(rb, SEG).scale((rv / rb, rv / rb, 1)).translate((x, y, z0 + rb)))
    return Manifold.batch_hull(pts)

def bowl_cavity(cx, cy, w, d, floor, R, top):
    """Rounded cavity: every bottom edge and corner has radius R."""
    s = []
    for x in (cx - w / 2 + R, cx + w / 2 - R):
        for y in (cy - d / 2 + R, cy + d / 2 - R):
            s.append(Manifold.sphere(R, SEG).translate((x, y, floor + R)))
            s.append(cyl(1, R, top, x, y))
    return Manifold.batch_hull(s)

def post(x, y, z_base, z_top, chute_z, exit_dir):
    """Hollow post with a sloped floor at chute_z and a window facing exit_dir (+1 = +x)."""
    body = cyl(z_top - z_base, POST_OD / 2, z_base, x, y)
    bore = cyl(z_top - chute_z, POST_ID / 2, chute_z, x, y)
    ## split-ring male end on a 45 deg shoulder, returned with the wedge so it is added after the cuts
    e, sh_h = 0.01, (POST_ID - MALE_ID) / 2
    shoulder = (cyl(sh_h, POST_OD / 2, z_top - sh_h, x, y)
                - cyl(sh_h + 2 * e, POST_ID / 2 + e, z_top - sh_h - e, x, y, MALE_ID / 2 - e))
    male = (cyl(MALE_LEN, MALE_OD / 2, z_top, x, y)
            - cyl(MALE_LEN + 2, MALE_ID / 2, z_top - 1, x, y)
            - box(x, x + MALE_OD / 2 + 1, y - MALE_SLOT / 2, y + MALE_SLOT / 2, z_top - e, z_top + MALE_LEN + 1))
    solid = body
    hole = bore
    ## sloped floor: wedge filling the bore bottom, high at the back, low at the window
    wedge = Manifold.hull(
        box(x - POST_ID / 2, x - POST_ID / 2 + 0.1, y - POST_ID / 2, y + POST_ID / 2, chute_z, chute_z + 9)
        + box(x + POST_ID / 2 - 0.1, x + POST_ID / 2, y - POST_ID / 2, y + POST_ID / 2, chute_z, chute_z + 0.1))
    if exit_dir < 0:
        wedge = wedge.translate((-x, -y, 0)).rotate((0, 0, 180)).translate((x, y, 0))
    wedge = (wedge ^ cyl(20, POST_ID / 2, chute_z, x, y)) + shoulder + male
    win_w, win_h = MARBLE + 7, MARBLE + 10
    xs = (x, x + exit_dir * (POST_OD / 2 + 6))
    window = box(min(xs), max(xs), y - win_w / 2, y + win_w / 2, chute_z, chute_z + win_h)
    return solid, hole, wedge, window

def side_bucket(w, d, H, R, wall=4.0, post_h=70.0):
    """Post at -x end, rounded bucket beside it."""
    cav = bowl_cavity(0, 0, w, d, wall, R, H + 5)
    px = -w / 2 - wall - POST_OD / 2 + 9          # post overlaps the bucket wall
    x0 = px - POST_OD / 2
    outer = rounded_box(-w / 2 - wall, w / 2 + wall, -d / 2 - wall, d / 2 + wall, 0, H, min(R, 14), 3)
    ## flared foot under the post, blended into the bucket's base
    flare = Manifold.batch_hull([cyl(10, POST_OD / 2 + 9, 0, px, 0, POST_OD / 2),
                                 box(-w / 2 - wall, -w / 2, -d / 2, d / 2, 0, 10)])
    chute_z = H - 10
    solid, hole, wedge, window = post(px, 0, 0, post_h, chute_z, +1)
    m = outer + solid + flare
    m = m - cav - hole - window
    m = m + wedge
    ## round the bucket rim a little by trimming a chamfer ring is skipped in concept
    return m, dict(cav_w=w, cav_d=d, depth=H - wall, R=R, post_x=px, chute_z=chute_z,
                   foot=(w / 2 + wall - x0, d + 2 * wall), height=post_h + MALE_LEN,
                   marble_at=(0, 0, wall + MARBLE / 2))

def ring_bowl(outer_r=78.0, H=42.0, R=26.0, wall=4.0, post_h=70.0):
    """Post in the middle, round trough all the way around it."""
    inner_r = POST_OD / 2
    prof = CrossSection.square((outer_r - wall - R - (inner_r + R), 400)).translate((inner_r + R, wall + R))
    prof = prof.offset(R, JoinType.Round, 2, SEG)
    cav = Manifold.revolve(prof, SEG)
    outer_prof = CrossSection.square((outer_r - 3, H)).offset(3, JoinType.Round, 2, SEG) ^ CrossSection.square((outer_r + 5, H)).translate((0, 0))
    outer_prof = outer_prof ^ CrossSection.square((outer_r + 5, H + 5))
    outer = Manifold.revolve(outer_prof, SEG)
    chute_z = wall + R * 0.55
    solid, hole, wedge, window = post(0, 0, 0, post_h, chute_z, +1)
    m = outer - cav + solid
    m = m - hole - window
    m = m + wedge
    return m, dict(outer_d=2 * outer_r, depth=H - wall, R=R, chute_z=chute_z,
                   height=post_h + MALE_LEN, marble_at=(-31, 31, wall + MARBLE / 2))

def export(m, path):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))
    t.export(path)
    return t

def main():
    from project import out_dirs
    dirs = out_dirs()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out" , default=dirs["custom"])     # printable STLs
    ap.add_argument("--prev", default=dirs["preview"])    # cut-aways and marbles
    a = ap.parse_args()
    out, prev = a.out, a.prev
    concepts = {
        "bucket_ring": ring_bowl(),
        "bucket_side": side_bucket(w=100, d=90, H=50, R=30),
        "bucket_kid" : side_bucket(w=74, d=66, H=40, R=22),
    }
    for k, (m, info) in concepts.items():
        t = export(m, f"{out}/{k}.stl")
        ## cut-away copy: keep the back half (y >= 0) so the inside shows from the front
        tc = export(m.trim_by_plane((0, 1, 0), 0.0), f"{prev}/{k}_cut.stl")
        cap = (np.abs(tc.triangles_center[:, 1]) < 0.01) & (tc.face_normals[:, 1] < -0.99)
        trimesh.Trimesh(tc.vertices, tc.faces[cap]).export(f"{prev}/{k}_cut_face.stl")
        mbc = trimesh.creation.icosphere(subdivisions=3, radius=MARBLE / 2)
        mbc.apply_translation((info["marble_at"][0], 0, info["marble_at"][2]))
        mbc.export(f"{prev}/{k}_cut_marble.stl")
        mb = trimesh.creation.icosphere(subdivisions=3, radius=MARBLE / 2)
        mb.apply_translation(info["marble_at"])
        mb.export(f"{prev}/{k}_marble.stl")
        print(k, "watertight", t.is_watertight, "extents", np.round(t.extents, 1),
              "vol cm3", round(t.volume / 1000, 1), info)

if __name__ == "__main__":
    main()
