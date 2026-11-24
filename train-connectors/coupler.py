## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Replacement coupler for the battery Christmas-train cars (Nov 2026).

Each car has a black tab with a 4.5 mm hole at its front and a black loop at its back. The original red
hook snapped into the tab hole from below and reached forward into the next car's loop; it broke (twice)
at the corner above the drop leg. This replaces it with two printed parts and a short piece of
1.75 mm filament as the hinge pin:

- swivel: a flat bar under the tab with a split snap peg up through the hole (barbs front and back, like
  the original), and a knuckle in front of the tab's tip. It turns in the hole, so the coupler follows
  curves (the yaw joint).
- arm: hinged on the swivel's knuckle (the pitch joint) with a filament pin. Its flat underside rests on
  the next car's loop, and its leg drops through the loop's opening. The leg's back face is raked 30
  degrees, so the loop's end bar, pulled against it, pushes the arm down: the bar is clamped between the
  underside and the raked face, harder the harder the train pulls. The hinge sits level with the pull,
  so pulling neither lifts the car in front nor the car behind. Uncouple by pushing the cars together a
  couple of mm and lifting the arm.

Coordinates: x along the track from the tab hole toward the next car, y across, z up from the table with
both cars on the track. mm. Both parts are flat profiles in x-z extruded across y, printed on their side.
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, set_circular_segments
from shapely.geometry import Polygon, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity

set_circular_segments(96)

# ---------------- measured on the cars (Aaron, Nov 23 2026; cars on the track) ----------------
TAB_T = 1.5                      # tab thickness at the hole
TAB_TOP = 27.0                   # tab top above the table
TAB_W = 16.0                     # tab width
TAB_TIP = 6.0                    # tab reaches this far past the hole center
HOLE_D = 4.5
LOOP_T = 1.5
LOOP_TOP = 27.5
LOOP_W = 16.0
LOOP_OUT = 12.0                  # loop sticks out this far from the car's end wall
OPEN_L = 7.5                     # opening along the track
OPEN_W = 10.0                    # opening across

# ---------------- assumed (from photos, or not yet measured) ----------------
END_BAR = 2.25                   # loop's end bar along the track (opening assumed centered like the tab's hole)
TIP_R = 8.0                      # tab and loop ends are half circles across their 16 mm width
X_I = 22.0                       # pull spacing: hole center to the loop's end-bar inner edge. From the glued
                                 # original in the ruler photos (its leg 22 to 24 mm past the hole); measurement 9
                                 # will confirm. Changing it moves the leg and nothing else.
RIDGE_IN = 2.6                   # stand-in for the two raised ridges on top of the tab beside the hole
RIDGE_H = 1.8
RIDGE_X1 = 1.5

# ---------------- design ----------------
CLR = 0.15                       # vertical play of the swivel at the tab, each side (prints grow it a little)
PIN_D = 1.75                     # filament
SW_T = 2.4                       # swivel thickness (y); its peg is a 4.2 circle cut to this, so the barbs
                                 # stand out about evenly all round the hole
PLATE_Z1 = TAB_TOP - TAB_T - CLR # 25.35, plate top
PLATE_Z0 = 22.3
TONGUE_X = 13.5                  # plate runs on past the knuckle; the arm's stop lands on it
PEG_R = 2.1
SLOT_HALF = 0.7                  # 1.4 slot: the front prong is part of the plate (rigid, takes the pull);
                                 # the back prong is a 7 mm finger that flexes to let both barbs through
BOSS_Z0 = 19.9                   # peg runs on below the plate so the back finger is long
SLOT_Z0 = 20.9
BARB_R = 2.55                    # 0.30 past the hole edge on the centerline, 0.35 at the corners; about 0.15
                                 # is left if the print comes out 0.15 small per side
