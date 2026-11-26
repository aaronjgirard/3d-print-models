## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Replacement coupler for the battery Christmas-train cars, version 2 (Nov 25 2026).

Every car has a black tab with a hole at its front and a black loop at its back; the hook on each car's tab
reaches forward into the loop of the car ahead (the tender's goes into the engine's loop). Version 1 (Nov 24)
printed and the clamp held well, but its snap peg was loose in the hole and fell out, its arm was too wide
for the engine's loop, and the arm's hinge hole strung up where the upper cheek bridged a slot.

Version 2 is three printed parts and two short pieces of 1.75 mm filament:

- kingpin: dropped in from the top. Its flat head sits on the tab between the tab's two ridges, its round
  4.55 mm shaft goes down through the 4.7 x 5.3 hole and through the swivel, and a piece of filament pushed
  through the hole at its tip, under the swivel, locks everything in. The head is too long to turn between
  the ridges, so the kingpin stays put and the swivel turns on it.
- swivel: a plate under the tab that turns on the kingpin (so the coupler follows curves), with a fork of
  two cheeks in front of the tab's tip that carries the hinge pin.
- arm: a plain 4.6 mm wide bar hinged between the cheeks (the pitch joint), narrow enough for the engine's
  6.2 mm loop. Its flat underside rests on the loop ahead and its leg drops through the opening. The leg's
  back face is raked 30 degrees from the underside down, so pulling draws the loop's end bar into the throat
  and clamps it between the underside and the raked face. Below the rake the leg runs straight down another
  2 mm (version 1 stopped at the end of the rake), so it reaches deeper under the loop.

Coordinates: x along the track from the tab hole toward the car ahead, y across, z up from the table with
the cars on the track; mm. Arm angles are about the hinge, positive lifting the leg.
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, set_circular_segments
from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity

set_circular_segments(96)

# ---------------- measured (Aaron; cars on the track) ----------------
TAB_T = 1.5                      # tab thickness at the hole (Nov 23)
TAB_TOP = 27.0                   # tab top above the table (Nov 23)
TAB_W = 16.0
TAB_TIP = 6.0                    # tab reaches this far past the hole center
TAB_L = 14.5                     # whole tab length (Nov 25)
HOLE_L, HOLE_W = 4.7, 5.3        # tab hole along x across (Nov 25; the Nov 23 "4.5" was a single caliper read)
RIDGE_TOP = TAB_TOP - TAB_T + 4.0  # two ridges on top of the tab, 4.0 above its underside (Nov 25)
RIDGE_LEN = 11.0                 # ridges run 11 of the tab's 14.5 mm from its root (Nov 25)
LOOP_T, LOOP_TOP = 1.5, 27.5     # the cars' loops (Nov 23)
LOOP_W, LOOP_OUT = 16.0, 12.0
OPEN_L, OPEN_W = 7.5, 10.0
E_LOOP_T, E_LOOP_TOP = 2.0, 25.5  # the engine's loop (Nov 25)
E_OPEN_L, E_OPEN_W = 9.5, 6.2

# ---------------- assumed ----------------
X_I = 22.0                       # tab hole center to a car loop's end-bar inner edge when pulling, from the glued
                                 # original in the ruler photos; measurement 9 (spacing) will confirm
END_BAR = 2.25                   # loop end bar along the track (both loops)
TIP_R = 8.0                      # tab and car-loop ends are half round across their 16 mm
RIDGE_IN = HOLE_W / 2            # inner faces of the ridges; not measured, taken as the hole's edges (worst case)
E_LOOP_W, E_LOOP_OUT = 14.0, E_OPEN_L + 2 * END_BAR   # engine loop's outline (only used by the checks)

