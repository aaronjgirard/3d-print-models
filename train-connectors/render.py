## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Preview renders into out/renders: the coupler on the cars' tab and loop, the two parts, the print plate, and
side sections through the middle in four states."""
import os
import math
import numpy as np
import pyvista as pv
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import box, Polygon
from shapely import affinity
from manifold3d import Manifold
import coupler as C
import export as E

pv.OFF_SCREEN = True
OUT = "out/renders"
SWIVEL = "#2f6db5"      # printed parts: blue and violet (no red, yellow or green)
ARM = "#8a5cc2"
CAR = "#2b2b2b"         # black tab and loop
WALL = "#c9c9c9"
PIN = "#e8e8e8"


def pv_mesh(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), f]).astype(np.int64))


def render(items, path, camera, size=(1600, 1100), parallel=False, pscale=None, zoom=1.0):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for m, color in items:
        p.add_mesh(pv_mesh(m), color=color, smooth_shading=True, split_sharp_edges=True, specular=0.25, specular_power=15)
    p.enable_lightkit()
    if parallel:
        p.enable_parallel_projection()
    p.camera_position = camera
    if parallel and pscale:
        p.camera.parallel_scale = pscale
    else:
        p.camera.zoom(zoom)
    p.screenshot(path)
    p.close()


def cam(target, az, el, dist):
    a, e = math.radians(az), math.radians(el)
    eye = (target[0] + dist * math.cos(e) * math.cos(a), target[1] + dist * math.cos(e) * math.sin(a),
           target[2] + dist * math.sin(e))
    return [eye, target, (0, 0, 1)]


def pin(length):
    return Manifold.cylinder(length, C.PIN_D / 2, C.PIN_D / 2, 48, True).rotate((90, 0, 0)).translate((C.KX, 0, C.KZ))


def loop_short():
    """Loop without the big end wall, for the 3D views."""
    lp = C.loop()
    cut = Manifold.cube((60, 60, 60)).translate((C.X_TIP + C.LOOP_OUT, -30, 0))
    return lp - cut, Manifold.cube((3, 26, 14)).translate((C.X_TIP + C.LOOP_OUT, -13, C.Z_BAR0 - 4))


def views():
    sw, arm, tab = C.swivel(), C.arm(), C.tab()
    lp, wall = loop_short()
    a0 = C.place_arm(arm, 0)
    p = pin(C.ARM_W)
    scene = [(tab, CAR), (sw, SWIVEL), (a0, ARM), (p, PIN), (lp, CAR), (wall, WALL)]
    tgt = (13, 0, 26)
    render(scene, f"{OUT}/coupled_3q.png", cam(tgt, -55, 30, 62), size=(1600, 1000))
    render(scene, f"{OUT}/coupled_3q_back.png", cam(tgt, -125, 28, 62), size=(1600, 1000))
    render(scene, f"{OUT}/coupled_under.png", cam(tgt, -55, -30, 62), size=(1600, 1000))
    render(scene, f"{OUT}/coupled_side.png", cam(tgt, -90, 0, 200), parallel=True, pscale=11, size=(1800, 900))
    # lifted to couple or uncouple
    lifted = [(tab, CAR), (sw, SWIVEL), (C.place_arm(arm, 28), ARM), (C.place_arm(p, 28), PIN),
              (lp.translate((-2.0, 0, 0)), CAR), (wall.translate((-2.0, 0, 0)), WALL)]
    render(lifted, f"{OUT}/lifted_3q.png", cam(tgt, -55, 30, 62), size=(1600, 1000))
    # parts alone
    render([(sw, SWIVEL)], f"{OUT}/swivel.png", cam((6, 0, 24.5), -60, 25, 55))
    render([(arm, ARM)], f"{OUT}/arm.png", cam((17, 0, 27), -60, 25, 60))
    render([(arm, ARM)], f"{OUT}/arm_back.png", cam((17, 0, 27), -150, 20, 60))
    # print plate, top
    items = [(m, ARM if "arm" in n else SWIVEL) for n, m in E.plate()]
    bed = Manifold.cube((220, 220, 0.4)).translate((0, 0, -0.4))
    render(items + [(bed, "#e6e6e6")], f"{OUT}/plate_top.png", cam((110, 110, 0), -90, 89.9, 200), parallel=True,
           pscale=22, size=(1400, 900))


def draw(ax, geom, **kw):
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty:
            continue
        x, y = g.exterior.xy
        ax.fill(x, y, **kw)
        for h in g.interiors:
            hx, hy = h.xy
            ax.fill(hx, hy, color="white")


def sections():
    """Section through the middle (y = 0) of everything, four states."""
    fig, axs = plt.subplots(2, 2, figsize=(14, 8.2))
    states = [("Coupled and pulling: bar clamped between underside and raked face", 0, 0.0),
              ("Pushed together: leg moves 3.6 mm before it meets the far side", 0, -3.6),
              ("To uncouple: push 2 mm together, lift about 25 deg", 28, -2.0),
              ("Uncoupled: arm rests on its stop at -15 deg", -15, None)]
    peg = Polygon([(-C.PEG_R, C.BOSS_Z0), (C.PEG_R, C.BOSS_Z0), (C.PEG_R, C.CATCH_Z), (C.BARB_R, C.CATCH_Z),
                   (C.BARB_R, C.CATCH_Z + C.BARB_LAND), (C.TIP_R_TOP, C.TIP_Z), (-C.TIP_R_TOP, C.TIP_Z),
                   (-C.BARB_R, C.CATCH_Z + C.BARB_LAND), (-C.BARB_R, C.CATCH_Z), (-C.PEG_R, C.CATCH_Z)])
    sw2 = C.swivel_profile().union(peg).difference(box(-C.SLOT_HALF, C.SLOT_Z0, C.SLOT_HALF, 40))
    sw2 = sw2.difference(C.circle(C.KX, C.KZ, C.K_HOLE))
    arm_mid = C.arm_outline().difference(C.sweep_swivel()).difference(C.circle(C.KX, C.KZ, C.ARM_HOLE))
    arm_out = C.arm_outline()
    for ax, (title, phi, dx) in zip(axs.flat, states):
        tabsec = box(-14, C.TAB_TOP - C.TAB_T, C.TAB_TIP, C.TAB_TOP).difference(box(-C.HOLE_D / 2, 0, C.HOLE_D / 2, 40))
        draw(ax, tabsec, color=CAR)
        if dx is not None:
            lp = box(C.X_TIP, C.Z_BAR0, C.X_TIP + C.LOOP_OUT, C.LOOP_TOP).difference(box(C.X_I, 0, C.X_I + C.OPEN_L, 40))
            draw(ax, affinity.translate(lp, dx, 0), color=CAR)
            draw(ax, affinity.translate(box(C.X_TIP + C.LOOP_OUT, 20, C.X_TIP + C.LOOP_OUT + 4, 37), dx, 0), color=WALL)
        draw(ax, affinity.rotate(arm_out, phi, origin=(C.KX, C.KZ)), color=ARM, alpha=0.35)
        draw(ax, sw2, color=SWIVEL)
        draw(ax, affinity.rotate(arm_mid, phi, origin=(C.KX, C.KZ)), color=ARM, alpha=0.95)
        ax.add_patch(plt.Circle((C.KX, C.KZ), C.PIN_D / 2, color=PIN, ec="k", lw=0.6, zorder=5))
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal")
        ax.set_xlim(-9, 33)
        ax.set_ylim(18.5, 33.5)
        ax.grid(alpha=0.25)
        ax.set_xlabel("mm from the tab hole, along the track")
        ax.set_ylabel("mm above the table")
    axs[0, 0].annotate("tab", (-6, C.TAB_TOP - 0.7), color="white", fontsize=9, ha="center", va="center")
    axs[0, 0].annotate("loop", (C.X_I + C.OPEN_L + 1.1, C.Z_BAR0 - 1.6), color=CAR, fontsize=9, ha="center")
    axs[0, 0].annotate("swivel", (4.5, 21.2), color=SWIVEL, fontsize=9, ha="center")
    axs[0, 0].annotate("arm", (16, 32.0), color=ARM, fontsize=9, ha="center")
    axs[0, 0].annotate("filament pin", (C.KX, C.KZ), xytext=(C.KX - 7, 31.5), fontsize=8,
                       arrowprops=dict(arrowstyle="-", lw=0.6))
    fig.text(0.5, 0.005, "Section through the middle. Pale violet: the arm's outer cheeks, which straddle the swivel.",
             ha="center", fontsize=9, color="#555")
    plt.tight_layout(rect=(0, 0.02, 1, 1))
    plt.savefig(f"{OUT}/sections.png", dpi=120)
    plt.close()


def main():
    os.makedirs(OUT, exist_ok=True)
    views()
    sections()
    print("renders in", OUT)


if __name__ == "__main__":
    main()
