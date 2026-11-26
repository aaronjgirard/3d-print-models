## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""I <3 MOM planter: a 4 inch pot with arms, print-in-place hinged legs, raised front lettering, inset back
lettering, and a bottom-text region used as an OrcaSlicer modifier (toolpath-only text on the bottom layers).

Coordinates: mm, pot axis at x = y = 0, bed at z = 0, front of the pot toward -y (the viewer in Orca's front
view), +x to the viewer's right. Print orientation is the model orientation.
"""
import numpy as np
import manifold3d as m3
from manifold3d import Manifold as M, CrossSection as CS
import text2d as T

m3.set_circular_segments(96)

# ---------------- pot ----------------
H = 88.0              # height
R_TOP = 50.8          # outer radius at the rim: 4.0 in outside diameter
R_BASE = 46.5         # outer radius of the taper line at z = 0
WALL = 2.6            # wall thickness (6 perimeters)
FLOOR = 2.25          # floor: 0.25 first layer + 10 x 0.2 = 6 bottom + 5 top shell layers
FILLET = 5.0          # outer bottom round; its lowest part is a 45 degree chamfer (printable)
IN_FILLET = 3.0       # inside corner between floor and wall
SEG = 360             # facets around the pot

K = (R_TOP - R_BASE) / H                       # taper, radius per mm of height


def r_out(z):
    return R_BASE + K * z


def outer_profile():
    """(r, z) polygon of the solid pot (no cavity), counterclockwise."""
    s = np.sqrt(1 + K * K)
    rc = R_BASE + K * FILLET - FILLET * s       # fillet center radius, at z = FILLET
    a_wall = -np.arctan(K)                      # wall normal angle (slightly below horizontal)
    pts = [(0.0, 0.0)]
    rb = rc + FILLET * (np.sqrt(2) - 1)         # where the 45 degree chamfer meets the bed
    pts.append((rb, 0.0))
    for a in np.linspace(-np.pi / 4, a_wall, 24):  # arc from the 45 degree point up to the wall tangent
        pts.append((rc + FILLET * np.cos(a), FILLET + FILLET * np.sin(a)))
    pts.append((r_out(H), H))
    pts.append((0.0, H))
    return np.array(pts), rb


def cavity_profile():
    """(r, z) polygon of the inside of the pot, from the floor up past the rim."""
    zc = FLOOR + IN_FILLET
    rc = r_out(zc) - WALL - IN_FILLET
    pts = [(0.0, FLOOR)]
    for a in np.linspace(-np.pi / 2, 0, 16):
        pts.append((rc + IN_FILLET * np.cos(a), zc + IN_FILLET * np.sin(a)))
    pts.append((r_out(H + 2) - WALL, H + 2))
    pts.append((0.0, H + 2))
    return np.array(pts)


def revolve(profile):
    return M.revolve(CS([profile]), SEG)


PROFILE, R_BOTTOM = outer_profile()             # R_BOTTOM: radius of the flat bottom face

# ---------------- lettering ----------------
FRONT_FONT = T.font_path("CourierPrime-Bold.ttf")
BACK_FONT = T.font_path("Sriracha-Regular.ttf")
BOTTOM_FONT = T.font_path("CourierPrime-Bold.ttf")
CAP = 16.0            # front capital height
HEART_W = 1.35 * CAP  # heart width
ROW_GAP = 5.6         # between the bottom of "I <3" and the top of MOM
FRONT_Z = 47.0        # middle of the front block
RAISE = 1.6           # front elements stand proud of the surface
EMBED = 0.8           # and go this far into the wall
BACK_W = 72.0         # width of "Vlad & Dad"
BACK_Z = 47.0
INSET = 1.0           # back letters are cut this deep (wall left behind them: 1.6)
BOTTOM_R = 39.0       # bottom text stays inside this radius (6 walls + margin inside the bottom face)
BOTTOM_TOP = 1.25     # top of the bottom-text modifier: covers the 6 bottom layers (0.25 + 5 x 0.2)


def front_2d():
    """2D front elements in (u, v): u = arc length to the viewer's right, v = height. Returns dict."""
    I, _ = T.text_cs(FRONT_FONT, "I", cap_height=CAP)
    MOM, _ = T.text_cs(FRONT_FONT, "MOM", cap_height=CAP)
    heart = T.heart_cs(HEART_W)
    bI, bM, bH = I.bounds(), MOM.bounds(), heart.bounds()
    hh = bH[3] - bH[1]
    top_row_h = max(CAP, hh)
    total = CAP + ROW_GAP + top_row_h
    v_mom = FRONT_Z - total / 2                  # MOM baseline
    v_top_mid = v_mom + CAP + ROW_GAP + top_row_h / 2
    MOM = MOM.translate((-(bM[0] + bM[2]) / 2, v_mom))
    gap = 0.22 * CAP * 1.4
    Iw, Hw = bI[2] - bI[0], bH[2] - bH[1] if False else bH[2] - bH[0]
    left = -(Iw + gap + Hw) / 2
    I = I.translate((left - bI[0], v_top_mid - CAP / 2))
    heart = heart.translate((left + Iw + gap + Hw / 2, v_top_mid))
    return {"I": I, "heart": heart, "MOM": MOM}


