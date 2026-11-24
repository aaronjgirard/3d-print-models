## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Checks: parts are closed solids; nothing overlaps the stand-ins of the tab and loop through the arm's travel,
on curves and with the loop up or down; contacts are where they should be; the droop stop works; force balance."""
import math
import numpy as np
from shapely import affinity
import coupler as C

EPS = 1e-3          # mm3; overlaps below this count as touching


def ov(a, b):
    return (a ^ b).volume()


def loop_at(dx, dz, psi):
    """Loop turned psi deg about the middle of the leg, then moved dx along the pull and dz up."""
    cx = (C.X_I + C.X_FRONT) / 2
    l = C.loop().translate((-cx, 0, 0)).rotate((0, 0, psi)).translate((cx, 0, 0))
    return l.translate((dx, 0, dz))


def leg_bottom(phi):
    return affinity.rotate(C.leg_profile(), phi, origin=(C.KX, C.KZ)).bounds[1]


def seat(arm, dz, psi, slack=2.2):
    """Lower the arm onto the loop with slack, then pull. Returns the rest angle, the pull to contact, where the
    contact is, and whether the leg reaches below the bar there."""
    lp = loop_at(-slack, dz, psi)
    phi = None
    for p in np.arange(35, C.PHI_STOP - 0.01, -0.25):
        if ov(C.place_arm(arm, p), lp) > EPS:
            break
        phi = p
    a = C.place_arm(arm, phi)
    hit = next((d for d in np.arange(0, slack + 2.0, 0.02) if ov(a, loop_at(-slack + d, dz, psi)) > EPS), None)
    if hit is None:
        return phi, None, "none", False
    b = (a ^ loop_at(-slack + hit + 0.05, dz, psi)).bounding_box()
    zmid, xmid = (b[2] + b[5]) / 2, (b[0] + b[3]) / 2
    bar0 = C.Z_BAR0 + dz
    raked = bar0 - 0.1 <= zmid <= bar0 + C.LOOP_T + 0.1 and xmid < C.X_FRONT - 1.0
    return phi, hit, ("raked face" if raked else f"x {xmid:.1f} z {zmid:.1f}"), leg_bottom(phi) < bar0 - 0.5


def running(arm, dz, psi):
    """Coupled on the straight with the loop dz up, then the loop turns psi on a curve: the leg stays in the
    opening, the loop backs off along the pull if it has to, the arm settles on it, then the pull seats it."""
    phi, _, _, _ = seat(arm, dz, 0)
    for p in np.arange(phi + 6, C.PHI_STOP - 0.01, -0.25):     # arm may settle lower or higher on the turned loop
        a = C.place_arm(arm, p)
        free = [d for d in np.arange(-3.5, 0.01, 0.05) if ov(a, loop_at(d, dz, psi)) < EPS]
        if not free:
            break
        best = (p, min(free))
    p, d0 = best
    a = C.place_arm(arm, p)
    hit = next((d for d in np.arange(d0, d0 + 4, 0.02) if ov(a, loop_at(d, dz, psi)) > EPS), None)
    b = (a ^ loop_at(hit + 0.05, dz, psi)).bounding_box()
    zmid, xmid = (b[2] + b[5]) / 2, (b[0] + b[3]) / 2
    bar0 = C.Z_BAR0 + dz
    raked = bar0 - 0.1 <= zmid <= bar0 + C.LOOP_T + 0.1 and xmid < C.X_FRONT - 1.0
    return p, hit, raked and leg_bottom(p) < bar0 - 0.5


def main():
    sw, arm, tab = C.swivel(), C.arm(), C.tab()
    ok = True

    def report(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  ({detail})" if detail else ""))

    for name, m in (("swivel", sw), ("arm", arm)):
        report(f"{name} is one closed solid", m.num_vert() > 0 and m.volume() > 0 and len(m.decompose()) == 1,
               f"{m.volume():.0f} mm3, genus {m.genus()}")

    # snap: how far the barbs reach over the hole edge, and how hard the back finger has to bend to get them through
    ys = np.linspace(0, C.SW_T / 2, 25)
    hole = np.sqrt((C.HOLE_D / 2) ** 2 - ys ** 2)
    barb = np.sqrt(C.BARB_R ** 2 - ys ** 2)
    over = barb - hole
    bend = 2 * over.max()                                   # front prong is rigid, so the back finger takes both
    L = (C.CATCH_Z + 0.15) - C.SLOT_Z0
    t = C.PEG_R - C.SLOT_HALF
    strain = 3 * t * bend / (2 * L ** 2)
    report("snap: barbs reach over the hole edge", over.min() > 0.2, f"{over.min():.2f} to {over.max():.2f} mm")
    report("snap: back finger bends under 4 % to go in", strain < 0.04 and bend < 2 * C.SLOT_HALF - 0.3,
           f"bends {bend:.2f} mm over {L:.1f} mm, about {strain * 100:.1f} % strain, slot {2 * C.SLOT_HALF:.1f}")

    # swivel in the tab, turned on curves
    worst = max(ov(sw, C.yaw(tab, p)) for p in range(-25, 26, 5))
    report("swivel clears the tab, turned up to 25 deg", worst < EPS, f"worst overlap {worst:.4f} mm3")
    lim = next((p for p in np.arange(25, 90.1, 0.5) if ov(sw, C.yaw(tab, p)) > EPS), None)
    print(f"     swivel first touches the (assumed) ridges at {lim} deg")

    # arm against swivel over its travel, and the droop stop
    worst = max(ov(C.place_arm(arm, p), sw) for p in np.arange(C.PHI_STOP, C.PHI_UP + 0.01, 1.0))
    report("arm clears the swivel from -15 to +40 deg", worst < EPS, f"worst {worst:.4f}")
    stop = ov(C.place_arm(arm, C.PHI_STOP - 0.5), sw)
    report("droop stop: arm meets the swivel at -15 deg", stop > EPS, f"overlap {stop:.3f} mm3 at -15.5")

    # arm and swivel against the tab, any arm angle, on curves
    worst = 0
    for psi in range(-20, 21, 5):
        t = C.yaw(tab, psi)
        for p in np.arange(C.PHI_STOP, C.PHI_UP + 0.01, 5.0):
            worst = max(worst, ov(C.place_arm(arm, p), t))
    report("arm clears the tab at every angle, turned up to 20 deg", worst < EPS, f"worst {worst:.4f}")

    # coupled and pulling, nominal
    a0 = C.place_arm(arm, 0)
    report("coupled: arm clears the loop", ov(a0, C.loop()) < EPS, f"{ov(a0, C.loop()):.4f}")
    up = ov(a0, C.loop(0, 0.05))
    pull = ov(a0, C.loop(0.05, 0))
    report("coupled: underside rests on the end bar", up > 0, f"loop 0.05 up overlaps {up:.4f}")
    report("coupled: end bar seats against the raked face", pull > 0, f"loop 0.05 further overlaps {pull:.4f}")

    # pushing: free travel until the leg's front meets the far side of the opening
    travel = next((d for d in np.arange(0, 6, 0.05) if ov(a0, C.loop(-d, 0)) > EPS), None)
    report("pushing: leg travels before it meets the far side", travel and travel > 3.0, f"{travel:.2f} mm")

    # uncoupling (and coupling, the same path backwards): slack, then lift
    for slack in (1.8, 2.0, 2.5):
        worst = max(ov(C.place_arm(arm, p), C.loop(-slack, 0)) for p in np.arange(0, C.PHI_UP + 0.01, 1.0))
        report(f"uncouple: {slack} mm slack, lift to 40 deg clears", worst < EPS, f"worst {worst:.4f}")
    lift = next(p for p in np.arange(0, 40, 0.25) if leg_bottom(p) > C.LOOP_TOP + 0.3)
    print(f"     leg bottom is 0.3 over the loop once the arm is lifted {lift:.1f} deg")

    # loop higher or lower than the tab (track joints, uneven floor), and on curves (loop turned relative to the
    # arm): lower the arm onto the loop with slack, then pull until the bar meets the arm
    for dz, psi in [(-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (0, -15), (0, 15)]:
        phi, hit, where, low = seat(arm, dz, psi)
        good = hit is not None and where == "raked face" and low
        report(f"couple with loop {dz:+d} mm, turned {psi:+d} deg: arm rests at {phi:+.1f} deg, bar seats on the raked face",
               good, f"pulled {hit if hit is None else round(hit, 2)} of 2.2 slack, contact {where}")
    for dz in (-2, 0, 2):
        for psi in (-15, 15):
            p, hit, good = running(arm, dz, psi)
            report(f"running onto a curve, loop {dz:+d} mm, turned {psi:+d} deg: arm at {p:+.1f} deg, still seated", good,
                   f"seats at {hit:+.2f} mm")

    # forces on the arm when pulling, from the geometry (hinge, raked contact, underside on the bar)
    th = C.THETA
    L = C.X_I - C.KX
    hc = C.Z_BAR0 - C.KZ
    d = C.END_BAR / 2
    Ff = (L * math.sin(th) + hc * math.cos(th)) / (L - d)       # per unit normal force N at the raked face
    Hz = math.sin(th) - Ff
    print(f"     pulling with F: bar clamped with {Ff / math.cos(th):.2f} F from above; vertical force at the hinge "
          f"{Hz / math.cos(th):+.2f} F (positive pushes the front car's wheels down)")

    print("\nall checks pass" if ok else "\nSOME CHECKS FAIL")
    return ok


if __name__ == "__main__":
    main()
