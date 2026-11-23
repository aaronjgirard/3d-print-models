## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Preview renders (pyvista, off screen) into out/renders."""
import os
import math
import numpy as np
import pyvista as pv
import trimesh
import track as T
import check as C

pv.OFF_SCREEN = True
OUT = "out/renders"
TRACK = "#3a3a3c"      # printed pieces
ORIG = "#4a6fa5"       # stand-ins for the originals
LIGHT = "#8c8c8f"


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)


def pv_mesh(m):
    tm = to_trimesh(m)
    faces = np.hstack([np.full((len(tm.faces), 1), 3), tm.faces]).astype(np.int64)
    return pv.PolyData(tm.vertices, faces)


def render(items, path, camera, size=(1600, 1000), zoom=1.0, parallel=False, pscale=None):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for m, color in items:
        p.add_mesh(pv_mesh(m), color=color, smooth_shading=False, specular=0.2, specular_power=12)
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
    return path


def cam(target, az, el, dist):
    """Camera looking at target from azimuth az (deg, from +x toward +y) and elevation el (deg)."""
    a, e = math.radians(az), math.radians(el)
    eye = (target[0] + dist * math.cos(e) * math.cos(a), target[1] + dist * math.cos(e) * math.sin(a),
           target[2] + dist * math.sin(e))
    return [eye, target, (0, 0, 1)]


def main():
    os.makedirs(OUT, exist_ok=True)
    st, cv, tp = T.straight(), T.curve(), T.test_piece()
    sp, cp, tpp = T.Path(T.STRAIGHT_L), T.curve_path(), T.Path(T.TEST_L)
    # whole pieces
    render([(st, TRACK)], f"{OUT}/straight.png", cam((T.STRAIGHT_L / 2, 0, 0), -60, 35, 260))
    render([(cv, TRACK)], f"{OUT}/curve.png", cam((70, -25, 0), -70, 40, 250))
    render([(cv, TRACK), (T.attach(cv, cp), LIGHT)], f"{OUT}/two_curves_top.png", cam((140, -60, 0), -90, 89.9, 330),
           parallel=True, zoom=1.3)
    # ends and grain close up
    render([(st, TRACK)], f"{OUT}/male_end.png", cam((0, 0, 1), -145, 35, 75))
    render([(st, TRACK)], f"{OUT}/female_end.png", cam((T.STRAIGHT_L, 0, 1), -35, 35, 80))
    render([(st, TRACK)], f"{OUT}/prong_L.png", cam((T.STRAIGHT_L + 3, 14, 1), -20, 50, 55))
    c = T.tie_centers(T.STRAIGHT_L)
    render([(st, TRACK)], f"{OUT}/grain_ties.png", cam((c[2], 0, 2), -70, 50, 95))
    render([(st, TRACK)], f"{OUT}/grain_deck.png", cam((T.STRAIGHT_L - 8, 0, 2), -60, 55, 75))
    render([(st.rotate((0, 180, 0)).translate((T.STRAIGHT_L, 0, 0)), TRACK)], f"{OUT}/female_end_under.png",
           cam((0, 0, -1), -35, 35, 80))
    render([(st.rotate((0, 180, 0)), TRACK)], f"{OUT}/male_end_under.png", cam((0, 0, -1), -145, 35, 75))
    # joints: printed into printed, original male into printed female, printed male into original female
    nxt = T.attach(tp, tpp)
    render([(tp, TRACK), (nxt, LIGHT)], f"{OUT}/joint_printed.png", cam((T.TEST_L, 0, 1), -50, 40, 95))
    om = T.attach(C.orig_male_stub(plate_half=10.15), tpp)
    render([(tp, TRACK), (om, ORIG)], f"{OUT}/joint_orig_male.png", cam((T.TEST_L, 0, 1), -50, 40, 95))
    of = C.orig_female_stub()
    render([(of, ORIG), (T.attach(tp, T.Path(40.0)), TRACK)], f"{OUT}/joint_orig_female.png", cam((40, 0, 1), -50, 40, 95))
    # section through the joint centerline (printed into printed), seen from the side
    cut_box = T.prism(T.rect(-50, 120, -0.3, 0.3), -5, 20, T.Path(1))
    a, b = tp ^ cut_box, nxt ^ cut_box
    render([(a, TRACK), (b, LIGHT)], f"{OUT}/joint_section.png", cam((T.TEST_L, 0, 3), 90, 0, 200), parallel=True,
           pscale=9, size=(1800, 700))
    cut2 = T.prism(T.rect(-50, 120, -17.0, -16.4), -5, 20, T.Path(1))
    render([(tp ^ cut2, TRACK), (nxt ^ cut2, LIGHT)], f"{OUT}/joint_section_rail.png",
           cam((T.TEST_L, -16.75, 3), 90, 0, 200), parallel=True, pscale=9, size=(1800, 700))
    print("renders in", OUT)


if __name__ == "__main__":
    main()
