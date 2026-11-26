## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Checks: closed solids, hinge clearances at rest, and each leg hinge swept from 60 degrees up to 90 down."""
import numpy as np
import manifold3d as m3
from manifold3d import Manifold as M
import planter as P


def rot_about_x_axis(part, y0, z0, deg):
    return part.translate((0, -y0, -z0)).rotate((deg, 0, 0)).translate((0, y0, z0))


def main():
    d = P.build()
    body, legs = d["body"], d["legs"]
    print("body status", body.status(), "components", len(body.decompose()))
    for i, p in enumerate(legs):
        print(f"leg part {i}: status {p.status()}, components {len(p.decompose())}, bbox z {np.round(p.bounding_box()[2::3], 2)}")
    yh = P.hip_axis_y()
    # rest clearances
    parts = [("body", body)] + [(f"leg{i}", p) for i, p in enumerate(legs)]
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            g = parts[i][1].min_gap(parts[j][1], 3.0)
            if g < 3.0:
                print(f"rest gap {parts[i][0]} - {parts[j][0]}: {g:.3f}")
    # sweep: for each leg, rotate child chains about each hinge (downward = far end down)
    for side, base in ((-1, 0), (1, 3)):
        l1, l2, l3 = legs[base], legs[base + 1], legs[base + 2]
        hinges = [(yh, body, [l1, l2, l3]), (yh - P.PITCH, l1, [l2, l3]), (yh - 2 * P.PITCH, l2, [l3])]
        for hi, (ya, parent, chain) in enumerate(hinges):
            worst = 9.0
            for deg in list(range(-60, 0, 10)) + list(range(0, 91, 5)):
                # leg points toward -y; "down" means the far end (more negative y) goes down:
                # rotation about +x by -deg sends (y<0 relative) downward for deg>0
                moved = [rot_about_x_axis(c, ya, P.ZA, deg) for c in chain]
                g = min(parent.min_gap(c, 2.0) for c in moved)
                if deg in (-60, -30, 0, 45, 85, 90) or g < 0.3:
                    inter = sum((parent ^ c).volume() for c in moved)
                    print(f"  leg {side:+d} hinge {hi} at {deg:+4d} deg: min gap {g:.3f}, overlap {inter:.3f} mm3")
                worst = min(worst, g)
    print("done")


if __name__ == "__main__":
    main()
