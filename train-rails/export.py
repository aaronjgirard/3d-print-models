## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Export every part in print orientation (bottom on the bed, centered) as STL and 3MF into out/package,
with a rough PLA estimate in parts.csv (the slicer's figure is better: 4 / 15 / 14 g)."""
import os
import shutil
import numpy as np
import trimesh
import track as T

OUT = "out/package"
DENSITY = 1.24          # PLA g/cm3


def to_trimesh(m):
    """Mesh exactly as manifold3d produced it (track.piece already merges coplanar faces and removes
    slivers); trimesh's own processing is left off so it cannot reorder or drop anything."""
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


def centered(m):
    b = m.bounding_box()
    return m.translate((-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]))


def estimate(m, walls=3, infill=0.20):
    """Rough extruded volume in cm3: shell (walls, top, bottom) plus sparse infill."""
    t_shell = 0.42 * walls * 0.85 + 0.15
    V = m.volume() / 1000.0
    A = m.surface_area() / 100.0
    shell = min(V, A * t_shell / 10.0)
    return shell + (V - shell) * infill


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT + "/stl")
    os.makedirs(OUT + "/3mf")
    parts = {"track_test_piece": T.test_piece(), "track_straight": T.straight(), "track_curve_22_5": T.curve()}
    lines = ["part, x mm, y mm, z mm, PLA g (rough)"]
    for name, m in parts.items():
        m = centered(m)
        tm = to_trimesh(m)
        assert tm.is_watertight and tm.is_volume, name
        tm.export(f"{OUT}/stl/{name}.stl")
        tm.export(f"{OUT}/3mf/{name}.3mf")
        b = m.bounding_box()
        lines.append(f"{name}, {b[3] - b[0]:.1f}, {b[4] - b[1]:.1f}, {b[5] - b[2]:.1f}, {estimate(m) * DENSITY:.0f}")
    open(f"{OUT}/parts.csv", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