def back_2d():
    l2, _ = T.text_cs(BACK_FONT, "Vlad & Dad", size_em=10)
    b = l2.bounds()
    em = 10 * BACK_W / (b[2] - b[0])
    l2, _ = T.text_cs(BACK_FONT, "Vlad & Dad", size_em=em)
    l1, _ = T.text_cs(BACK_FONT, "From", size_em=0.8 * em)
    b2, b1 = l2.bounds(), l1.bounds()
    l2 = l2.translate((-(b2[0] + b2[2]) / 2, 0))
    l1 = l1.translate((-(b1[0] + b1[2]) / 2, 0.98 * em))
    both = l1 + l2
    bb = both.bounds()
    return both.translate((0, BACK_Z - (bb[1] + bb[3]) / 2))


def bottom_2d_reading():
    """THANKSGIVING over 2026, as read from below (pot upside down, heart facing you)."""
    def block(ch1):
        l1, _ = T.text_cs(BOTTOM_FONT, "THANKSGIVING", cap_height=ch1)
        l2, _ = T.text_cs(BOTTOM_FONT, "2026", cap_height=1.6 * ch1)
        b1, b2 = l1.bounds(), l2.bounds()
        gap = 0.45 * ch1
        tot = ch1 + gap + 1.6 * ch1
        return (l1.translate((-(b1[0] + b1[2]) / 2, tot / 2 - ch1)) +
                l2.translate((-(b2[0] + b2[2]) / 2, -tot / 2)))
    best = None
    for ch in np.arange(4.0, 16.0, 0.05):
        cs = block(ch)
        pts = np.vstack(T.cs_polys(cs))
        if np.hypot(pts[:, 0], pts[:, 1]).max() <= BOTTOM_R:
            best = (ch, cs)
    return best


def wrap(cs2d, w0, w1, side, refine=0.6):
    """Put a 2D shape (u, v) on the outside of the pot as a solid between w0 and w1 (outward offsets
    from the outer surface). side=+1: front (centered on -y, u toward +x); side=-1: back (centered on +y,
    u toward -x, as read from behind)."""
    solid = cs2d.extrude(w1 - w0).translate((0, 0, w0)).refine_to_length(refine)

    def f(p):
        u, v, w = p[:, 0], p[:, 1], p[:, 2]
        R = r_out(v) + w
        phi = u / r_out(v)
        x = side * R * np.sin(phi)
        y = -side * R * np.cos(phi)
        return np.c_[x, y, v]
    return solid.warp_batch(f)


# ---------------- arms and hands ----------------
ARM_R0, ARM_R1 = 4.1, 3.5          # arm radius at the shoulder and the wrist
SHOULDER_PHI, SHOULDER_Z = np.radians(82.0), 36.0
WRIST_PHI, WRIST_RAD, WRIST_Z = np.radians(66.0), 63.0, 4.2
HAND_T = 3.6                        # hand thickness


def cyl_pt(phi, r, z, sx):
    return np.array([sx * r * np.sin(phi), -r * np.cos(phi), z])


