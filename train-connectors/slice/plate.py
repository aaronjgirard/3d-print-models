## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Lay out the black PLA plate (two coupler sets, plus the tender's clip-on loop when it exists) on the
220 x 220 bed, write one STL per part with the layout baked in, and slice them with the OrcaSlicer 2.5.0
command line using the presets from make_presets.py.

Run from the train-connectors folder:  python3 slice/plate.py [path to OrcaSlicer AppRun]
Writes slice/plate/*.stl, out/package/black_pla_plate.gcode, and out/package/black_pla_plate.3mf (an Orca project
with the same layout and presets, for the Prepare tab).
"""
import os
import shutil
import subprocess
import sys
import numpy as np
import trimesh
sys.path.insert(0, os.getcwd())
import export as E

ORCA = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/slicer/squashfs-root/AppRun"
HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 6.0


def parts():
    """(name, manifold in print orientation on the bed) for everything on the plate."""
    ps = E.parts()
    items = []
    for i in (1, 2):
        for name in ("coupler_arm", "coupler_swivel", "coupler_kingpin"):
            items.append((f"{name}_{i}", ps[name]))
    try:
        import tender_loop as T
        items.append(("tender_loop", T.print_part()))
    except ImportError:
        pass
    return items


def layout():
    """Coupler sets in two rows as in export.plate(); the tender loop in a row below them."""
    items = parts()
    rows = [[n for n, _ in items if n.endswith("_1")], [n for n, _ in items if n.endswith("_2")],
            [n for n, _ in items if not n[-2:] in ("_1", "_2")]]
    lookup = dict(items)
    placed, y = [], 0.0
    for row in rows:
        if not row:
            continue
        x, h = 0.0, 0.0
        for n in row:
            m = lookup[n]
            b = m.bounding_box()
            placed.append((n, m.translate((x - b[0], y - b[1], -b[2]))))
            x += b[3] - b[0] + GAP
            h = max(h, b[4] - b[1])
        y += h + GAP
    lo = np.min([p.bounding_box()[:3] for _, p in placed], axis=0)
    hi = np.max([p.bounding_box()[3:] for _, p in placed], axis=0)
    shift = (110 - (lo[0] + hi[0]) / 2, 110 - (lo[1] + hi[1]) / 2, 0)
    return [(n, p.translate(shift)) for n, p in placed]


def main():
    pdir = os.path.join(HERE, "plate")
    if os.path.isdir(pdir):
        shutil.rmtree(pdir)
    os.makedirs(pdir)
    files = []
    for n, m in layout():
        tm = E.to_trimesh(m)
        assert tm.is_watertight and tm.is_volume, n
        b = m.bounding_box()
        assert b[0] > 2 and b[1] > 2 and b[3] < 218 and b[4] < 218, n
        f = os.path.join(pdir, f"{n}.stl")
        tm.export(f)
        files.append(f)
    os.makedirs("out/package", exist_ok=True)
    odir = os.path.join(HERE, "out_gcode")
    if os.path.isdir(odir):
        shutil.rmtree(odir)
    cmd = [ORCA, "--slice", "0", "--debug", "1", "--outputdir", odir,
           "--load-settings", f"{HERE}/machine.json;{HERE}/process.json",
           "--load-filaments", f"{HERE}/filament.json", "--curr-bed-type", "High Temp Plate", "--arrange", "0",
           "--export-3mf", "black_pla_plate.3mf"] + files
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    shutil.copy(os.path.join(odir, "plate_1.gcode"), "out/package/black_pla_plate.gcode")
    shutil.copy(os.path.join(odir, "black_pla_plate.3mf"), "out/package/black_pla_plate.3mf")   # Orca project
    g = open("out/package/black_pla_plate.gcode").read().splitlines()
    for key in ("; estimated printing time (normal mode)", "; total filament used [g]", "; total layers count"):
        print(next(l for l in g if l.startswith(key)))
    cmds = [l.split(";")[0].strip() for l in g]
    cmds = [c for c in cmds if c and not c.startswith("M73")]        # M73 is only the progress display
    print("objects:", sum(1 for c in cmds if c.startswith("EXCLUDE_OBJECT_DEFINE")),
          "| START_PRINT:", cmds.count("START_PRINT"), "| last command:", cmds[-1],
          "| G28 lines:", sum(1 for c in cmds if c.startswith("G28")))


if __name__ == "__main__":
    main()
