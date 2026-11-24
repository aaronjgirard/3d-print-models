## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Export the swivel and arm in print orientation (on their side, the profile flat on the bed) as STL and 3MF into
out/package, plus a plate with two sets."""
import os
import shutil
import numpy as np
import trimesh
import coupler as C

OUT = "out/package"


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


def print_pose(m):
    """Thickness (y) up, profile on the bed, corner at the origin."""
    m = m.rotate((-90, 0, 0))
    b = m.bounding_box()
    return m.translate((-b[0], -b[1], -b[2]))


def parts():
    return {"coupler_swivel": print_pose(C.swivel()), "coupler_arm": print_pose(C.arm())}


def plate(n=2, gap=6.0):
    """n sets in a row, centered on the 220 x 220 bed."""
    ps = parts()
    placed, y = [], 0.0
    for i in range(n):
        x = 0.0
        for name in ("coupler_arm", "coupler_swivel"):
            m = ps[name]
            b = m.bounding_box()
            placed.append((f"{name}_{i + 1}", m.translate((x, y, 0))))
            x += b[3] - b[0] + gap
        y += max(ps[k].bounding_box()[4] for k in ps) + gap
    lo = np.min([p.bounding_box()[:3] for _, p in placed], axis=0)
    hi = np.max([p.bounding_box()[3:] for _, p in placed], axis=0)
    shift = (110 - (lo[0] + hi[0]) / 2, 110 - (lo[1] + hi[1]) / 2, 0)
    return [(n_, p.translate(shift)) for n_, p in placed]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT + "/stl")
    lines = ["part, x mm, y mm, z mm (print height), volume mm3"]
    for name, m in parts().items():
        tm = to_trimesh(m)
        assert tm.is_watertight and tm.is_volume, name
        tm.export(f"{OUT}/stl/{name}.stl")
        tm.export(f"{OUT}/{name}.3mf")
        b = m.bounding_box()
        lines.append(f"{name}, {b[3] - b[0]:.1f}, {b[4] - b[1]:.1f}, {b[5] - b[2]:.1f}, {m.volume():.0f}")
    scene = trimesh.Scene()
    for name, m in plate():
        tm = to_trimesh(m)
        assert tm.is_watertight
        scene.add_geometry(tm, node_name=name, geom_name=name)
    scene.export(f"{OUT}/coupler_plate_2_sets.3mf")
    trimesh.util.concatenate([to_trimesh(m) for _, m in plate()]).export(f"{OUT}/stl/coupler_plate_2_sets.stl")
    open(f"{OUT}/parts.csv", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