CATCH_Z = TAB_TOP + CLR          # underside of the barbs
BARB_LAND = 0.3
TIP_Z = 28.6
TIP_R_TOP = 1.6
KX, KZ = 9.5, 26.5               # hinge axis; KZ is level with the pull (bar contact at 26.0)
K_R = 2.4                        # swivel knuckle
K_HOLE = 1.3                     # 2.6 hole: turns freely on the filament even if it prints small
ARM_W = 7.6
SLOT_W = SW_T / 2 + 0.3          # half width of the slot in the arm
CHEEK_R = 2.7
ARM_HOLE = 1.15                  # 2.3 hole: prints about 1.8 to 2.0 and grips the filament; if loose, melt the pin ends
THETA = math.radians(30)         # rake of the leg's back face
BEAM_Z1 = 31.0
LEG_T = 3.0                      # leg thickness at the loop's top
LEG_Z0 = 23.0                    # leg bottom, 3 mm under the loop
LUG_X = (KX + CHEEK_R - 0.5, KX + 4.7)
LUG_Z0 = 24.0
PHI_STOP, PHI_UP = -15.0, 40.0   # arm travel: droop stop (checked), and enough lift to couple
SWEEP_DOWN = -10.5               # slot swept from here; the 0.3 clearance lets the arm droop on to about -15
SWEEP_CLR = 0.3

# derived
Z_BAR0 = LOOP_TOP - LOOP_T       # 26.0
X_THROAT = X_I + LOOP_T * math.tan(THETA)
X_FRONT = X_THROAT + LEG_T
X_LEG_BACK = X_I - (Z_BAR0 - LEG_Z0) * math.tan(THETA)
X_TIP = X_I - END_BAR            # loop's tip


# ---------------- 2D / 3D helpers ----------------
def cs(poly):
    """shapely (multi)polygon in (x, z) -> CrossSection."""
    polys = getattr(poly, "geoms", [poly])
    loops = []
    for p in polys:
        p = orient(p, 1.0)                        # exterior counterclockwise, holes clockwise
        loops.append(np.asarray(p.exterior.coords)[:-1])
        for h in p.interiors:
            loops.append(np.asarray(h.coords)[:-1])
    return CrossSection([l.tolist() for l in loops])


def extrude_y(poly, y0, y1):
    """Profile in (x, z), extruded across y0..y1."""
    m = Manifold.extrude(cs(poly), y1 - y0)       # profile in XY, extruded along +Z
    return m.rotate((90, 0, 0)).translate((0, y1, 0))   # (x, zp, e) -> (x, -e, zp), then shift


def circle(x, z, r):
    return Point(x, z).buffer(r, 128)


def rounded_rect(x0, z0, x1, z1, r):
    return box(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, 32) if r > 0 else box(x0, z0, x1, z1)


# ---------------- swivel ----------------
def swivel_profile():
    """Flat part of the swivel in x-z (no peg): plate from the front prong to a rounded tongue, and the knuckle."""
    plate = unary_union([box(SLOT_HALF, PLATE_Z0, TONGUE_X - 1.0, PLATE_Z1),
                         rounded_rect(TONGUE_X - 3.0, PLATE_Z0, TONGUE_X, PLATE_Z1, 1.0)])
    knuckle = circle(KX, KZ, K_R)
    return unary_union([plate, knuckle])


def peg():
    """Snap peg: a 4.2 post with a barb ring, cut to the swivel thickness, split front/back."""
    z_b = BOSS_Z0
    half = Polygon([(0, z_b), (PEG_R, z_b), (PEG_R, CATCH_Z), (BARB_R, CATCH_Z), (BARB_R, CATCH_Z + BARB_LAND),
                    (TIP_R_TOP, TIP_Z), (0, TIP_Z)])
    m = Manifold.revolve(cs(half), 128)
    slab = Manifold.cube((20, SW_T, 20), center=True).translate((0, 0, 25))
    return m ^ slab


def swivel():
    body = extrude_y(swivel_profile().difference(circle(KX, KZ, K_HOLE)), -SW_T / 2, SW_T / 2)
    body = body + peg()
    slot = Manifold.cube((2 * SLOT_HALF, SW_T + 2, TIP_Z - SLOT_Z0 + 1)).translate((-SLOT_HALF, -SW_T / 2 - 1, SLOT_Z0))
    return body - slot


# ---------------- arm ----------------
def leg_profile():
    pts =[(X_THROAT, LOOP_TOP), (X_LEG_BACK, LEG_Z0), (X_FRONT, LEG_Z0), (X_FRONT, LOOP_TOP)]
    return Polygon(pts)


