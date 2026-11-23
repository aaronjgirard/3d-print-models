## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""How many pieces fit on the 220 x 220 bed, and plate files for the fullest layouts (out/plates).

Result (Nov 22 2026):
- With 3 mm between parts and 4.5 mm from the bed edges: 4 straights (9 mm apart) or 4 curves (nested,
  every other one slid 11 mm so the tie ends interleave). 5 of either does not fit.
- Tight, with 2 mm between parts and 1.5 mm from the bed edges: 5 straights fit, every other one turned
  180 degrees and slid 15.5 mm so the tie ends interleave (1.8 mm from the front and back edges).
  5 curves still do not fit; neither do 5 straights at 2.5 mm gaps with 1 mm from the edges.
Load the plate 3MF rather than arranging copies in the slicer, which spaces curves by their outline and
fits only 3, and never turns every other straight around.

Footprints are the parts' real outlines (union of slices through every height band), not bounding
boxes, so neighbouring pieces can tuck their tie ends into each other's gaps.
"""
import math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
from shapely.ops import unary_union
import track as T

BED = 220.0
EDGE = 4.5        # standard plates: room for a one-loop skirt 3 mm out, inside the bed
GAP = 3.0         # standard plates: between parts
TIGHT_EDGE = 1.5  # tight plate: skirt and brim off
TIGHT_GAP = 2.0


def footprint(m, zs=(0.1, 0.9, 1.3, 1.5, 2.1, 2.5, 2.9, 4.0)):
    """Outline of a part seen from above: union of its slices (holes ignored, they do not matter here)."""
    polys = []
    for z in zs:
        for p in m.slice(z).to_polygons():
            q = Polygon(p)
            if q.is_valid and q.area > 0 and q.exterior.is_ccw:
                polys.append(Polygon(q.exterior))
    return unary_union(polys).buffer(0)


def fits(placed, gap=GAP, edge=EDGE):
    """All placed footprints inside the usable bed area and at least `gap` apart."""
    u = unary_union(placed)
    x0, y0, x1, y1 = u.bounds
    if x1 - x0 > BED - 2 * edge + 1e-6 or y1 - y0 > BED - 2 * edge + 1e-6:
        return False
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            if placed[i].distance(placed[j]) < gap - 1e-6:
                return False
    return True


def centre(placed):
    """Shift a layout so its outline is centred on the bed; returns (shifted footprints, dx, dy)."""
    x0, y0, x1, y1 = unary_union(placed).bounds
    dx, dy = BED / 2 - (x0 + x1) / 2, BED / 2 - (y0 + y1) / 2
    return [affinity.translate(p, dx, dy) for p in placed], dx, dy


def rows(fp, n, flip_alternate, pitch, shift):
    """n copies stacked in y at `pitch`; every other copy shifted by `shift` in x and, if flip_alternate,
    turned 180 degrees about its own centre. Returns list of (footprint, angle, x, y)."""
    cx, cy = fp.centroid.x, fp.centroid.y
    out = []
    for k in range(n):
        ang = 180.0 if (flip_alternate and k % 2) else 0.0
        q = affinity.rotate(fp, ang, origin=(cx, cy))
        x, y = (shift if k % 2 else 0.0), k * pitch
        out.append((affinity.translate(q, x, y), ang, x, y))
    return out


def best_rows(fp, n, pitches, shifts, flips=(False, True), gap=GAP, edge=EDGE):
    """First pitch (in the order given) at which n copies fit, over the shifts and flip options;
    None if none fit. Descending pitches give the most even spacing, ascending the tightest layout."""
    for pitch in pitches:
        for flip in flips:
            for shift in shifts:
                lay = rows(fp, n, flip, pitch, shift)
                if fits([p for p, *_ in lay], gap, edge):
                    return pitch, flip, shift, lay
    return None


def most(fp, label, pitches, shifts, n_max=8, gap=GAP, edge=EDGE):
    best = None
    for n in range(1, n_max + 1):
        r = best_rows(fp, n, pitches, shifts, gap=gap, edge=edge)
        if r is None:
            break
        best = (n,) + r
    n, pitch, flip, shift, lay = best
    print(f"{label}: {n} per plate (pitch {pitch:.2f} mm, every other one {'turned 180 deg and ' if flip else ''}"
          f"shifted {shift:.1f} mm)")
    return best


def straight_fp():
    return footprint(T.straight())


def curve_fp():
    """Curve turned so its chord runs along x (the bulge faces +y or -y)."""
    fp = footprint(T.curve())
    p0, _ = T.curve_path().frame(0.0)
    p1, _ = T.curve_path().frame(T.curve_path().L)
    ang = -math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    return affinity.rotate(fp, ang, origin=(0, 0)), ang


def plate(part, fp_turn, lay):
    """Place copies of a manifold part to match a layout of footprints (part pre-turned by fp_turn degrees
    about the origin, as its footprint was), centred on the bed. Returns (list of manifolds, footprints)."""
    fps = [p for p, *_ in lay]
    fps_c, dx, dy = centre(fps)
    base = part.rotate((0, 0, fp_turn))
    fp0 = footprint(base)
    cx, cy = fp0.centroid.x, fp0.centroid.y
    parts = []
    for (p, ang, x, y) in lay:
        m = base.translate((-cx, -cy, 0)).rotate((0, 0, ang)).translate((cx + x + dx, cy + y + dy, 0))
        parts.append(m)
    return parts, fps_c


def summary(fps):
    n = len(fps)
    x0, y0, x1, y1 = unary_union(fps).bounds
    gap = min(fps[i].distance(fps[j]) for i in range(n) for j in range(i + 1, n))
    print(f"  min gap {gap:.2f} mm, bed edges x {x0:.1f} / {BED - x1:.1f}, y {y0:.1f} / {BED - y1:.1f} mm")


def _panel(ax, fps, title, edge):
    import matplotlib.pyplot as plt
    ax.add_patch(plt.Rectangle((0, 0), BED, BED, fill=False, lw=1.5, ec="#444"))
    ax.add_patch(plt.Rectangle((edge, edge), BED - 2 * edge, BED - 2 * edge, fill=False, lw=0.8, ls="--", ec="#999"))
    for p in fps:
        for g in getattr(p, "geoms", [p]):
            x, y = g.exterior.xy
            ax.fill(x, y, color="#3a3a3c")
    ax.set_xlim(-5, BED + 5); ax.set_ylim(-5, BED + 5); ax.set_aspect("equal")
    ax.set_title(title, fontsize=11); ax.set_xlabel("mm"); ax.set_ylabel("mm")


def draw(fps, title, path, edge=EDGE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 6.4))
    _panel(ax, fps, title, edge)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def overview(panels, path):
    """panels: list of (footprints, title, edge). Dashed line: the margin each layout keeps from the bed edge."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(panels), figsize=(5.6 * len(panels), 6.0))
    for ax, (fps, title, edge) in zip(axs, panels):
        _panel(ax, fps, title, edge)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def export_plate(parts, name):
    import os
    import trimesh
    from export import to_trimesh
    os.makedirs("out/plates", exist_ok=True)
    sc = trimesh.Scene()
    for i, m in enumerate(parts):
        tm = to_trimesh(m)
        sc.add_geometry(tm, node_name=f"{name}_{i + 1}", geom_name=f"{name}_{i + 1}")
    sc.export(f"out/plates/{name}.3mf")
    merged = trimesh.util.concatenate([to_trimesh(m) for m in parts])
    merged.export(f"out/plates/{name}.stl")
    return f"out/plates/{name}.3mf"


