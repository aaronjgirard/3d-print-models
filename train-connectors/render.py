## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Preview renders into out/renders: the coupler on a car's tab coupled to a car's loop and to the engine's loop,
an exploded view in assembly order, the three parts, the black PLA plate, side sections through the middle in
four states, and the tender's clip-on loop on its beam (3D views and two sections)."""
import os
import math
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import box
from shapely import affinity
from manifold3d import Manifold
import coupler as C
import export as E
import check as K

pv.OFF_SCREEN = True
OUT = "out/renders"
SWIVEL = "#2f6db5"      # printed parts: blue, violet, sky blue (no red, yellow or green)
ARM = "#8a5cc2"
KINGPIN = "#58a6d6"
CAR = "#2b2b2b"         # black tab and loops
WALL = "#c9c9c9"
PIN = "#e8e8e8"         # filament
CLIP = "#a7b4c2"        # tender's loop: light blue-grey, to stand out from the black beam (it prints in black PLA)


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


def loop_short(kind, dx=0.0):
    """Seated loop without the big end wall, plus a small piece of end wall, for the 3D views."""
    lp = K.loop_at(kind, dx, 0, 0)
    eng = kind == "engine"
    end = C.X_I + K.BASE[kind] + dx - C.END_BAR + (C.E_LOOP_OUT if eng else C.LOOP_OUT)
    top, t = K.KIND[kind]["top"], K.KIND[kind]["t"]
    cut = Manifold.cube((60, 60, 60)).translate((end, -30, 0))
    return lp - cut, Manifold.cube((3, 26, 14)).translate((end, -13, top - t - 4))


def coupler_at(phi, psi=0.0):
    a = C.place_arm(C.arm(), phi)
    hp = C.place_arm(C.pin(), phi)
    return [(C.yaw(C.swivel(), psi), SWIVEL), (C.yaw(a, psi), ARM), (C.yaw(hp, psi), PIN),
            (C.yaw(C.kingpin(), psi), KINGPIN), (C.yaw(C.lock_pin(), psi), PIN)]


