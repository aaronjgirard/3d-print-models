## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Checks for version 2: parts are closed solids; the kingpin, swivel and arm clear the tab and each other through
the arm's travel and on curves; the droop stop works; coupling, pulling, pushing and uncoupling on the cars' loop
and on the engine's lower, narrower loop, with the loop up or down and turned; force balance from the geometry."""
import math
import numpy as np
from shapely import affinity
import coupler as C

EPS = 1e-3          # mm3; overlaps below this count as touching


def ov(a, b):
    return (a ^ b).volume()


# ---------------- 2D seated geometry and forces (section through the middle) ----------------
def rot(v, deg):
    a = math.radians(deg)
    return np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)])


def bar_corners(x_i, top, t):
    return [np.array(p) for p in ((x_i, top), (x_i, top - t), (x_i - C.END_BAR, top), (x_i - C.END_BAR, top - t))]


def to_arm(p, phi):
    k = np.array([C.KX, C.KZ])
    return rot(p - k, -phi) + k


def rake_s(q):
    """Signed distance of an arm-frame point into the leg past the raked face (positive inside the leg)."""
    p0 = np.array([C.X_THROAT, C.BEAM_Z0])
    return float((q - p0) @ np.array([math.cos(C.THETA), -math.sin(C.THETA)]))


def seated(top, t):
    """Arm angle and bar position once the pull has drawn the bar into the throat: one corner of the bar on the
    raked face and one on the underside. Returns phi, x_i (bar's inner edge), rake contact, underside contact."""
    def place(phi):
        lo, hi = 10.0, 30.0                        # bar inner edge: back it off until it is just behind the rake
        for _ in range(60):
            mid = (lo + hi) / 2
            s = max(rake_s(to_arm(c, phi)) for c in bar_corners(mid, top, t))
            lo, hi = (mid, hi) if s < 0 else (lo, mid)
        x_i = lo
        gap = C.BEAM_Z0 - max(to_arm(c, phi)[1] for c in bar_corners(x_i, top, t))
        return x_i, gap
    lo, hi = C.PHI_STOP, 30.0                      # lower the arm until its underside meets the bar
    for _ in range(60):
        mid = (lo + hi) / 2
        _, gap = place(mid)
        lo, hi = (lo, mid) if gap > 0 else (mid, hi)
    phi = hi
    x_i, gap = place(phi)
    cs = bar_corners(x_i, top, t)
    r = max(cs, key=lambda c: rake_s(to_arm(c, phi)))
    zs = [to_arm(c, phi)[1] for c in cs]
    tops = [c for c, z in zip(cs, zs) if z > max(zs) - 0.01]
    u = sum(tops) / len(tops)                      # flat on the bar: take the middle of the bar's top
    on_stop = gap > 0.01
    return phi, x_i, r, u, on_stop


def forces(phi, r, u):
    """Per unit pull: clamp (underside pressing on the bar) and the vertical force on the car ahead (positive
    lifts it; the car behind gets the same push down at the hinge)."""
    k = np.array([C.KX, C.KZ])
    ur = rot((math.cos(C.THETA), -math.sin(C.THETA)), phi)     # on the arm, into the raked face
    uu = rot((0.0, 1.0), phi)                                  # on the arm, up into the underside

    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    U = -cross(r - k, ur) / cross(u - k, uu)                    # per unit force on the raked face
    f = ur + U * uu
    return U / f[0], -f[1] / f[0], U


# ---------------- 3D helpers ----------------
KIND = {"car": dict(t=C.LOOP_T, top=C.LOOP_TOP, engine=False), "engine": dict(t=C.E_LOOP_T, top=C.E_LOOP_TOP, engine=True)}
BASE = {k: seated(v["top"], v["t"])[1] - C.X_I for k, v in KIND.items()}     # pulled position of each loop


def loop_at(kind, dx, dz, psi, dy=0.0):
    """Loop of the car or engine ahead, turned psi about its end bar's inner edge (relative to the coupler, a
    loop held by the pull turns about where the bar sits in the throat), moved dx along the pull from its seated
    position, dy across and dz up. dy stands in for the coupler turning a little on its kingpin to centre the
    leg in the opening (1 mm across costs about 2.6 degrees of turn, 22 mm from the kingpin)."""
    cx = C.X_I                   # loops turn about the bar's inner edge, where the pull holds them
    l = C.loop(engine=KIND[kind]["engine"]).translate((-cx, 0, 0)).rotate((0, 0, psi)).translate((cx, 0, 0))
    return l.translate((BASE[kind] + dx, dy, dz))