def make(part, fp_turn, lay, name, title, edge):
    parts, fps = plate(part, fp_turn, lay)
    export_plate(parts, name)
    draw(fps, title, f"out/plates/{name}.png", edge)
    summary(fps)
    return fps


if __name__ == "__main__":
    panels = []
    sfp = straight_fp()
    b = sfp.bounds
    print(f"straight footprint {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f}")
    n, pitch, flip, shift, lay = most(sfp, "straights", np.arange(60.0, 30, -0.25), np.arange(0, 21, 0.5))
    fps = make(T.straight(), 0.0, lay, f"plate_{n}_straights", f"{n} straights", EDGE)
    panels.append((fps, f"{n} straights", EDGE))

    cfp, ang = curve_fp()
    b = cfp.bounds
    print(f"curve footprint {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} (turned {ang:.2f} deg)")
    n, pitch, flip, shift, lay = most(cfp, "curves", np.arange(80.0, 30, -0.25), np.arange(-20, 21, 1.0))
    fps = make(T.curve(), ang, lay, f"plate_{n}_curves", f"{n} curves, nested", EDGE)
    panels.append((fps, f"{n} curves, nested", EDGE))

    # Tight: skirt and brim off, 2 mm gaps. Ascending pitches give the most compact layout.
    tight_pitches, tight_shifts = np.arange(38.0, 48.0, 0.05), np.arange(-28, 28.5, 0.5)
    r = best_rows(sfp, 5, tight_pitches, tight_shifts, gap=TIGHT_GAP, edge=TIGHT_EDGE)
    pitch, flip, shift, lay = r
    print(f"tight: 5 straights (pitch {pitch:.2f} mm, every other one {'turned 180 deg and ' if flip else ''}"
          f"shifted {shift:.1f} mm)")
    fps = make(T.straight(), 0.0, lay, "plate_5_straights_tight", "5 straights, tight (skirt off)", TIGHT_EDGE)
    panels.append((fps, "5 straights, tight (skirt off)", TIGHT_EDGE))
    r = best_rows(cfp, 5, tight_pitches, tight_shifts, gap=TIGHT_GAP, edge=TIGHT_EDGE)
    print("tight: 5 curves", "fit" if r else "do not fit")

    overview(panels, "out/plates/plates_overview.png")

    tfp = footprint(T.test_piece())
    b = tfp.bounds
    print(f"test piece footprint {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f}")
