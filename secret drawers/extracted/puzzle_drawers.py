"""Two-layer puzzle drawer box ('Dial & Drawers'). Units mm, z up, box centred on x = y = 0.

Layout (world coordinates, assembled, everything closed):
  lower tube  z 0 .. 39.5   drawer A pulls out toward +X
  upper tube  z 39.5 .. 83  drawer B pulls out toward +Y, 6 mm of extra push-in travel behind it
  dial        flush disc in the top, rotates 30 deg about the centre cap

Locks:
  1. dial peg (hangs through an arc slot in the ceiling) sits in a notch of a block on B's front wall:
     B cannot move until the dial is turned 30 deg clockwise.
  2. a pin pressed into B's floor hangs through slots in both mid plates into A's cavity, just in front
     of A's rear wall: A cannot be pulled until B is PUSHED IN 6 mm, which lines the pin up with an
     escape notch in A's rear wall. Pulling B out does not free A.
  B is captive (its pin runs in a closed slot), so the puzzle cannot be solved by removing B.

Parts: lower tube, upper tube, drawer A, drawer B, dial (peg integral), centre cap, lock pin.
"""
import numpy as np, trimesh
from manifold3d import Manifold, CrossSection, set_circular_segments

SEG = 96
set_circular_segments(SEG)

# ------------------------------------------------------------------ parameters
W = 150.0                     # outer X and Y
WALL = 6.0                    # tube side walls (thick enough for the decoy pulls)
GAP = 0.5                     # drawer clearance per side and on top
CH = 1.5                      # outer edge chamfer
DR_H, DR_FLOOR, DR_WALL, DR_FRONT = 32.0, 3.0, 3.0, 8.0
CAV_H = DR_H + GAP            # 32.5
L_FLOOR, L_CEIL = 3.0, 4.0
U_FLOOR, U_CEIL = 4.0, 7.0
H_L = L_FLOOR + CAV_H + L_CEIL          # 39.5
H_U = U_FLOOR + CAV_H + U_CEIL          # 43.5
Z_U = H_L                               # base of the upper tube
TOP = Z_U + H_U                         # 83
Z_CEIL_U = TOP - U_CEIL                 # 76, underside of the upper ceiling
HALF = W / 2
IN = HALF - WALL                        # 69, inner wall face

# dial
DIAL_D, DIAL_T, DIAL_GAP = 134.0, 3.0, 0.3
PEG_D, PEG_R = 5.0, 58.0
PEG_HANG = 3.0
ARC_LOCK, ARC_OPEN = 90.0, 60.0         # peg angle (deg from +X) locked / unlocked
CAP_HEAD_D, CAP_HEAD_T, CAP_STEM_D = 12.0, 1.2, 5.0
CAP_HOLE_D = 4.8                        # press fit in the ceiling
DIAL_HOLE_D = 5.5                       # clearance in the dial

# B -> A lock pin
PIN_D = 6.0
PIN_X = -(IN - GAP - DR_WALL - 0.5 - PIN_D / 2)      # -62, just in front of A's rear wall
PIN_Y = -53.0                                        # with B closed
PUSH_IN, PULL = 6.0, 100.0                           # B travel: 6 in, 100 out
PIN_DIP = 2.5                                        # how far the pin reaches into A's cavity
PIN_HOLE_D = PIN_D - 0.2
SLOT_W = PIN_D + 0.6

# recessed finger pulls: a stadium mouth with a hook lip at the top, same on real fronts and decoy panels
PULL_W, PULL_H, PULL_HIDE = 36.0, 14.0, 3.0          # mouth width / height, extra pocket height hidden behind the lip
PULL_D, PULL_D_REAL, LIP_T = 4.2, 5.5, 2.0           # pocket depth on decoys / real drawer fronts, lip thickness
PULL_TOP = 5.0                                       # pocket top (behind the lip) below the panel top
GROOVE = 0.5                                         # decoy seam width and depth

# drawer envelopes (closed)
A_X0, A_X1 = -IN + GAP, HALF                         # -68.5 .. 75
A_Z0 = L_FLOOR
B_Y0, B_Y1 = -IN + GAP + PUSH_IN, HALF               # -62.5 .. 75
B_Z0 = Z_U + U_FLOOR


# ------------------------------------------------------------------ helpers
def cyl(h, r, x=0.0, y=0.0, z=0.0, r2=None, seg=SEG):
    return Manifold.cylinder(h, r, r if r2 is None else r2, seg).translate((x, y, z))


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out