def leg_bottom(phi):
    return affinity.rotate(C.leg_profile(), phi, origin=(C.KX, C.KZ)).bounds[1]


def contact_ok(kind, a, lp, dz, x_inner):
    b = (a ^ lp).bounding_box()
    zmid, xmid = (b[2] + b[5]) / 2, (b[0] + b[3]) / 2
    bar0 = KIND[kind]["top"] - KIND[kind]["t"] + dz
    raked = bar0 - 0.1 <= zmid <= bar0 + KIND[kind]["t"] + 0.1 and xmid < x_inner + 0.6
    return raked, f"x {xmid:.1f} z {zmid:.1f}"


def seat(kind, arm, dz, psi, slack=2.2, dy=0.0):
    """Hold the arm up, set the loop slack behind its pulled position, let the arm fall onto it, then pull.
    Returns the rest angle, the pull to contact, where the contact is, and whether the leg reaches under the bar."""
    lp = loop_at(kind, -slack, dz, psi, dy)
    assert ov(C.place_arm(arm, C.PHI_UP), lp) < EPS, "arm does not clear the loop when lifted"
    phi = C.PHI_UP
    for p in np.arange(C.PHI_UP, C.PHI_STOP - 0.01, -0.25):
        if ov(C.place_arm(arm, p), lp) > EPS:
            break
        phi = p
    a = C.place_arm(arm, phi)
    hit = next((d for d in np.arange(0, slack + 2.0, 0.02) if ov(a, loop_at(kind, -slack + d, dz, psi, dy)) > EPS), None)
    if hit is None:
        return phi, None, "none", False
    x_inner = C.X_I + BASE[kind] - slack + hit + 2.0 * abs(math.sin(math.radians(psi)))
    good, where = contact_ok(kind, a, loop_at(kind, -slack + hit + 0.05, dz, psi, dy), dz, x_inner)
    bar0 = KIND[kind]["top"] - KIND[kind]["t"] + dz
    return phi, hit, ("raked face" if good else where), leg_bottom(phi) < bar0 - 0.5


def running(kind, arm, dz, psi):
    """Coupled on the straight with the loop dz up, then the loop turns psi on a curve: the leg stays in the
    opening, the loop backs off along the pull if it has to, the arm settles on it, then the pull seats it."""
    phi, _, _, _ = seat(kind, arm, dz, 0)
    best = None
    for p in np.arange(min(phi + 6, C.PHI_UP), C.PHI_STOP - 0.01, -0.5):
        a = C.place_arm(arm, p)
        free = [(d, dy) for dy in (0.0, -0.5, 0.5, -1.0, 1.0) for d in np.arange(-3.5, 0.01, 0.1)
                if ov(a, loop_at(kind, d, dz, psi, dy)) < EPS]
        if not free and best is not None:
            break
        if free:
            best = (p, max(free, key=lambda f: (f[0], -abs(f[1]))))
    if best is None:
        return None, None, False, None
    p, (d0, dy) = best
    a = C.place_arm(arm, p)
    hit = next((d for d in np.arange(d0, d0 + 4, 0.02) if ov(a, loop_at(kind, d, dz, psi, dy)) > EPS), None)
    x_inner = C.X_I + BASE[kind] + hit + 2.0 * abs(math.sin(math.radians(psi)))
    good, _ = contact_ok(kind, a, loop_at(kind, hit + 0.05, dz, psi, dy), dz, x_inner)
    bar0 = KIND[kind]["top"] - KIND[kind]["t"] + dz
    return p, hit, good and leg_bottom(p) < bar0 - 0.5, dy