def arm(sx):
    p0 = cyl_pt(SHOULDER_PHI, r_out(SHOULDER_Z) - 1.5, SHOULDER_Z, sx)
    p3 = cyl_pt(WRIST_PHI, WRIST_RAD, WRIST_Z, sx)
    out0 = np.array([sx * np.sin(SHOULDER_PHI), -np.cos(SHOULDER_PHI), 0.0])
    p1 = p0 + out0 * 9.0 + np.array([0, 0, -9.0])
    p2 = p3 + np.array([0, 0, 13.0]) - (p3 - p0) * np.array([1, 1, 0]) * 0.12
    t = np.linspace(0, 1, 28)[:, None]
    pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    rads = ARM_R0 + (ARM_R1 - ARM_R0) * t[:, 0]
    balls = [M.sphere(r, 40).translate(tuple(p)) for p, r in zip(pts, rads)]
    hulls = [M.batch_hull([a, b]) for a, b in zip(balls[:-1], balls[1:])]
    return M.batch_boolean(hulls, m3.OpType.Add), pts


def hand_2d():
    """Cartoon hand lying flat, pointing along +x, palm centered at the origin."""
    palm = CS.circle(6.2, 64).scale((1.0, 0.92))
    parts = [palm]
    for ang, ln in ((-38, 7.0), (-13, 8.4), (13, 8.4), (38, 7.0)):
        a = np.radians(ang)
        d = np.array([np.cos(a), np.sin(a)])
        p0, p1 = d * 3.0, d * (5.2 + ln)
        seg = CS.batch_hull([CS.circle(1.75, 32).translate(tuple(p0)), CS.circle(1.6, 32).translate(tuple(p1))])
        parts.append(seg)
    a = np.radians(92)                                   # thumb
    d = np.array([np.cos(a), np.sin(a)])
    parts.append(CS.batch_hull([CS.circle(1.9, 32).translate(tuple(d * 3.0)),
                                CS.circle(1.75, 32).translate(tuple(d * 9.5 + np.array([1.6, 0])))]))
    return CS.batch_boolean(parts, m3.OpType.Add)


def rounded_slab(cs, t, r=1.2, steps=5):
    """Extrude cs to thickness t with its top edge rounded by about r (stacked insets)."""
    out = [cs.extrude(t - r)]
    for i in range(1, steps + 1):
        z0 = t - r + r * (i - 1) / steps
        z1 = t - r + r * i / steps
        inset = r - np.sqrt(max(r * r - (r * i / steps) ** 2, 0))
        c = cs.offset(-inset, m3.JoinType.Round)
        if not c.is_empty():
            out.append(c.extrude(z1 - z0 + 0.01).translate((0, 0, z0)))
    return M.batch_boolean(out, m3.OpType.Add)


def hand(sx, arm_pts):
    wrist = arm_pts[-1]
    tang = arm_pts[-1] - arm_pts[-6]
    d = np.array([tang[0], tang[1]])
    d /= np.linalg.norm(d)
    ang = np.degrees(np.arctan2(d[1], d[0]))
    cs = hand_2d()                                       # a right hand seen from above, palm down
    if sx > 0:                                           # the pot faces -y, so its right hand is at -x;
        cs = cs.mirror((0, 1))                           # mirror for the left hand at +x (thumbs point inward)
    cs = cs.rotate(ang).translate((wrist[0] + d[0] * 3.5, wrist[1] + d[1] * 3.5))
    return rounded_slab(cs, HAND_T, 1.3)


# ---------------- legs (print-in-place hinges) ----------------
LEG_X = 19.0          # leg centers at x = +-LEG_X
LEG_W = 13.0          # width
LEG_H = 9.0           # height (hinge axes at half height)
ZA = LEG_H / 2
RK = 4.5              # knuckle radius
GR = 0.55             # radial clearance around knuckles
RC = RK + GR
MID = 2.5             # middle knuckle half width
GAP = 0.45            # lateral gap between knuckles
OUT0 = MID + GAP      # outer knuckles start here
PITCH = 14.0          # hinge spacing along the leg
CONE_R, CONE_H = 2.2, 1.5          # pin cones on the outer knuckles (45 degrees)
CONE_CLR, CONE_TIP_CLR = 0.40, 0.45
FOOT_T, FOOT_W, FOOT_H = 6.0, 18.0, 20.0
LINK3_LEN = 9.0       # from the last hinge to the back of the foot
HIP_BACK = 9.0        # hip bracket reaches this far behind the hip axis (into the pot wall)