def arm_outline():
    beam = box(KX, LOOP_TOP, X_FRONT, BEAM_Z1)
    lug = box(LUG_X[0], LUG_Z0, LUG_X[1], LOOP_TOP + 0.01)
    shape = unary_union([circle(KX, KZ, CHEEK_R), beam, leg_profile(), lug])
    # soften: top front corner, chamfer on the leg's front bottom, round the barb tip, fillet in the throat
    shape = shape.difference(Polygon([(X_FRONT - 1.0, BEAM_Z1 + 1), (X_FRONT + 1, BEAM_Z1 + 1), (X_FRONT + 1, BEAM_Z1 - 1.0)]))
    shape = shape.difference(Polygon([(X_FRONT - 0.8, LEG_Z0 - 1), (X_FRONT + 1, LEG_Z0 - 1), (X_FRONT + 1, LEG_Z0 + 0.8)]))
    shape = shape.buffer(-0.35, 32).buffer(0.35, 32)          # rounds convex corners (barb tip, lug)
    shape = shape.buffer(0.3, 32).buffer(-0.3, 32)            # fillets concave corners (throat, beam to cheek)
    return shape


def sweep_swivel(phi0=SWEEP_DOWN, phi1=PHI_UP, step=0.5, clr=SWEEP_CLR):
    """Region the swivel's flat part occupies in the arm's frame over the arm's travel."""
    prof = swivel_profile()
    shapes = []
    a = phi0
    while a <= phi1 + 1e-9:
        # the arm at angle a sees the swivel rotated by -a about the hinge
        shapes.append(affinity.rotate(prof, -a, origin=(KX, KZ)))
        a += step
    return unary_union(shapes).buffer(clr, 32)


def arm():
    outline = arm_outline()
    full = extrude_y(outline.difference(circle(KX, KZ, ARM_HOLE)), -ARM_W / 2, ARM_W / 2)
    slot = extrude_y(sweep_swivel(), -SLOT_W, SLOT_W)
    return full - slot


# ---------------- stand-ins for the cars ----------------
def tab():
    """Black tab at the front of a car, hole at the origin."""
    c = -(TIP_R - TAB_TIP)                       # center of the half-round tip
    outline = unary_union([Point(c, 0).buffer(TIP_R, 128), box(-14, -TAB_W / 2, c, TAB_W / 2)])
    outline = outline.difference(Point(0, 0).buffer(HOLE_D / 2, 128))
    base = Manifold.extrude(cs(outline), TAB_T).translate((0, 0, TAB_TOP - TAB_T))
    ridges = []
    for s in (-1, 1):
        r = box(-14, RIDGE_IN, RIDGE_X1, TAB_W / 2) if s > 0 else box(-14, -TAB_W / 2, RIDGE_X1, -RIDGE_IN)
        ridges.append(Manifold.extrude(cs(r), RIDGE_H).translate((0, 0, TAB_TOP)))
    return base + ridges[0] + ridges[1]


def loop(dx=0.0, dz=0.0):
    """Black loop at the back of the next car, at the pull position shifted by dx, dz; its end wall too."""
    c = X_TIP + TIP_R
    outline = unary_union([Point(c, 0).buffer(TIP_R, 128), box(c, -LOOP_W / 2, X_TIP + LOOP_OUT, LOOP_W / 2)])
    outline = outline.difference(box(X_I, -OPEN_W / 2, X_I + OPEN_L, OPEN_W / 2))
    m = Manifold.extrude(cs(outline), LOOP_T).translate((0, 0, Z_BAR0))
    wall = Manifold.cube((30, 40, 40)).translate((X_TIP + LOOP_OUT, -20, 18))
    return (m + wall).translate((dx, 0, dz))


def place_arm(a, phi):
    """Arm rotated by phi degrees about the hinge (positive lifts the leg)."""
    return a.translate((-KX, 0, -KZ)).rotate((0, -phi, 0)).translate((KX, 0, KZ))


def yaw(m, psi):
    return m.rotate((0, 0, psi))


if __name__ == "__main__":
    s, a = swivel(), arm()
    for name, m in (("swivel", s), ("arm", a)):
        b = m.bounding_box()
        print(f"{name}: {b[3]-b[0]:.1f} x {b[4]-b[1]:.1f} x {b[5]-b[2]:.1f} mm, {m.volume():.0f} mm3, genus {m.genus()}")
    print(f"throat {X_THROAT:.2f}, leg front {X_FRONT:.2f}, barb tip {X_LEG_BACK:.2f}, loop tip {X_TIP:.2f}")