def octagon(half, c):
    """Square of half size `half` with corners chamfered by c (2D)."""
    h = half
    pts = [(h - c, -h), (h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c), (-h + c, -h)]
    return CrossSection([np.array(pts, float)])


def chamfered_block(half, z0, z1, c, bottom=True, top=True):
    """Square block with chamfered vertical edges, optionally chamfered bottom / top edges."""
    parts = [Manifold.extrude(octagon(half, c), z1 - z0 - (c if bottom else 0) - (c if top else 0))
             .translate((0, 0, z0 + (c if bottom else 0)))]
    if bottom:
        parts.append(Manifold.extrude(octagon(half - c, c), 0.01).translate((0, 0, z0)))
    if top:
        parts.append(Manifold.extrude(octagon(half - c, c), 0.01).translate((0, 0, z1 - 0.01)))
    return Manifold.batch_hull(parts)


def rounded_square(half, r, z0, z1):
    cs = CrossSection.square((2 * (half - r), 2 * (half - r)), True).offset(r, 2, 2, SEG)
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


def slot_y(x, y0, y1, w, z0, z1):
    """Stadium slot along y (closed, rounded ends) through z0..z1."""
    return Manifold.hull(cyl(z1 - z0, w / 2, x, y0, z0) + cyl(z1 - z0, w / 2, x, y1, z0))


def arc_slot(r, a0, a1, w, z0, z1, step=2.0):
    angs = np.radians(np.arange(a0, a1 + 1e-6, step))
    cs = [cyl(z1 - z0, w / 2, r * np.cos(a), r * np.sin(a), z0) for a in angs]
    return union([Manifold.hull(a + b) for a, b in zip(cs[:-1], cs[1:])])


def seam_groove(face, u0, u1, z0, z1):
    """Decoy drawer seam: a rectangular groove loop on a face ('+x','-x','+y','-y')."""
    d, g = GROOVE, GROOVE
    sides = [(u0 - g, u0, z0 - g, z1 + g), (u1, u1 + g, z0 - g, z1 + g), (u0 - g, u1 + g, z1, z1 + g), (u0 - g, u1 + g, z0 - g, z0)]
    out = []
    for a0, a1, b0, b1 in sides:
        if face == '+x':
            out.append(box(HALF - d, HALF + 1, a0, a1, b0, b1))
        elif face == '-x':
            out.append(box(-HALF - 1, -HALF + d, a0, a1, b0, b1))
        elif face == '+y':
            out.append(box(a0, a1, HALF - d, HALF + 1, b0, b1))
        else:
            out.append(box(a0, a1, -HALF - 1, -HALF + d, b0, b1))
    return union(out)


def stadium_x(x0, x1, yc, zc, w, h):
    """Stadium (w along y, h along z) extruded along x from x0 to x1."""
    r = h / 2
    c = Manifold.cylinder(x1 - x0, r, r, SEG).rotate((0, 90, 0)).translate((x0, 0, 0))
    return Manifold.hull(c.translate((0, yc - (w / 2 - r), zc)) + c.translate((0, yc + (w / 2 - r), zc)))


def pull_pocket(face, z_panel_top, depth=PULL_D):
    """Recessed pull on a face at the top centre of a drawer-sized panel (cut it from the part)."""
    zt = z_panel_top - PULL_TOP
    mouth = stadium_x(HALF - LIP_T, HALF + 1, 0, zt - PULL_HIDE - PULL_H / 2, PULL_W, PULL_H)
    inner = stadium_x(HALF - depth, HALF - LIP_T + 0.01, 0, zt - (PULL_H + PULL_HIDE) / 2, PULL_W, PULL_H + PULL_HIDE)
    p = mouth + inner
    return p.rotate((0, 0, {'+x': 0, '+y': 90, '-x': 180, '-y': 270}[face]))


def front_chamfered_box(x0, x1, y0, y1, z0, z1, face, c=0.6):
    """Drawer body: box with a small chamfer around its front face."""
    if face == '+x':
        return Manifold.batch_hull([box(x0, x1 - c, y0, y1, z0, z1), box(x1 - 0.01, x1, y0 + c, y1 - c, z0 + c, z1 - c)])
    return Manifold.batch_hull([box(x0, x1, y0, y1 - c, z0, z1), box(x0 + c, x1 - c, y1 - 0.01, y1, z0 + c, z1 - c)])


