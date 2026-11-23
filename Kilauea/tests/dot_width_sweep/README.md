# Receiver dot width sweep (Kilauea, densest inch)

Updated 2026-11-13 05:47 MST (result: 0.9 mm for Kilauea, 1.2 mm for hhh; terrain cut from 4x to 3x vertical exaggeration; 0.7 mm control dropped 21:09; 1.5 mm and up dropped 21:08)

The 0.7 mm dots on the hhh print snap off. This plate tests wider dots on the most crowded 1-inch patch of the Kilauea model, to find the widest dot that still reads as separate receivers.

- Patch: model x 67.5 to 92.9 mm, y 126.5 to 151.9 mm of `../../kilauea_190mm_4x_dots_v2_scale.stl` (SW corner E 259507, N 2148820, UTM 5). It holds 179 dots (stations within 0.1 mm merged): dense lines in the north and west, a regular grid in the south-east. Nearest-neighbor spacing is 0.16 mm minimum and 1.13 mm median.
- Terrain: taken from the model mesh with its dots removed and the gaps filled, on a 0.1 mm grid. The model is 4x vertical exaggeration (station elevations against model heights fit 4.14x); the tile relief is scaled by 3/4 to 3x (`ve_from`, `ve_to` in the config), with the lowest ground 5 mm above the bed (tile 5.0 to 11.7 mm terrain).
- Dots: same rule as the full model (top 1.2 mm above the highest terrain under the dot, 32 sides), at the station positions in `c14_station_meta.txt`. The model's own dots sit within 0.3 mm of them (median 0.01 mm).
- Tiles: 25.4 mm square, width cut 0.6 mm into the south wall (3 mm cap height). One row, 0.9, 1.1, 1.3 mm left to right, 12 mm apart. The first plate also had 1.5, 1.7, 2.0 and 2.3 mm (judged a no in the preview) and a 0.7 mm control (the current width, known to break); both dropped, stats kept below.

| width (mm) | dots touching a neighbor |
|---|---|
| 0.7 | 8% |
| 0.9 | 22% |
| 1.1 | 40% |
| 1.3 | 65% |
| 1.5 | 72% |
| 1.7 | 75% |
| 2.0 | 89% |
| 2.3 | 99% |

## Result (2026-11-13 05:47 MST)
Aaron picked 0.9 mm for the Kilauea model and 1.2 mm for hhh (stations 7 mm or more apart). Applied in `../../kilauea_190mm_4x_dots0p9_scale.stl` and `../../../WA_DNR/hhh_survey_dots1p2_vexag3_scale.stl`.

## Files
- `dot_width_sweep.py`, `config.json`: builds everything (`python dot_width_sweep.py`; needs numpy, scipy, trimesh, manifold3d, networkx, plus matplotlib and shapely for `../../../WA_DNR/add_wall_text.py`).
- `out/kilauea_dot_width_sweep_<w>mm.stl`: one tile per width. `out/kilauea_dot_width_sweep.3mf`: all 3 on one plate.
- `kilauea_dot_width_sweep_ve3_PLAplus_0.20mm_54m.gcode`: the 3x plate sliced with `../../../cli_slice/slice.sh relief ... --arrange 0` (the flag keeps the layout; without it Orca packs the tiles 2 mm apart and the brims fuse). 64 layers, 12.85 mm, 11.3 g, Klipper estimate 54 min with margin. Replaces the 4x slice (58 min).