def hip_axis_y():
    return -(R_BOTTOM + GR + RK + 0.6)    # hanging links clear a shelf edge at the pot's front


def _poly(pts):
    return CS([np.array(pts, float)])


def child_clear(A):
    """2D (s, z) region a child's outer bands must stay out of around axis s = A."""
    t = (A + RC * np.cos(np.pi / 4), ZA + RC * np.sin(np.pi / 4))
    top = LEG_H + 1
    roof = _poly([(A, ZA), t, (t[0] - (top - t[1]), top), (A - 1, top)])
    v = _poly([(A - 30, -1), (A + ZA + 1, -1), (A, ZA), (A - 30, ZA)])   # V notch half (45 deg) + behind
    behind = _poly([(A - 30, -1), (A, -1), (A, top), (A - 30, top)])
    return CS.circle(RC, 96).translate((A, ZA)) + roof + v + behind


def parent_clear(B):
    t = (B - RC * np.cos(np.pi / 4), ZA + RC * np.sin(np.pi / 4))
    top = LEG_H + 1
    roof = _poly([(B, ZA), (B + 1, top), (t[0] + (top - t[1]), top), t])
    v = _poly([(B - ZA - 1, -1), (B + 30, -1), (B + 30, ZA), (B, ZA)])
    ahead = _poly([(B, -1), (B + 30, -1), (B + 30, top), (B, top)])
    return CS.circle(RC, 96).translate((B, ZA)) + roof + v + ahead


def v_child(A):
    return _poly([(A - 30, -1), (A + ZA + 1, -1), (A, ZA), (A - 30, ZA)])


def v_parent(B):
    return _poly([(B - ZA - 1, -1), (B + 30, -1), (B + 30, ZA), (B, ZA)])


def knuckle(A):
    return CS.circle(RK, 96).translate((A, ZA))


def band(profile, a0, a1):
    """Extrude an (s, z) profile across a in [a0, a1] and map (s, z, a) -> local (a, s, z)."""
    solid = profile.extrude(a1 - a0).translate((0, 0, a0))
    return solid.transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def bands(mid, gap, outer):
    hw = LEG_W / 2
    parts = []
    if mid is not None:
        parts.append(band(mid, -MID, MID))
    if gap is not None:
        parts += [band(gap, MID, OUT0), band(gap, -OUT0, -MID)]
    if outer is not None:
        parts += [band(outer, OUT0, hw), band(outer, -hw, -OUT0)]
    return M.batch_boolean([p for p in parts if not p.is_empty()], m3.OpType.Add)


def cone_x(x_base, x_tip, r_base, r_tip, s0):
    """Truncated cone along local a (x), axis at (s = s0, z = ZA)."""
    h = abs(x_tip - x_base)
    c = M.cylinder(h, r_base, r_tip, 64)                 # along +z from 0 to h
    if x_tip > x_base:      # point toward +a
        c = c.rotate((0, 90, 0)).translate((x_base, s0, ZA))
    else:
        c = c.rotate((0, -90, 0)).translate((x_base, s0, ZA))
    return c


def pins(B):
    tip_r = CONE_R - CONE_H
    return (cone_x(OUT0, OUT0 - CONE_H, CONE_R, tip_r, B) +
            cone_x(-OUT0, -OUT0 + CONE_H, CONE_R, tip_r, B))


def sockets(A):
    d = CONE_CLR * np.sqrt(2)                           # radial offset of a 45 degree cone at normal clearance
    floor = OUT0 - CONE_H - CONE_TIP_CLR                 # socket floor |a|
    r_face = CONE_R - (OUT0 - MID) + d + 0.05            # socket radius at the knuckle face (|a| = MID), a bit past
    r_floor = CONE_R - (OUT0 - floor) + d
    over = 0.3                                           # run past the face so the cut is clean
    return (cone_x(MID + over, floor, r_face + over, r_floor, A) +
            cone_x(-MID - over, -floor, r_face + over, r_floor, A))


def body_rect(s0, s1):
    return _poly([(s0, 0), (s1, 0), (s1, LEG_H), (s0, LEG_H)])