# ---------------- design ----------------
CLR_V = 0.15                     # vertical play of the swivel, each side
PIN_D = 1.75                     # filament
TAB_X0 = TAB_TIP - TAB_L         # -8.5, tab root
RIDGE_X1 = TAB_X0 + RIDGE_LEN    # 2.5, ridges end here
# kingpin
KP_R = 2.275                     # 4.55 shaft: 0.075 a side in the 4.7 hole along the track
HEAD_HX, HEAD_HY, HEAD_T = 3.3, KP_R, 1.2   # head 6.6 x 4.55 x 1.2, rests on the tab beyond the hole's ends
# swivel
SW_Z1 = TAB_TOP - TAB_T - CLR_V  # 25.35, plate top
SW_Z0 = SW_Z1 - 3.0              # 22.35, plate bottom
BEAR_R = 2.55                    # 5.1 bearing hole on the 4.55 shaft: holes print small on this printer
PLATE_R = 4.3                    # plate is a round end around the kingpin
LOCK_D = 2.2                     # lock hole across the kingpin, a teardrop pointing at the tip (up as printed)
KP_EXTRA = 0.4                   # kingpin 2 layers longer after the first print (Aaron, Nov 25: "1 or 2 layers taller")
LOCK_PIN_Z = SW_Z0 - CLR_V - KP_EXTRA - PIN_D / 2   # lock filament's center, 0.55 under the swivel
LOCK_Z = LOCK_PIN_Z + (LOCK_D - PIN_D) / 2 * math.sqrt(2)   # hole center, so the filament sits in the point
KP_Z0 = LOCK_Z - LOCK_D / 2 * math.sqrt(2) - 1.0  # kingpin tip, 1.0 below the hole's point
KX, KZ = 9.5, 26.5               # hinge axis; KZ is level with the pull on the cars' loops (bar bottom at 26.0)
K_R = 2.4                        # cheek and arm knuckle radius
CHEEK_HOLE = 1.15                # 2.3 holes in the cheeks (teardrops): print a little small and grip the pin,
                                 # like the 2.3 arm holes of version 1
CHEEK_T = 2.0
TONGUE_X = 13.5                  # plate runs on between the cheeks; the arm's stop lands on it
# arm
ARM_W = 4.0                      # with the chamfers, fits the engine's 6.2 opening turned about 20 degrees
ARM_CHAMFER = 1.5                # 45 degree chamfers on the front corners, seen from above
ARM_HOLE = 1.3                   # 2.6 hole (round as printed): the arm turns on the pin, like the 2.6
                                 # knuckle hole of version 1
THETA = math.radians(30)         # rake of the leg's back face
BEAM_Z0, BEAM_Z1 = LOOP_TOP, 31.0
LEG_T = 3.0                      # leg thickness at the loop's top
RAKE_Z0 = 23.0                   # rake ends 3 mm under a car loop (as in version 1)
LEG_Z0 = RAKE_Z0 - 2.0           # then 2 mm straight down (Aaron, Nov 25)
LUG_X = (KX + K_R - 0.2, KX + 4.7)
LUG_Z0 = 24.0
PHI_STOP, PHI_UP = -20.0, 45.0   # droop stop (checked; the engine's lower loop needs about -10), lift range
SWEEP_DOWN = -15.75              # stop face swept from here; the clearance adds about 4.3 degrees
SWEEP_CLR = 0.3
SIDE_CLR = 0.3                   # arm to cheeks, each side

CHEEK_Y0 = ARM_W / 2 + SIDE_CLR  # 2.6
CHEEK_Y1 = CHEEK_Y0 + CHEEK_T    # 4.6

# derived
Z_BAR0 = LOOP_TOP - LOOP_T       # 26.0
X_THROAT = X_I + LOOP_T * math.tan(THETA)
X_FRONT = X_THROAT + LEG_T
X_RAKE_END = X_I - (Z_BAR0 - RAKE_Z0) * math.tan(THETA)
X_TIP = X_I - END_BAR


# ---------------- 2D / 3D helpers ----------------
def cs(poly):
    """shapely (multi)polygon -> CrossSection."""
    loops = []
    for p in getattr(poly, "geoms", [poly]):
        p = orient(p, 1.0)
        loops.append(np.asarray(p.exterior.coords)[:-1])
        for h in p.interiors:
            loops.append(np.asarray(h.coords)[:-1])
    return CrossSection([l.tolist() for l in loops])


def extrude_y(poly, y0, y1):
    """Profile in (x, z), extruded across y0..y1."""
    return Manifold.extrude(cs(poly), y1 - y0).rotate((90, 0, 0)).translate((0, y1, 0))


def extrude_z(poly, z0, z1):
    """Outline in (x, y), extruded from z0 to z1."""
    return Manifold.extrude(cs(poly), z1 - z0).translate((0, 0, z0))


def circle(x, z, r):
    return Point(x, z).buffer(r, 128)


def rounded_rect(x0, z0, x1, z1, r):
    return box(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, 32) if r > 0 else box(x0, z0, x1, z1)


