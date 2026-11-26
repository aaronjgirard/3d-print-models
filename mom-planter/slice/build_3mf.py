## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Build the Orca project: pot and legs as parts of one object, the bottom text as a modifier part with
concentric bottom and internal-solid patterns; then slice it with the OrcaSlicer 2.5.0 command line.

Run from the mom-planter folder after export.py:  python3 slice/build_3mf.py [path to OrcaSlicer AppRun]
Writes out/package/mom_planter_HyperPLA.3mf (sliced project) and out/package/mom_planter_HyperPLA.gcode.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ORCA = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/slicer/squashfs-root/AppRun"
HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.abspath("out/stl")
PKG = os.path.abspath("out/package")
NAME = "mom_planter_HyperPLA"
env = dict(os.environ, XDG_RUNTIME_DIR="/tmp/xdg")
os.makedirs("/tmp/xdg", mode=0o700, exist_ok=True)
SETTINGS = ["--load-settings", f"{HERE}/machine.json;{HERE}/process.json",
            "--load-filaments", f"{HERE}/filament.json", "--curr-bed-type", "High Temp Plate"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    return r


def main():
    modifier = json.load(open(f"{HERE}/changes_from_stock.json"))["bottom_text_modifier"]
    work = os.path.join(HERE, "work")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    parts = [f"{STL}/planter_pot.stl", f"{STL}/planter_legs.stl", f"{STL}/bottom_text_modifier.stl"]
    run([ORCA, "--assemble", "--arrange", "0", "--outputdir", work, "--export-3mf", "assembled.3mf"] + SETTINGS + parts)

    # patch: names, and part 3 becomes a modifier with its own fill patterns
    src = os.path.join(work, "assembled.3mf")
    dst = os.path.join(work, f"{NAME}_unsliced.3mf")
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "Metadata/model_settings.config":
            s = data.decode()
            s = s.replace('<metadata key="name" value="Assembly"/>', '<metadata key="name" value="I heart MOM planter"/>')
            s = s.replace('value="planter_pot.stl"/>\n      <metadata key="matrix"', 'value="pot"/>\n      <metadata key="matrix"', 1)
            s = s.replace('<metadata key="name" value="planter_legs.stl"/>', '<metadata key="name" value="legs (print in place)"/>')
            m = re.search(r'<part id="3" subtype="normal_part">\n(\s*)<metadata key="name" value="bottom_text_modifier.stl"/>', s)
            assert m, "part 3 not found"
            ind = m.group(1)
            extra = "".join(f'{ind}<metadata key="{k}" value="{v}"/>\n' for k, v in modifier.items())
            s = s.replace(m.group(0), f'<part id="3" subtype="modifier_part">\n{ind}<metadata key="name" value="bottom text THANKSGIVING 2026"/>\n{extra}'.rstrip("\n"), 1)
            data = s.encode()
        zout.writestr(item, data)
    zout.close()

    # slice the patched project
    odir = os.path.join(HERE, "out_gcode")
    shutil.rmtree(odir, ignore_errors=True)
    os.makedirs(odir)
    run([ORCA, "--slice", "0", "--outputdir", odir, "--export-3mf", f"{NAME}.3mf"] + SETTINGS + [dst])
    os.makedirs(PKG, exist_ok=True)
    shutil.copy(os.path.join(odir, "plate_1.gcode"), f"{PKG}/{NAME}.gcode")
    shutil.copy(os.path.join(odir, f"{NAME}.3mf"), f"{PKG}/{NAME}.3mf")
    g = open(f"{PKG}/{NAME}.gcode").read().splitlines()
    for key in ("; estimated printing time (normal mode)", "; total filament used [g]", "; total layers count"):
        print(next((l for l in g if l.startswith(key)), key + " ?"))
    cmds = [l.split(";")[0].strip() for l in g]
    cmds = [c for c in cmds if c and not c.startswith("M73")]
    print("START_PRINT:", cmds.count("START_PRINT"), "| last command:", cmds[-1],
          "| G28 lines:", sum(1 for c in cmds if c.startswith("G28")))


if __name__ == "__main__":
    main()