# ------------------------------------------------------------------ parts (world coordinates)
def lower_tube():
    m = chamfered_block(HALF, 0, H_L, CH, bottom=True, top=False)
    m -= box(-IN, HALF + 1, -IN, IN, L_FLOOR, L_FLOOR + CAV_H)                 # cavity, open at +X
    m -= rounded_square(60.3, 3.3, H_L - 1.2, H_L + 1)                          # pocket for the upper tube's rim
    # pin slot through the ceiling; roof toward +X so it prints without bridging (tube stands on -X)
    zc0, zc1 = H_L - L_CEIL, H_L
    m -= slot_y(PIN_X, PIN_Y - PUSH_IN, PIN_Y + PULL, SLOT_W, zc0 - 1, zc1 + 1)
    x1 = PIN_X + SLOT_W / 2
    y0, y1 = PIN_Y - PUSH_IN - SLOT_W / 2, PIN_Y + PULL + SLOT_W / 2
    roof = np.array([[x1 - 0.3, y0, zc0 - 0.01], [x1 - 0.3, y0, zc1 + 0.01], [x1 + L_CEIL / 2, y0, (zc0 + zc1) / 2],
                     [x1 - 0.3, y1, zc0 - 0.01], [x1 - 0.3, y1, zc1 + 0.01], [x1 + L_CEIL / 2, y1, (zc0 + zc1) / 2]])
    m -= Manifold.hull_points(roof)
    for f in ('-x', '+y', '-y'):                                               # decoy panels with pulls
        m -= pull_pocket(f, A_Z0 + DR_H)
        m -= seam_groove(f, -(IN - GAP), IN - GAP, A_Z0, A_Z0 + DR_H)
    return m


def upper_tube():
    z0, z1 = Z_U, TOP
    m = chamfered_block(HALF, z0, z1, CH, bottom=False, top=True)
    m -= box(-IN, IN, -IN, HALF + 1, z0 + U_FLOOR, z0 + U_FLOOR + CAV_H)      # cavity, open at +Y
    m += rounded_square(60.0, 3.0, z0 - 1.0, z0 + 0.01) - rounded_square(57.0, 1.0, z0 - 2, z0 + 1)   # rim
    m -= slot_y(PIN_X, PIN_Y - PUSH_IN, PIN_Y + PULL, SLOT_W, z0 - 2, z0 + U_FLOOR + 1)           # pin slot (floor)
    m -= cyl(DIAL_T + 1, DIAL_D / 2 + DIAL_GAP, 0, 0, z1 - DIAL_T)                                 # dial recess
    m -= arc_slot(PEG_R, ARC_OPEN, ARC_LOCK, PEG_D + 0.6, Z_CEIL_U - 1, z1 + 1)                  # peg arc slot
    m -= cyl(U_CEIL + 2, CAP_HOLE_D / 2, 0, 0, Z_CEIL_U - 1)                                      # cap stem hole
    for f in ('-y', '+x', '-x'):                                               # decoy panels with pulls
        m -= pull_pocket(f, B_Z0 + DR_H)
        m -= seam_groove(f, -(IN - GAP), IN - GAP, B_Z0, B_Z0 + DR_H)
    return m


def drawer_a():
    x0, x1, y0, y1, z0, z1 = A_X0, A_X1, -(IN - GAP), IN - GAP, A_Z0, A_Z0 + DR_H
    m = front_chamfered_box(x0, x1, y0, y1, z0, z1, '+x')
    m -= box(x0 + DR_WALL, x1 - DR_FRONT, y0 + DR_WALL, y1 - DR_WALL, z0 + DR_FLOOR, z1 + 1)
    ye = PIN_Y - PUSH_IN                                                        # escape notch in the rear wall
    m -= box(x0 - 1, x0 + DR_WALL + 1, ye - PIN_D / 2 - 1, ye + PIN_D / 2 + 1, z1 - PIN_DIP - 1.0, z1 + 1)
    m -= pull_pocket('+x', z1, PULL_D_REAL)
    return m


