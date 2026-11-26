## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Checks for the tender's clip-on loop (tender_loop.py) against a stand-in of the tender's back beam, and the
coupler (on the car behind) working in the new loop."""
import numpy as np
import coupler as C
import tender_loop as T
from check import ov, EPS


def to_coupler(m):
    """Tender frame (u out from the tender's beam face) -> coupler frame (x toward the car ahead, the tender)."""
    return m.mirror((1, 0, 0)).translate((C.X_I + T.ROOT + T.OPEN_L, 0, 0))


def main():
    ok = True

    def report(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  ({detail})" if detail else ""))

    clip, beam, pins = T.clip(), T.beam(), T.lock_pins()
    fitted = T.clip(with_support=False)
    report("clip is one closed solid", len(clip.decompose()) == 1 and clip.volume() > 0, f"{clip.volume():.0f} mm3")
    report("clip fits over the beam (stub cut off)", ov(fitted, beam) < EPS)
    report("clip does not fit until the stub is cut off", ov(fitted, T.beam(stub=True)) > 1)
    report("clip rests on the top of the beam", ov(fitted.translate((0, 0, -0.05)), beam) > 0)
    report("pegs fill the windows along the beam (0.2 each end)", ov(fitted.translate((0, 0.25, 0)), beam) > 0)
    pull = next(d for d in np.arange(0, 2, 0.05) if ov(fitted.translate((d, 0, 0)), beam) > EPS)
    report("pulled, the pegs bear on the inside of the beam's outer wall", 0.3 < pull < 1.0, f"after {pull:.2f} mm")
    report("lock filaments pass through the pegs and clear the beam", ov(pins, fitted) < EPS and ov(pins, beam) < EPS)
    lift = next(d for d in np.arange(0, 2, 0.05) if ov(pins.translate((0, 0, d)), beam) > EPS)
    report("lifted, the lock filaments catch under the top of the beam", lift < 0.8, f"after {lift:.2f} mm")
    lo, hi = T.WALL_T, T.WALL_T
    for w in np.arange(T.WALL_T, 0.0, -0.05):
        T.WALL_T, T.WIN_U0, T.WIN_U1 = w, -w - T.WIN_W, -w
        if ov(fitted, T.beam()) > EPS:
            break
        lo = w
    for w in np.arange(1.0, 3.0, 0.05):
        T.WALL_T, T.WIN_U0, T.WIN_U1 = w, -w - T.WIN_W, -w
        if ov(fitted, T.beam()) > EPS:
            break
        hi = w
    T.WALL_T, T.WIN_U0, T.WIN_U1 = 1.0, -1.0 - T.WIN_W, -1.0
    print(f"     fits if the beam's outer wall (window to face) is {lo:.2f} to {hi:.2f} thick; read as 1.0 off photo 08")

    # the coupler of the car behind, in the new loop
    end = to_coupler(fitted + beam + pins)
    arm = C.arm()
    a0 = C.place_arm(arm, 0.0)
    report("coupler: seated arm clears the new loop and the beam", ov(a0, end) < EPS)
    report("coupler: underside rests on the end bar", ov(a0, end.translate((0, 0, 0.05))) > 0)
    report("coupler: end bar seats against the raked face", ov(a0, end.translate((0.05, 0, 0))) > 0)
    travel = next(d for d in np.arange(0, 8, 0.05) if ov(a0, end.translate((-d, 0, 0))) > EPS)
    report("coupler: pushing travel as on the cars' loops", abs(travel - 3.65) < 0.1, f"{travel:.2f} mm")
    worst = max(ov(C.place_arm(arm, p), end.translate((-2.0, 0, 0))) for p in np.arange(0, C.PHI_UP + 0.01, 1.0))
    report("coupler: uncouples with 2 mm slack, lifting to 45 deg", worst < EPS)
    report("coupler: swivel, kingpin and tab clear the tender", ov(end, C.swivel() + C.kingpin() + C.tab()) < EPS)
    for psi in (-15, 15):
        e = end.translate((-C.X_I, 0, 0)).rotate((0, 0, psi)).translate((C.X_I, 0, 0))
        free = [d for d in np.arange(-3.0, 0.01, 0.1) for dy in (0, -0.5, 0.5, -1, 1) if ov(a0, e.translate((d, dy, 0))) < EPS]
        report(f"coupler: on a curve (loop turned {psi:+d} deg) the leg still fits the opening", bool(free),
               f"loop backed off {max(free):.1f} mm" if free else "")
    print("\nall checks pass" if ok else "\nSOME CHECKS FAIL")
    return ok


if __name__ == "__main__":
    main()