def teardrop(x, z, r, up=True):
    """Hole profile that prints without sagging: a circle with a 45 degree point toward +z (or -z)."""
    s = 1 if up else -1
    tip = (x, z + s * r * math.sqrt(2))
    a, b = (x - r / math.sqrt(2), z + s * r / math.sqrt(2)), (x + r / math.sqrt(2), z + s * r / math.sqrt(2))
    return unary_union([circle(x, z, r), Polygon([a, tip, b, (x, z)])])


def stadium(lx, ly):
    """Oblong hole lx along x by ly across, rounded on its short ends (x)."""
    r = min(lx, ly) / 2
    if ly >= lx:
        return LineString([(0, -(ly / 2 - r)), (0, ly / 2 - r)]).buffer(r, 64)
    return LineString([(-(lx / 2 - r), 0), (lx / 2 - r, 0)]).buffer(r, 64)


# ---------------- kingpin ----------------
def kingpin():
    head = extrude_z(rounded_rect(-HEAD_HX, -HEAD_HY, HEAD_HX, HEAD_HY, 0.9), TAB_TOP, TAB_TOP + HEAD_T)
    shaft = Manifold.cylinder(TAB_TOP + 0.01 - KP_Z0, KP_R, KP_R, 96).translate((0, 0, KP_Z0))
    lock = extrude_y(teardrop(0, LOCK_Z, LOCK_D / 2, up=False), -5, 5)   # prints head down: point toward the tip
    return (head + shaft) - lock


# ---------------- swivel ----------------
def swivel_outline():
    """Plate seen from above: round end on the kingpin, fork width under the cheeks, tongue between them."""
    p = unary_union([Point(0, 0).buffer(PLATE_R, 96),
                     box(0, -CHEEK_Y1, KX + K_R, CHEEK_Y1),
                     rounded_rect(KX, -CHEEK_Y0, TONGUE_X, CHEEK_Y0, 0.8)])
    return p.buffer(-0.6, 32).buffer(0.6, 32).difference(Point(0, 0).buffer(BEAR_R, 96))


def cheek_profile():
    return unary_union([circle(KX, KZ, K_R), box(KX - K_R, SW_Z0, KX + K_R, KZ)]).difference(
        teardrop(KX, KZ, CHEEK_HOLE, up=True))


def swivel_central_profile():
    """The swivel between the cheeks, in x-z: what the arm must clear."""
    plate = box(-PLATE_R, SW_Z0, TONGUE_X, SW_Z1)
    return plate.difference(circle(KX, KZ, K_R + SWEEP_CLR))


def swivel():
    plate = extrude_z(swivel_outline(), SW_Z0, SW_Z1)
    notch = extrude_y(circle(KX, KZ, K_R + SWEEP_CLR), -CHEEK_Y0, CHEEK_Y0)
    cheeks = [extrude_y(cheek_profile(), CHEEK_Y0, CHEEK_Y1), extrude_y(cheek_profile(), -CHEEK_Y1, -CHEEK_Y0)]
    return (plate - notch) + cheeks[0] + cheeks[1]


# ---------------- arm ----------------
def leg_profile():
    return Polygon([(X_THROAT, LOOP_TOP), (X_RAKE_END, RAKE_Z0), (X_RAKE_END, LEG_Z0), (X_FRONT, LEG_Z0),
                    (X_FRONT, LOOP_TOP)])


def arm_outline_raw():
    beam = box(KX, BEAM_Z0, X_FRONT, BEAM_Z1)
    lug = box(LUG_X[0], LUG_Z0, LUG_X[1], BEAM_Z0 + 0.01)
    shape = unary_union([circle(KX, KZ, K_R), beam, leg_profile(), lug])
    shape = shape.difference(Polygon([(X_FRONT - 1.0, BEAM_Z1 + 1), (X_FRONT + 1, BEAM_Z1 + 1), (X_FRONT + 1, BEAM_Z1 - 1.0)]))
    shape = shape.difference(Polygon([(X_FRONT - 0.8, LEG_Z0 - 1), (X_FRONT + 1, LEG_Z0 - 1), (X_FRONT + 1, LEG_Z0 + 0.8)]))
    shape = shape.buffer(-0.35, 32).buffer(0.35, 32)      # round convex corners
    return shape.buffer(0.3, 32).buffer(-0.3, 32)          # fillet concave corners (throat)