def link(A, B):
    """Link with a middle knuckle at A (child of the previous part) and outer knuckles at B."""
    body = body_rect(A, B)
    mid = knuckle(A) + (body - v_child(A) - parent_clear(B))
    gap = body - child_clear(A) - parent_clear(B)
    outer = (body - child_clear(A) - v_parent(B)) + knuckle(B)
    return bands(mid, gap, outer) + pins(B) - sockets(A)


def last_link(A):
    s1 = A + LINK3_LEN
    body = body_rect(A, s1 + 0.5)
    mid = knuckle(A) + (body - v_child(A))
    rest = body - child_clear(A)
    part = bands(mid, rest, rest) - sockets(A)
    foot = CS.circle(FOOT_W / 2, 96).translate((0, FOOT_H - FOOT_W / 2)) + \
        _poly([(-FOOT_W / 2, 0), (FOOT_W / 2, 0), (FOOT_W / 2, FOOT_H - FOOT_W / 2), (-FOOT_W / 2, FOOT_H - FOOT_W / 2)])
    foot3 = rounded_slab(foot, FOOT_T, 1.5).rotate((90, 0, 0)).translate((0, s1 + FOOT_T, 0))
    # rotate(+90 about x): thickness (+z) -> -s, height (+y) -> +z; shifted to span s1 .. s1 + FOOT_T
    return part + foot3


def hip_bracket():
    B = 0.0
    body = body_rect(-HIP_BACK, B)
    mid = body - parent_clear(B)
    outer = (body - v_parent(B)) + knuckle(B)
    return bands(mid, mid, outer) + pins(B)


def to_global(local, x_leg):
    """Local (a, s, z) with s pointing away from the pot -> global; s runs toward -y."""
    yh = hip_axis_y()
    return local.rotate((0, 0, 180)).translate((x_leg, yh, 0))


def leg_parts():
    parts = []
    for xl in (-LEG_X, LEG_X):
        parts.append(to_global(link(0.0, PITCH), xl))
        parts.append(to_global(link(PITCH, 2 * PITCH), xl))
        parts.append(to_global(last_link(2 * PITCH), xl))
    return parts


def hips():
    return [to_global(hip_bracket(), xl) for xl in (-LEG_X, LEG_X)]


# ---------------- assembly ----------------
def build():
    outer = revolve(PROFILE)
    cavity = revolve(cavity_profile())
    f = front_2d()
    front = {k: wrap(v, -EMBED, RAISE, +1) for k, v in f.items()}
    back = wrap(back_2d(), -INSET, 1.0, -1)
    arms = []
    for sx in (-1, 1):
        a, pts = arm(sx)
        arms += [a, hand(sx, pts)]
    body = M.batch_boolean([outer] + list(front.values()) + arms + hips(), m3.OpType.Add)
    body = body - cavity - back
    legs = leg_parts()
    ch, btxt = bottom_2d_reading()
    # mirror so it reads from below, then turn 180 degrees: it reads right with the pot upside down and
    # the heart facing you (THANKSGIVING on the back half of the bottom)
    btxt_model = btxt.mirror((0, 1)).rotate(180)        # (x, y) -> (-x, y)
    modifier = btxt_model.extrude(BOTTOM_TOP)
    return {"body": body, "legs": legs, "modifier": modifier, "front": front, "bottom_cap": ch,
            "bottom_2d": btxt}


if __name__ == "__main__":
    import time
    t0 = time.time()
    d = build()
    b = d["body"]
    print("body", b.status(), "genus", b.genus(), "vol cm3 %.1f" % (b.volume() / 1000), "bbox", np.round(b.bounding_box(), 2))
    for i, p in enumerate(d["legs"]):
        print("leg part", i, p.status(), "genus", p.genus(), "vol %.2f" % (p.volume() / 1000), np.round(p.bounding_box(), 2))
    print("bottom text cap %.2f" % d["bottom_cap"], "modifier bbox", np.round(d["modifier"].bounding_box(), 2))
    print("R_BOTTOM %.2f, hip axis y %.2f" % (R_BOTTOM, hip_axis_y()))
    print("%.1f s" % (time.time() - t0))
