## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Clip-on replacement for the tender's broken loop (Nov 25 2026).

The tender's back end is a beam between two buffers. Its own loop (identical to the cars' loops) broke off,
leaving a stub. Behind the beam's outer face, in the top of the beam, are two small rectangular windows,
one next to each buffer. This part sits over the beam: a plate down the beam's face (where the stub is cut
off) carries a new loop, two arms reach back over the top of the beam, and a peg from each arm drops
through a window. A piece of filament through each peg, under the beam's top, keeps it from lifting off.
The pull is taken by the pegs bearing on the inside of the beam's outer wall.

Coordinates (tender frame): u along the track away from the tender (the way the loop sticks out), from
the beam's outer face; v across; z up from the table with the tender on the track. mm.
"""
import math
import numpy as np
from manifold3d import Manifold
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import coupler as C

# ---------------- measured (Aaron, Nov 25 2026) ----------------
WIN_L = 5.0                     # windows along the beam (v)
WIN_W = 2.3                     # windows across the beam (u); "approximate, hard to get into"
WIN_PITCH = 29.5                # window middle to middle
DECK_T = 3.5                    # windows go through about this much ("roughly")
STUB_DROP = 3.5                 # top of the broken stub below the top of the beam
BEAM_H = 8.0                    # beam's face, top to bottom
STUB_OUT = 2.5                  # stub sticks out about this far now (it gets cut off)
LOOP_TOP = C.LOOP_TOP           # the stub is "the same as" the cars' loops: top 27.5, 1.5 thick, 16 wide,
LOOP_T = C.LOOP_T               # 7.5 x 10 opening, 12 out from the end wall
LOOP_W, LOOP_OUT = C.LOOP_W, C.LOOP_OUT
OPEN_L, OPEN_W = C.OPEN_L, C.OPEN_W

# ---------------- read off photo 08 (about 14.75 px/mm there, from the 29.5 window pitch) ----------------
WALL_T = 1.0                    # beam's outer wall between the windows and the face (the peg fits 0.6 to 1.6)
BUF_V, BUF_SHAFT_R, BUF_HEAD_R = 19.9, 1.35, 3.05   # buffers: middle across, shaft and head radius
BUF_HEAD_U = 3.7                # buffer head's back face out from the beam's face
ROOT = LOOP_OUT - OPEN_L - C.END_BAR   # 2.25, loop's root before the opening (as on the cars)

# derived
BEAM_TOP = LOOP_TOP + STUB_DROP  # 31.0
DECK_Z0 = BEAM_TOP - DECK_T      # 27.5, underside of the beam's top
WIN_U0, WIN_U1 = -WALL_T - WIN_W, -WALL_T
WIN_V = WIN_PITCH / 2

# ---------------- design ----------------
PLATE_T = 2.0                   # plate down the beam's face (u 0 to 2)
PLATE_V = 16.5                  # plate half width; buffer shafts start about 18.5 out
TOP_T = 2.0                     # arms over the top of the beam
ARM_U0 = -4.3                   # arms reach back past the windows onto the beam's top
PEG_U0, PEG_U1 = -2.9, -1.6     # peg across the beam: 1.3 thick, 0.6 off the outer wall's inside
PEG_CLR = 0.2                   # each end of the window along the beam
LOCK_D = 2.1                    # lock hole across the peg (along u), teardrop pointing up as printed
LOCK_PIN_TOP = DECK_Z0 - 0.5    # lock filament's top: 0.5 under the beam's top plate, so a 4 mm deck still fits
Z0 = 24.0                       # bottom of the plate and pegs (the print bed)
CORNER_R = 4.0                  # loop's far corners
OPEN_R = 1.5                    # opening's corners
SUPPORT_U = (10.4, 11.2)        # snap-off wall under the loop's far end, so the loop prints as a bridge
SUPPORT_RAIL_V = (6.1, 6.9)     # snap-off walls under the side rails, so no rail spans 8 mm of air
SUPPORT_RAIL_U0 = 3.7          # they start just past the lower gussets

LOOP_Z0 = LOOP_TOP - LOOP_T
LOCK_PIN_Z = LOCK_PIN_TOP - C.PIN_D / 2
LOCK_Z = LOCK_PIN_Z + (LOCK_D - C.PIN_D) / 2      # hole center: the filament rests on the hole's bottom


def loop_outline():
    """Loop seen from above (u, v): from the plate's face to 12 out, far corners rounded, with the opening."""
    body = unary_union([box(PLATE_T - 0.01, -LOOP_W / 2, LOOP_OUT - CORNER_R, LOOP_W / 2),
                        C.rounded_rect(PLATE_T, -LOOP_W / 2, LOOP_OUT, LOOP_W / 2, CORNER_R)
                        .intersection(box(LOOP_OUT - CORNER_R - 0.01, -LOOP_W, LOOP_OUT + 1, LOOP_W))])
    opening = C.rounded_rect(ROOT, -OPEN_W / 2, ROOT + OPEN_L, OPEN_W / 2, OPEN_R)
    return body.difference(opening)