def drawer_b():
    x0, x1, y0, y1, z0, z1 = -(IN - GAP), IN - GAP, B_Y0, B_Y1, B_Z0, B_Z0 + DR_H
    m = front_chamfered_box(x0, x1, y0, y1, z0, z1, '+y')
    m -= box(x0 + DR_WALL, x1 - DR_WALL, y0 + DR_WALL, y1 - DR_FRONT, z0 + DR_FLOOR, z1 + 1)
    # lock block on the front wall, notch open at the top and toward +X
    m += box(-4, 4, PEG_R - PEG_D / 2 - 2.5, y1 - DR_FRONT + 0.01, z0 + DR_FLOOR - 0.01, z1)
    m -= box(-PEG_D / 2 - 0.3, 5, PEG_R - PEG_D / 2 - 0.3, PEG_R + PEG_D / 2 + 0.3, z1 - PEG_HANG - GAP - 0.5, z1 + 1)
    # boss and press-fit hole for the lock pin
    m += cyl(3.0, PIN_D, PIN_X, PIN_Y, z0 + DR_FLOOR - 0.01)
    m -= cyl(DR_FLOOR + 5, PIN_HOLE_D / 2, PIN_X, PIN_Y, z0 - 1)
    m -= pull_pocket('+y', z1, PULL_D_REAL)
    return m


def dial(angle=ARC_LOCK):
    """Disc with its peg; `angle` is the world angle of the peg (deg from +X)."""
    z0 = TOP - DIAL_T
    m = cyl(DIAL_T, DIAL_D / 2, 0, 0, z0)
    m -= cyl(DIAL_T + 2, DIAL_HOLE_D / 2, 0, 0, z0 - 1)
    m -= cyl(CAP_HEAD_T + 1, CAP_HEAD_D / 2 + 0.2, 0, 0, TOP - CAP_HEAD_T)
    for k in range(8):                                                           # grip dimples
        a = np.radians(angle - 90 + 45 * k)
        m -= cyl(2, 3.0, 0.78 * DIAL_D / 2 * np.cos(a), 0.78 * DIAL_D / 2 * np.sin(a), TOP - 1.0)
    a = np.radians(angle)
    m += cyl(DIAL_T - 0.01 + (TOP - DIAL_T - Z_CEIL_U) + PEG_HANG, PEG_D / 2,
             PEG_R * np.cos(a), PEG_R * np.sin(a), Z_CEIL_U - PEG_HANG)
    return m


def cap():
    head = cyl(CAP_HEAD_T, CAP_HEAD_D / 2, 0, 0, TOP - CAP_HEAD_T)
    stem = cyl(TOP - CAP_HEAD_T - Z_CEIL_U, CAP_STEM_D / 2, 0, 0, Z_CEIL_U)
    return head + stem


def lock_pin():
    z0 = A_Z0 + DR_H - PIN_DIP
    z1 = B_Z0 + DR_FLOOR + 3.0
    body = cyl(z1 - z0 - 0.8, PIN_D / 2, PIN_X, PIN_Y, z0 + 0.8)
    tip = cyl(0.8, PIN_D / 2 - 0.8, PIN_X, PIN_Y, z0, r2=PIN_D / 2)
    return body + tip


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts), process=False)


# print orientations: (rotation xyz degrees) applied after moving the part to the origin
PRINT_ROT = {
    'lower_tube': (0, -90, 0),    # stands on its -X face, drawer opening up
    'upper_tube': (90, 0, 0),     # stands on its -Y face, drawer opening up
    'drawer_a': (0, 0, 0), 'drawer_b': (0, 0, 0),
    'dial': (180, 0, 0),          # top face on the bed, peg up
    'cap': (180, 0, 0),           # head on the bed
    'lock_pin': (0, 0, 0),
}


def all_parts(dial_angle=ARC_LOCK):
    return {'lower_tube': lower_tube(), 'upper_tube': upper_tube(), 'drawer_a': drawer_a(), 'drawer_b': drawer_b(),
            'dial': dial(dial_angle), 'cap': cap(), 'lock_pin': lock_pin()}


if __name__ == '__main__':
    import os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    for name, m in all_parts().items():
        t = to_trimesh(m)
        if PRINT_ROT[name] != (0, 0, 0):
            m = m.rotate(PRINT_ROT[name])
        bb = m.bounding_box()
        m = m.translate((-bb[0], -bb[1], -bb[2]))
        tp = to_trimesh(m)
        tp.export(f'{out}/{name}.stl')
        print(f'{name:11s} watertight {tp.is_watertight!s:5s} print bbox {np.round(tp.extents, 1)} mm  '
              f'volume {t.volume / 1000:6.1f} cm3')
