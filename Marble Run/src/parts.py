"""Shared building blocks for Marbleworks-compatible pieces. Units mm, z up.

Post convention (connector sizes from the fit ladder, config/project.json):
  - 50 mm stacking pitch; body OD 29.6, bore 25.6 (bottom 16 mm is the socket a lower plug enters)
  - plug end on top: split ring OD 25.75, bore 21.6, 11 mm tall, 12.8 mm slot
  - 'emit' post: solid floor + sloped wedge at sill height, side window -> marble leaves the column
  - 'recv' post: open bore, side window -> marble enters and drops down the column
"""
import os, sys, numpy as np, trimesh
from manifold3d import Manifold, CrossSection, FillRule, set_circular_segments
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_cfg
SEG = 72
set_circular_segments(SEG)

CFG = load_cfg()
CON = CFG["connector"]
PITCH = 50.0
POST_OD, POST_ID = CON["post_od"], CON["socket_id"]
PLUG_OD, PLUG_ID, PLUG_LEN = CON["plug_od"], CON["plug_id"], CON["plug_len"]
PLUG_SLOT = CON["plug_slot"]  # split-ring gap, faces +x
SOCKET = 16.0
MARBLE = CFG["marble"]
WIN_W, WIN_H = MARBLE + 7, MARBLE + 8
CH_R = MARBLE / 2 + 2.5      # channel inner radius (half-round bottom)
CH_WALL = 2.4
CH_H = 12.0                  # channel wall height above the bottom of the round

def cyl(h, r, x=0, y=0, z=0, r2=None):
    return Manifold.cylinder(h, r, r if r2 is None else r2).translate((x, y, z))

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))

def union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out

class Piece:
    """Collect solids, cuts and late-added solids, then resolve in the right order."""
    def __init__(self):
        self.solid, self.cut, self.late = [], [], []
    def build(self):
        m = union(self.solid)
        if self.cut:
            m = m - union(self.cut)
        if self.late:
            m = m + union(self.late)
        return m

SHOULDER = (POST_ID - PLUG_ID) / 2   # 45 deg shoulder height, as on the tubes and fit ladder

def add_plug(pc, x, y, top):
    """Split-ring plug on a 45 deg shoulder at height top, added late so no cut can notch it."""
    e = 0.01
    sh = (cyl(SHOULDER, POST_OD / 2, x, y, top - SHOULDER)
          - cyl(SHOULDER + 2 * e, POST_ID / 2 + e, x, y, top - SHOULDER - e, r2=PLUG_ID / 2 - e))
    ring = (cyl(PLUG_LEN, PLUG_OD / 2, x, y, top)
            - cyl(PLUG_LEN + 2, PLUG_ID / 2, x, y, top - 1)
            - box(x, x + PLUG_OD / 2 + 1, y - PLUG_SLOT / 2, y + PLUG_SLOT / 2, top - e, top + PLUG_LEN + 1))
    pc.late.append(sh + ring)

def post(pc, x, y, z0, kind, sill=None, dirs=(), plug=True):
    """Add a post. dirs: list of window directions in degrees (0 = +x)."""
    top = z0 + PITCH
    pc.solid.append(cyl(PITCH, POST_OD / 2, x, y, z0))
    if plug:
        add_plug(pc, x, y, top)
    if sill is None:
        sill = z0 + (25 if kind == "emit" else 22)
    if kind == "emit":
        pc.cut.append(cyl(SOCKET, POST_ID / 2, x, y, z0 - 0.01))
        pc.cut.append(cyl(top - sill + 0.01, POST_ID / 2, x, y, sill))
        a = np.radians(dirs[0])
        ## wedge: high opposite the window, low at the window
        w = Manifold.hull(box(-POST_ID / 2, -POST_ID / 2 + 0.1, -POST_ID / 2, POST_ID / 2, 0, 9)
                          + box(POST_ID / 2 - 0.1, POST_ID / 2, -POST_ID / 2, POST_ID / 2, 0, 0.1))
        w = (w ^ cyl(9, POST_ID / 2)).rotate((0, 0, dirs[0])).translate((x, y, sill))
        pc.late.append(w)
    else:
        pc.cut.append(cyl(PITCH + 0.02, POST_ID / 2, x, y, z0 - 0.01))
    for d in dirs:
        win = box(0, POST_OD / 2 + 4, -WIN_W / 2, WIN_W / 2, 0, WIN_H).rotate((0, 0, d)).translate((x, y, sill))
        pc.cut.append(win)
    return sill

def channel(pc, pts, h=CH_H, r=CH_R, wall=CH_WALL, cut_h=WIN_H):
    """U channel along a polyline of points (x, y, z_bottom). z is the inside bottom."""
    pts = [np.array(p, float) for p in pts]
    up = np.array([0, 0, 1.0])
    ro = r + wall
    outer, inner = [], []
    for a, b in zip(pts[:-1], pts[1:]):
        ca, cb = a + up * r, b + up * r          # centre of the round
        outer.append(Manifold.hull(Manifold.sphere(ro).translate(tuple(ca)) + Manifold.sphere(ro).translate(tuple(cb))
                                   + Manifold.sphere(ro).translate(tuple(ca + up * (h - r))) + Manifold.sphere(ro).translate(tuple(cb + up * (h - r)))))
        lift = up * (cut_h - r)   # cut stops at window height so it never slots the posts above
        inner.append(Manifold.hull(Manifold.sphere(r).translate(tuple(ca)) + Manifold.sphere(r).translate(tuple(cb))
                                   + Manifold.sphere(r).translate(tuple(ca + lift)) + Manifold.sphere(r).translate(tuple(cb + lift))))
    o = union(outer)
    ## flat top: trim outer at wall height along the path (per-segment slab)
    tops = []
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        dh = (b - a)[:2]
        n = np.array([-dh[1], dh[0], 0.0]) / (np.linalg.norm(dh) + 1e-9)
        t = np.append(dh / (np.linalg.norm(dh) + 1e-9), 0.0)
        ## extend each prism a little past its ends so joints are covered
        a2, b2 = a - t * (ro + 1) * (i == 0), b + t * (ro + 1) * (i == len(pts) - 2)
        corners = []
        for p in (a2, b2):
            for s in (-1, 1):
                for z in (h, 400):
                    corners.append(p + n * s * (ro + 3) + up * z)
        tops.append(Manifold.hull_points(np.array(corners)))
    o = o - union(tops)
    pc.solid.append(o)
    pc.cut.append(union(inner))

def text_cs(s, height, x, y, anchor="center", font="DejaVu Sans", weight="bold"):
    """2D text as a CrossSection, cap height ~height mm, centred at (x, y)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), s, size=height * 1.37, prop=FontProperties(family=font, weight=weight))
    polys = [p for p in tp.to_polygons() if len(p) > 2]
    cs = CrossSection([np.asarray(p, float) for p in polys], FillRule.EvenOdd)
    b = cs.bounds()
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return cs.translate((x - cx, y - cy))

def export(m, path):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))
    t.export(path)
    return t