def gussets():
    """45 degree fillets where the loop's side rails meet the plate, above and below, outside the opening."""
    g = []
    for s in (1, -1):
        v0, v1 = (OPEN_W / 2 + 0.3, LOOP_W / 2 - 0.3) if s > 0 else (-LOOP_W / 2 + 0.3, -OPEN_W / 2 - 0.3)
        up = Polygon([(PLATE_T - 0.01, LOOP_TOP - 0.01), (PLATE_T + 1.2, LOOP_TOP - 0.01), (PLATE_T - 0.01, LOOP_TOP + 1.2)])
        dn = Polygon([(PLATE_T - 0.01, LOOP_Z0 + 0.01), (PLATE_T + 1.5, LOOP_Z0 + 0.01), (PLATE_T - 0.01, LOOP_Z0 - 1.5)])
        g += [C.extrude_y(up, v0, v1), C.extrude_y(dn, v0, v1)]
    return g


def clip(with_support=True):
    plate = C.extrude_z(C.rounded_rect(0, -PLATE_V, PLATE_T, PLATE_V, 0.6), Z0, BEAM_TOP + TOP_T)
    m = plate + C.extrude_z(loop_outline(), LOOP_Z0, LOOP_TOP)
    for g in gussets():
        m = m + g
    for s in (1, -1):
        c = s * WIN_V
        v0, v1 = c - WIN_L / 2 + PEG_CLR, c + WIN_L / 2 - PEG_CLR
        arm = C.extrude_z(C.rounded_rect(ARM_U0, v0, PLATE_T, v1, 0.6), BEAM_TOP, BEAM_TOP + TOP_T)
        peg = C.extrude_z(box(PEG_U0, v0, PEG_U1, v1), Z0, BEAM_TOP + 0.5)   # tip stays square: it is on the bed
        hole = C.teardrop(0, LOCK_Z, LOCK_D / 2, up=True)        # profile in (v, z), hole along u
        hole_m = Manifold.extrude(C.cs(hole), 10).rotate((90, 0, 90)).translate((PEG_U0 - 5, c, 0))
        m = m + arm + (peg - hole_m)
    if with_support:
        m = m + C.extrude_z(box(SUPPORT_U[0], -SUPPORT_RAIL_V[1], SUPPORT_U[1], SUPPORT_RAIL_V[1]), Z0, LOOP_Z0 + 0.01)
        for s in (1, -1):
            rail = box(SUPPORT_RAIL_U0, s * SUPPORT_RAIL_V[0], SUPPORT_U[0] + 0.01, s * SUPPORT_RAIL_V[1])
            m = m + C.extrude_z(rail, Z0, LOOP_Z0 + 0.01)
    return m


def lock_pins(length=6.0):
    """Lock filaments as fitted: pushed in from inside the tender until they stop at the outer wall."""
    pins = []
    for s in (1, -1):
        p = Manifold.cylinder(length, C.PIN_D / 2, C.PIN_D / 2, 48).rotate((0, -90, 0))   # along -u
        pins.append(p.translate((-WALL_T, s * WIN_V, LOCK_PIN_Z)))
    return pins[0] + pins[1]


# ---------------- stand-in of the tender's back end ----------------
def beam(stub=False):
    face = C.extrude_z(box(-WALL_T, -24, 0, 24), BEAM_TOP - BEAM_H, BEAM_TOP)
    deck = C.extrude_z(box(-5.4, -24, -WALL_T + 0.01, 24), DECK_Z0, BEAM_TOP)
    for s in (1, -1):
        deck = deck - C.extrude_z(box(WIN_U0, s * WIN_V - WIN_L / 2, WIN_U1 + 0.02, s * WIN_V + WIN_L / 2), DECK_Z0 - 1, BEAM_TOP + 1)
    m = face + deck
    for s in (1, -1):
        shaft = Manifold.cylinder(BUF_HEAD_U + 0.01, BUF_SHAFT_R, BUF_SHAFT_R, 48).rotate((0, 90, 0))
        head = Manifold.cylinder(1.7, BUF_HEAD_R, BUF_HEAD_R, 64).rotate((0, 90, 0)).translate((BUF_HEAD_U, 0, 0))
        m = m + (shaft + head).translate((0, s * BUF_V, BEAM_TOP - BEAM_H / 2))
    if stub:
        m = m + C.extrude_z(box(0, -LOOP_W / 2, STUB_OUT, LOOP_W / 2), LOOP_Z0, LOOP_TOP)
    return m


def print_part():
    """In print orientation: as fitted, plate and pegs on the bed."""
    m = clip()
    b = m.bounding_box()
    return m.translate((-b[0], -b[1], -b[2]))


if __name__ == "__main__":
    m = clip()
    b = m.bounding_box()
    print(f"tender loop: {b[3]-b[0]:.1f} x {b[4]-b[1]:.1f} x {b[5]-b[2]:.1f} mm, {m.volume():.0f} mm3, "
          f"pieces {len(m.decompose())}, genus {m.genus()}")
    print(f"beam top {BEAM_TOP}, deck underside {DECK_Z0}, loop {LOOP_Z0}-{LOOP_TOP}, lock hole at {LOCK_Z:.2f}, "
          f"filament top {LOCK_PIN_TOP:.2f}")
