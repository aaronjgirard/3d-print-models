## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Painted-look previews: front three-quarter, back, side with a leg hanging over a shelf edge."""
import os
import numpy as np
import pyvista as pv
import manifold3d as m3
from manifold3d import Manifold as M
import planter as P

pv.OFF_SCREEN = True
BLUE, BLACK, RED, WHITE = "#3f7fd0", "#1b1b1b", "#d42a2a", "#f4f4f4"


def pvm(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return pv.PolyData(v, np.c_[np.full(len(f), 3), f].ravel())


def paint_layers(d):
    f2 = P.front_2d()
    front = {k: P.wrap(v.offset(0.03, m3.JoinType.Round), 0.0, P.RAISE + 0.03, +1) for k, v in f2.items()}
    back = P.wrap(P.back_2d().offset(-0.03, m3.JoinType.Round), -P.INSET, -P.INSET + 0.08, -1)
    return front, back


def scene(d, legs_override=None, size=(1400, 1100)):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    pl.add_mesh(pvm(d["body"]), color=BLUE, smooth_shading=False, specular=0.25)
    for p in (legs_override or d["legs"]):
        pl.add_mesh(pvm(p), color=BLUE, specular=0.25)
    front, back = paint_layers(d)
    pl.add_mesh(pvm(front["I"]), color=BLACK)
    pl.add_mesh(pvm(front["MOM"]), color=BLACK)
    pl.add_mesh(pvm(front["heart"]), color=RED)
    pl.add_mesh(pvm(back), color=WHITE)
    pl.enable_lightkit()
    return pl


def main(out="out/renders"):
    os.makedirs(out, exist_ok=True)
    d = P.build()
    pl = scene(d)
    pl.camera_position = [(95, -330, 150), (0, -20, 38), (0, 0, 1)]
    pl.screenshot(f"{out}/front.png")
    pl = scene(d)
    pl.camera_position = [(-60, 330, 120), (0, 0, 45), (0, 0, 1)]
    pl.screenshot(f"{out}/back.png")
    # on a shelf edge: hip hinges at 90 degrees down
    yh = P.hip_axis_y()
    hung = [p.translate((0, -yh, -P.ZA)).rotate((90, 0, 0)).translate((0, yh, P.ZA)) for p in d["legs"]]
    pl = scene(d, hung)
    shelf = pv.Box(bounds=(-110, 110, -P.R_BOTTOM, 120, -14, 0))
    pl.add_mesh(shelf, color="#c8a77a")
    pl.camera_position = [(330, -260, 90), (0, -30, 20), (0, 0, 1)]
    pl.screenshot(f"{out}/shelf.png")
    print("renders in", out)


if __name__ == "__main__":
    main()
