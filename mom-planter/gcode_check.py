## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Plot toolpaths from the sliced G-code: the bottom text in layers 1 and 4, and a layer through the leg hinges."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

path = sys.argv[1] if len(sys.argv) > 1 else "out/package/mom_planter_HyperPLA.gcode"


def parse(path, want_layers):
    layers = {}
    layer, x, y, e, typ, absE = -1, 0.0, 0.0, 0.0, "", False
    for line in open(path):
        if line.startswith(";LAYER_CHANGE"):
            layer += 1
            continue
        if line.startswith(";TYPE:"):
            typ = line[6:].strip()
            continue
        c = line.split(";")[0].split()
        if not c:
            continue
        if c[0] == "M82": absE = True
        if c[0] == "M83": absE = False
        if c[0] in ("G1", "G0", "G2", "G3"):
            nx, ny, de = x, y, 0.0
            for t in c[1:]:
                if t[0] == "X": nx = float(t[1:])
                elif t[0] == "Y": ny = float(t[1:])
                elif t[0] == "E": de = float(t[1:])
            if layer in want_layers and de > 0 and (nx != x or ny != y):
                layers.setdefault(layer, []).append((x, y, nx, ny, typ))
            x, y = nx, ny
    return layers


L = parse(path, {0, 3, 22})
shift = np.load("out/stl/shift.npy")
fig, axs = plt.subplots(1, 3, figsize=(27, 9.5))
colors = {"Bottom surface": "#1f4e9c", "Internal solid infill": "#2a7a2a", "Outer wall": "#888888",
          "Inner wall": "#bbbbbb", "Gap infill": "#c0392b"}
for ax, li, title in ((axs[0], 0, "layer 1 (on the bed), seen from above"), (axs[1], 3, "layer 4"),
                      (axs[2], 22, "layer 23 (through the leg hinge axes)")):
    segs = L.get(li, [])
    for typ in sorted(set(s[4] for s in segs)):
        ss = [((a, b), (c, d)) for a, b, c, d, t in segs if t == typ]
        ax.add_collection(LineCollection(ss, colors=colors.get(typ, "#e67e22"), linewidths=0.6, label=f"{typ} ({len(ss)})"))
    ax.set_aspect("equal")
    if li < 20:
        ax.set_xlim(shift[0] - 46, shift[0] + 46); ax.set_ylim(shift[1] - 46, shift[1] + 46)
    else:
        ax.set_xlim(shift[0] - 32, shift[0] + 32); ax.set_ylim(shift[1] - 100, shift[1] - 40)
    ax.set_title(title); ax.legend(loc="upper right", fontsize=8)
plt.tight_layout(); plt.savefig("out/renders/gcode_layers.png", dpi=55)

# what you will see from below: layer 1 mirrored back (bottom view), lines only, shaded by direction
segs = np.array([s[:4] for s in L[0] if s[4] in ("Bottom surface", "Gap infill", "Outer wall", "Inner wall")])
ang = np.arctan2(segs[:, 3] - segs[:, 1], segs[:, 2] - segs[:, 0])
shade = 0.25 + 0.6 * np.abs(np.cos(2 * (ang - np.radians(20))))        # raking light 20 degrees off x
fig, ax = plt.subplots(figsize=(9, 9))
xs = -(segs[:, [0, 2]] - shift[0]); ys = segs[:, [1, 3]] - shift[1]     # pot upside down, heart toward you
ax.add_collection(LineCollection(np.stack([np.c_[xs[:, 0], ys[:, 0]], np.c_[xs[:, 1], ys[:, 1]]], 1),
                                 colors=plt.cm.Blues(shade), linewidths=1.1))
ax.set_aspect("equal"); ax.set_xlim(-46, 46); ax.set_ylim(-46, 46); ax.set_facecolor("#0d2547")
ax.set_title("bottom face, pot upside down with the heart toward you (layer 1 lines, shaded by direction)")
plt.tight_layout(); plt.savefig("out/renders/bottom_view_sim.png", dpi=80)
print({k: len(v) for k, v in L.items()})