def sweep_swivel(phi0=SWEEP_DOWN, phi1=PHI_UP, step=0.5, clr=SWEEP_CLR):
    """Region the swivel's middle occupies in the arm's frame over the arm's travel."""
    prof = swivel_central_profile()
    shapes, a = [], phi0
    while a <= phi1 + 1e-9:
        shapes.append(affinity.rotate(prof, -a, origin=(KX, KZ)))
        a += step
    return unary_union(shapes).buffer(clr, 32)


def arm_outline():
    return arm_outline_raw().difference(sweep_swivel())


def arm():
    m = extrude_y(arm_outline().difference(circle(KX, KZ, ARM_HOLE)), -ARM_W / 2, ARM_W / 2)
    c, h = ARM_CHAMFER, ARM_W / 2
    for s in (1, -1):        # cut x + s*y beyond the chamfer line at each front corner
        tri = Polygon([(X_FRONT - c - 20, s * (h + 20)), (X_FRONT + 20, s * (h - c - 20)), (X_FRONT + 20, s * (h + 20))])
        m = m - extrude_z(tri, 10, 40)
    return m


def pin(length=2 * CHEEK_Y1):
    return Manifold.cylinder(length, PIN_D / 2, PIN_D / 2, 48, True).rotate((90, 0, 0)).translate((KX, 0, KZ))


def lock_pin(length=7.0):
    return Manifold.cylinder(length, PIN_D / 2, PIN_D / 2, 48, True).rotate((90, 0, 0)).translate((0, 0, LOCK_PIN_Z))


# ---------------- stand-ins for the cars ----------------
def tab(ridges=True):
    """Black tab at the front of a car, hole center at the origin."""
    c = TAB_TIP - TIP_R
    outline = unary_union([Point(c, 0).buffer(TIP_R, 128), box(TAB_X0, -TAB_W / 2, c, TAB_W / 2)])
    outline = outline.intersection(box(TAB_X0, -TAB_W, TAB_TIP + 1, TAB_W)).difference(stadium(HOLE_L, HOLE_W))
    m = extrude_z(outline, TAB_TOP - TAB_T, TAB_TOP)
    if ridges:
        for s in (-1, 1):
            r = box(TAB_X0, RIDGE_IN, RIDGE_X1, 6.0) if s > 0 else box(TAB_X0, -6.0, RIDGE_X1, -RIDGE_IN)
            m = m + extrude_z(r, TAB_TOP, RIDGE_TOP)
    return m


def loop(dx=0.0, dz=0.0, engine=False):
    """Loop of the car (or engine) ahead at the pull position shifted by dx, dz, with its end wall."""
    if engine:
        t, top, ol, ow, w, out = E_LOOP_T, E_LOOP_TOP, E_OPEN_L, E_OPEN_W, E_LOOP_W, E_LOOP_OUT
    else:
        t, top, ol, ow, w, out = LOOP_T, LOOP_TOP, OPEN_L, OPEN_W, LOOP_W, LOOP_OUT
    xi = X_I                                     # end-bar inner edge at the reference position
    tip = xi - END_BAR
    c = tip + w / 2
    outline = unary_union([Point(c, 0).buffer(w / 2, 128), box(c, -w / 2, tip + out, w / 2)])
    outline = outline.difference(box(xi, -ow / 2, xi + ol, ow / 2))
    m = extrude_z(outline, top - t, top)
    wall = Manifold.cube((30, 40, 40)).translate((tip + out, -20, top - 10))
    return (m + wall).translate((dx, 0, dz))


def place_arm(a, phi):
    """Arm rotated by phi degrees about the hinge (positive lifts the leg)."""
    return a.translate((-KX, 0, -KZ)).rotate((0, -phi, 0)).translate((KX, 0, KZ))


def yaw(m, psi):
    return m.rotate((0, 0, psi))


if __name__ == "__main__":
    for name, m in (("kingpin", kingpin()), ("swivel", swivel()), ("arm", arm())):
        b = m.bounding_box()
        print(f"{name}: {b[3]-b[0]:.1f} x {b[4]-b[1]:.1f} x {b[5]-b[2]:.1f} mm, {m.volume():.0f} mm3, "
              f"pieces {len(m.decompose())}, genus {m.genus()}")
    print(f"throat {X_THROAT:.2f}, leg front {X_FRONT:.2f}, rake end {X_RAKE_END:.2f}, leg bottom {LEG_Z0}, "
          f"kingpin tip {KP_Z0:.2f}, lock hole at {LOCK_Z:.2f}, lock filament at {LOCK_PIN_Z:.2f}")