def main():
    kp, sw, arm, tab = C.kingpin(), C.swivel(), C.arm(), C.tab()
    lock = C.lock_pin()
    ok = True

    def report(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  ({detail})" if detail else ""))

    for name, m in (("kingpin", kp), ("swivel", sw), ("arm", arm)):
        report(f"{name} is one closed solid", m.num_vert() > 0 and m.volume() > 0 and len(m.decompose()) == 1,
               f"{m.volume():.0f} mm3, genus {m.genus()}")

    # kingpin in the tab
    report("kingpin clears the tab", ov(kp, tab) < EPS, f"{ov(kp, tab):.4f}")
    report("kingpin head rests on the tab", ov(kp.translate((0, 0, -0.05)), tab) > 0,
           f"head ends reach {C.HEAD_HX - C.HOLE_L / 2:.2f} past the hole's ends")
    print(f"     shaft {2 * C.KP_R:.2f} in the {C.HOLE_L} x {C.HOLE_W} hole: {(C.HOLE_L - 2 * C.KP_R) / 2:.3f} a side "
          f"along the track, {(C.HOLE_W - 2 * C.KP_R) / 2:.3f} across")
    turn = next((p for p in np.arange(0.5, 90.1, 0.5) if ov(C.yaw(kp, p), tab) > EPS), None)
    report("kingpin head cannot spin between the ridges", turn is not None and turn < 30,
           f"touches a ridge turned {turn} deg (ridge spacing assumed {2 * C.RIDGE_IN:.1f})")

    # swivel on the kingpin, under the tab, locked by the filament
    report("swivel turns on the kingpin without touching it", max(ov(C.yaw(sw, p), kp) for p in range(-30, 31, 10)) < EPS)
    report("lock filament passes through the kingpin", ov(lock, kp) < EPS)
    report("lock filament clears the swivel", ov(lock, sw) < EPS, f"{C.SW_Z0 - (C.LOCK_PIN_Z + C.PIN_D / 2):.2f} gap")
    dn = C.CLR_V + C.KP_EXTRA
    report(f"swivel play: 0.15 up to the tab, {dn:.2f} down to the lock", ov(sw.translate((0, 0, 0.2)), tab) > 0 and
           ov(sw.translate((0, 0, -dn - 0.05)), lock) > 0 and ov(sw.translate((0, 0, 0.1)), tab) < EPS and
           ov(sw.translate((0, 0, -dn + 0.05)), lock) < EPS)
    worst = max(ov(C.yaw(sw, p), tab) for p in range(-25, 26, 5))
    report("swivel clears the tab turned up to 25 deg", worst < EPS, f"worst overlap {worst:.4f} mm3")
    for s in (1, -1):
        lim = next((p for p in np.arange(25, 90.1, 0.5) if ov(C.yaw(sw, s * p), tab) > EPS), None)
        print(f"     swivel first touches the tab or ridges turned {s * lim if lim else 'beyond 90'} deg")

    # arm against the swivel over its travel, and the droop stop
    worst = max(ov(C.place_arm(arm, p), sw) for p in np.arange(C.PHI_STOP, C.PHI_UP + 0.01, 1.0))
    report(f"arm clears the swivel from {C.PHI_STOP:.0f} to +{C.PHI_UP:.0f} deg", worst < EPS, f"worst {worst:.4f}")
    stop = ov(C.place_arm(arm, C.PHI_STOP - 0.5), sw)
    report(f"droop stop: arm meets the swivel at {C.PHI_STOP:.0f} deg", stop > EPS, f"overlap {stop:.3f} mm3 at 0.5 lower")

    # arm against the tab and kingpin, any angle, on curves
    worst = 0
    for psi in range(-25, 26, 5):
        t, k = C.yaw(tab, psi), C.yaw(kp, psi)
        for p in np.arange(C.PHI_STOP, C.PHI_UP + 0.01, 5.0):
            a = C.place_arm(arm, p)
            worst = max(worst, ov(a, t), ov(a, k))
    report("arm clears the tab and kingpin at every angle, turned up to 25 deg", worst < EPS, f"worst {worst:.4f}")
    up = next((p for p in np.arange(C.PHI_UP, 120.1, 1.0) if ov(C.place_arm(arm, p), tab + kp) > EPS), None)
    print(f"     arm can be lifted to {up - 1 if up else 'beyond 120'} deg before it touches the tab")

    # each loop: seated geometry and forces, then coupling, pushing, uncoupling
    for kind in ("car", "engine"):
        k = KIND[kind]
        name = "car's loop" if kind == "car" else "engine's loop"
        phi, x_i, r, u, on_stop = seated(k["top"], k["t"])
        clamp, vert, _ = forces(phi, r, u)
        print(f"\n--- {name}: top {k['top']}, {k['t']} thick ---")
        report(f"{name}: pulled, the arm settles at {phi:+.1f} deg, above the stop", not on_stop and phi > C.PHI_STOP + 3,
               f"bar's inner edge {x_i:.2f} past the hole")
        a0 = C.place_arm(arm, phi)
        report(f"{name}: arm clears the seated loop", ov(a0, loop_at(kind, 0, 0, 0)) < EPS,
               f"{ov(a0, loop_at(kind, 0, 0, 0)):.4f}")
        report(f"{name}: underside rests on the end bar", ov(a0, loop_at(kind, 0, 0.05, 0)) > 0)
        report(f"{name}: end bar seats against the raked face", ov(a0, loop_at(kind, 0.05, 0, 0)) > 0)
        print(f"     pulling with F: bar clamped with {clamp:.2f} F from above; vertical force on the car ahead "
              f"{vert:+.2f} F (positive lifts it), the same pushing the car behind down at the hinge")
        travel = next((d for d in np.arange(0, 8, 0.05) if ov(a0, loop_at(kind, -d, 0, 0)) > EPS), None)
        report(f"{name}: pushing, the leg travels before it meets the far side", travel and travel > 3.0,
               f"{travel:.2f} mm")
        for slack in (1.8, 2.0, 2.5):
            worst = max(ov(C.place_arm(arm, p), loop_at(kind, -slack, 0, 0)) for p in np.arange(phi, C.PHI_UP + 0.01, 1.0))
            report(f"{name}: uncouple with {slack} mm slack, lift to {C.PHI_UP:.0f} deg clears", worst < EPS,
                   f"worst {worst:.4f}")
        lift = next(p for p in np.arange(phi, C.PHI_UP, 0.25) if leg_bottom(p) > k["top"] + 0.3)
        print(f"     leg bottom is 0.3 over the loop once the arm is lifted {lift:.1f} deg")
        dzs = (-3, -2, -1, 0, 1, 2, 3) if kind == "car" else (-2, -1, 0, 1, 2, 3)
        for dz, psi in [(d, 0) for d in dzs] + [(0, -15), (0, 15)]:
            tries = [seat(kind, arm, dz, psi, dy=dy) + (dy,) for dy in ((0.0,) if psi == 0 else (0.0, -0.5, 0.5, -1.0, 1.0))]
            p, hit, where, low, dy = min(tries, key=lambda t: (not (t[1] is not None and t[2] == "raked face" and t[3]), t[0]))
            good = hit is not None and where == "raked face" and low
            report(f"{name}: couple with the loop {dz:+d} mm, turned {psi:+d} deg: arm rests at {p:+.1f} deg, "
                   f"bar seats on the raked face", good,
                   f"pulled {hit if hit is None else round(hit, 2)} of 2.2 slack, contact {where}"
                   + (f", leg {dy:+.1f} off centre" if dy else ""))
        for dz in (-1, 0, 2):
            for psi in (-15, 15, 20):
                p, hit, good, dy = running(kind, arm, dz, psi)
                report(f"{name}: running onto a curve, loop {dz:+d} mm, turned {psi:+d} deg: arm at "
                       f"{p if p is None else round(p, 1)} deg, still seated", good,
                       "no room" if p is None else f"seats at {hit:+.2f} mm" + (f", leg {dy:+.1f} off centre" if dy else ""))
        for dz in (-1.0, 1.0):
            p2, _, r2, u2, st = seated(k["top"] + dz, k["t"])
            c2, v2, _ = forces(p2, r2, u2)
            print(f"     loop {dz:+.0f} mm: arm at {p2:+.1f} deg{' (on the stop)' if st else ''}, clamp {c2:.2f} F, "
                  f"vertical {v2:+.2f} F")

    print("\nall checks pass" if ok else "\nSOME CHECKS FAIL")
    return ok


if __name__ == "__main__":
    main()