def views():
    tab = C.tab()
    phi_e = K.seated(C.E_LOOP_TOP, C.E_LOOP_T)[0]
    tgt = (12, 0, 25.5)
    for kind, phi, tag in (("car", 0.0, "car"), ("engine", phi_e, "engine")):
        lp, wall = loop_short(kind)
        scene = [(tab, CAR)] + coupler_at(phi) + [(lp, CAR), (wall, WALL)]
        render(scene, f"{OUT}/coupled_{tag}_3q.png", cam(tgt, -55, 30, 64), size=(1600, 1000))
        render(scene, f"{OUT}/coupled_{tag}_side.png", cam(tgt, -90, 0, 200), parallel=True, pscale=11.5, size=(1800, 900))
    lp, wall = loop_short("car")
    scene = [(tab, CAR)] + coupler_at(0.0) + [(lp, CAR), (wall, WALL)]
    render(scene, f"{OUT}/coupled_car_3q_back.png", cam(tgt, -125, 28, 64), size=(1600, 1000))
    render(scene, f"{OUT}/coupled_car_under.png", cam(tgt, -55, -32, 64), size=(1600, 1000))
    # lifted to couple or uncouple: cars pushed 2 mm together, arm up
    lp, wall = loop_short("car", -2.0)
    render([(tab, CAR)] + coupler_at(36) + [(lp, CAR), (wall, WALL)], f"{OUT}/lifted_3q.png",
           cam(tgt, -55, 30, 64), size=(1600, 1000))
    # exploded, in assembly order: arm pinned into the swivel, swivel under the tab, kingpin down from the top,
    # lock filament across under the swivel
    drop = -9.0
    sub = [(C.swivel().translate((0, 0, drop)), SWIVEL), (C.arm().translate((0, 0, drop)), ARM),
           (C.pin().translate((0, 9, drop)), PIN)]
    ex = [(tab, CAR), (C.kingpin().translate((0, 0, 11)), KINGPIN), (C.lock_pin().translate((0, -10, drop)), PIN)] + sub
    render(ex, f"{OUT}/exploded_3q.png", cam((8, 0, 24), -60, 22, 78), size=(1600, 1200))
    # parts alone
    render([(C.kingpin(), KINGPIN)], f"{OUT}/kingpin.png", cam((0, 0, 23.5), -60, 20, 32))
    render([(C.swivel(), SWIVEL)], f"{OUT}/swivel.png", cam((5, 0, 25), -60, 28, 48))
    render([(C.arm(), ARM)], f"{OUT}/arm.png", cam((17, 0, 26), -60, 25, 52))
    render([(C.arm(), ARM)], f"{OUT}/arm_back.png", cam((17, 0, 26), -150, 20, 52))
    # print plate (the black PLA plate: two coupler sets and the tender's loop), top
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "slice"))
    import plate as P
    col = {"arm": ARM, "swivel": SWIVEL, "kingpin": KINGPIN, "tender": CLIP}
    items = [(m, next(c for k, c in col.items() if k in n)) for n, m in P.layout()]
    bed = Manifold.cube((220, 220, 0.4)).translate((0, 0, -0.4))
    render(items + [(bed, "#e6e6e6")], f"{OUT}/plate_top.png", cam((110, 110, 0), -90, 89.9, 200), parallel=True,
           pscale=20, size=(1400, 900))
    render(items + [(bed, "#e6e6e6")], f"{OUT}/plate_3q.png", cam((110, 110, 3), -60, 40, 135), size=(1400, 1000))


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
    phi_e, xi_e = K.seated(C.E_LOOP_TOP, C.E_LOOP_T)[:2]
    fig, axs = plt.subplots(2, 2, figsize=(14, 8.6))
    states = [("Coupled to a car's loop and pulling: bar clamped between underside and raked face", 0.0, "car", 0.0),
              (f"Coupled to the engine's lower loop and pulling: arm settles at {phi_e:.0f} deg", phi_e, "engine", 0.0),
              ("To uncouple: push 2 mm together, lift about 35 deg", 36.0, "car", -2.0),
              (f"Uncoupled: arm rests on its stop at {C.PHI_STOP:.0f} deg", C.PHI_STOP, None, None)]
    tabsec = box(C.TAB_X0, C.TAB_TOP - C.TAB_T, C.TAB_TIP, C.TAB_TOP).difference(
        box(-C.HOLE_L / 2, 0, C.HOLE_L / 2, 40))
    ridge = box(C.TAB_X0, C.TAB_TOP, C.RIDGE_X1, C.RIDGE_TOP)
    kp = box(-C.HEAD_HX, C.TAB_TOP, C.HEAD_HX, C.TAB_TOP + C.HEAD_T).union(
        box(-C.KP_R, C.KP_Z0, C.KP_R, C.TAB_TOP)).difference(C.teardrop(0, C.LOCK_Z, C.LOCK_D / 2, up=False))
    sw_mid = box(-C.PLATE_R, C.SW_Z0, C.TONGUE_X, C.SW_Z1).difference(box(-C.BEAR_R, 0, C.BEAR_R, 40)).difference(
        C.circle(C.KX, C.KZ, C.K_R + C.SWEEP_CLR))
    cheek = C.cheek_profile()
    arm_mid = C.arm_outline().difference(C.circle(C.KX, C.KZ, C.ARM_HOLE))
    for ax, (title, phi, kind, dx) in zip(axs.flat, states):
        draw(ax, ridge, color="#9a9a9a")
        draw(ax, tabsec, color=CAR)
        if kind is not None:
            t, top = K.KIND[kind]["t"], K.KIND[kind]["top"]
            xi = (xi_e if kind == "engine" else C.X_I) + dx
            ol = C.E_OPEN_L if kind == "engine" else C.OPEN_L
            tip = xi - C.END_BAR
            lp = box(tip, top - t, xi + ol + C.END_BAR, top).difference(box(xi, 0, xi + ol, 40))
            draw(ax, lp, color=CAR)
            draw(ax, box(xi + ol + C.END_BAR, top - 7, xi + ol + C.END_BAR + 4, top + 9), color=WALL)
        draw(ax, cheek, color=SWIVEL, alpha=0.3)
        draw(ax, sw_mid, color=SWIVEL)
        draw(ax, kp, color=KINGPIN)
        draw(ax, affinity.rotate(arm_mid, phi, origin=(C.KX, C.KZ)), color=ARM, alpha=0.95)
        ax.add_patch(plt.Circle((C.KX, C.KZ), C.PIN_D / 2, color=PIN, ec="k", lw=0.6, zorder=5))
        ax.add_patch(plt.Circle((0, C.LOCK_PIN_Z), C.PIN_D / 2, color=PIN, ec="k", lw=0.6, zorder=5))
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal")
        ax.set_xlim(-9, 37)
        ax.set_ylim(17.5, 34)
        ax.grid(alpha=0.25)
        ax.set_xlabel("mm from the tab hole, along the track")
        ax.set_ylabel("mm above the table")
    a = axs[0, 0]
    a.annotate("tab", (-6.5, C.TAB_TOP - 0.75), color="white", fontsize=9, ha="center", va="center")
    a.annotate("ridge (beside the cut)", (-3.5, C.RIDGE_TOP + 0.4), color="#555", fontsize=8, ha="center")
    a.annotate("kingpin", (-3.0, C.KP_Z0 + 0.6), color=KINGPIN, fontsize=9, ha="right")
    a.annotate("lock filament", (0, C.LOCK_PIN_Z), xytext=(-8.5, 18.3), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
    a.annotate("swivel", (6.0, 21.2), color=SWIVEL, fontsize=9, ha="center")
    a.annotate("arm", (17, 32.0), color=ARM, fontsize=9, ha="center")
    a.annotate("loop", (C.X_I + C.OPEN_L + 1.1, C.LOOP_TOP - C.LOOP_T - 1.8), color=CAR, fontsize=9, ha="center")
    a.annotate("hinge pin", (C.KX, C.KZ), xytext=(C.KX - 5, 32.3), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
    fig.text(0.5, 0.005, "Section through the middle. Pale blue: the swivel's cheeks, either side of the arm.",
             ha="center", fontsize=9, color="#555")
    plt.tight_layout(rect=(0, 0.02, 1, 1))
    plt.savefig(f"{OUT}/sections.png", dpi=120)
    plt.close()


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    views()
    sections()
    tender_views()
    print("renders in", OUT)



# ---------------- tender's clip-on loop ----------------


def to_tender(m):
    """Coupler frame (x toward the car ahead) -> tender frame (u out from the tender's beam face)."""
    import tender_loop as T
    return m.mirror((1, 0, 0)).translate((C.X_I + T.ROOT + T.OPEN_L, 0, 0))


def tender_views():
    import tender_loop as T
    clip, beam, pins = T.clip(with_support=False), T.beam(), T.lock_pins()
    coupler = [(to_tender(C.tab()), CAR)] + [(to_tender(m), col) for m, col in coupler_at(0.0)]
    scene = [(beam, CAR), (clip, CLIP), (pins, PIN)] + coupler
    render(scene, f"{OUT}/tender_loop_3q.png", cam((10, 0, 27), -130, 32, 80), size=(1600, 1100))
    render([(beam, CAR), (clip, CLIP), (pins, PIN)], f"{OUT}/tender_loop_under.png", cam((2, 0, 27), -150, -35, 62),
           size=(1600, 1100))
    render([(T.clip(), CLIP)], f"{OUT}/tender_loop_part.png", cam((4, 0, 28), -125, 30, 60))
    # sections: through a window and through the middle
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2))
    for ax, v, title in ((axs[0], T.WIN_V, "Through a window: arm over the top, peg down the window, lock under"),
                         (axs[1], 0.0, "Through the middle: plate down the beam's face, new loop")):
        face = box(-T.WALL_T, T.BEAM_TOP - T.BEAM_H, 0, T.BEAM_TOP)
        deck = box(-5.4, T.DECK_Z0, -T.WALL_T, T.BEAM_TOP)
        if v:
            deck = deck.difference(box(T.WIN_U0, 0, T.WIN_U1, 40))
        draw(ax, face.union(deck), color=CAR)
        if v == 0:
            prof = box(0, T.Z0, T.PLATE_T, T.BEAM_TOP + T.TOP_T).union(box(T.PLATE_T, T.LOOP_Z0, T.ROOT, T.LOOP_TOP)).union(
                box(T.ROOT + T.OPEN_L, T.LOOP_Z0, T.LOOP_OUT, T.LOOP_TOP))
        else:
            prof = box(0, T.Z0, T.PLATE_T, T.BEAM_TOP + T.TOP_T).union(box(T.ARM_U0, T.BEAM_TOP, T.PLATE_T, T.BEAM_TOP + T.TOP_T)).union(
                box(T.PEG_U0, T.Z0, T.PEG_U1, T.BEAM_TOP))
        draw(ax, prof, color=CLIP)
        if v:
            ax.add_patch(plt.Rectangle((-T.WALL_T - 6.0 + 0.0, T.LOCK_PIN_Z - C.PIN_D / 2), 6.0 - 0.0, C.PIN_D,
                                       color=PIN, ec="k", lw=0.6, zorder=5))
            ax.annotate("lock filament", (-5.5, T.LOCK_PIN_Z), xytext=(-9.5, 22.3), fontsize=8,
                        arrowprops=dict(arrowstyle="-", lw=0.6))
            ax.annotate("window", (-2.2, 29.2), xytext=(-9.5, 33.6), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
        else:
            ax.annotate("new loop (same as the cars')", (8, T.LOOP_TOP), xytext=(4.5, 30.5), fontsize=8,
                        arrowprops=dict(arrowstyle="-", lw=0.6))
            ax.annotate("stub cut off here", (0, 26.7), xytext=(-9.5, 22.3), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
        ax.annotate("beam", (-0.5, 24.0), color="white", fontsize=8, ha="center", rotation=90)
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal")
        ax.set_xlim(-10, 14)
        ax.set_ylim(21.5, 35)
        ax.grid(alpha=0.25)
        ax.set_xlabel("mm out from the beam's face, along the track")
        ax.set_ylabel("mm above the table")
    plt.tight_layout()
    plt.savefig(f"{OUT}/tender_loop_sections.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
