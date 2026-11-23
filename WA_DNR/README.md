# hhh survey relief model (WA DNR 3D survey, Columbia River valley)

Updated 2026-11-22 21:15 MST (citation and published-file note added; 2026-11-17 20:42 MST: array center lat/lon on the south wall; 0.9 mm dot version, brown PLA+, 20:38)

## Citation and published files
The receivers are the deployed stations of the WA DNR Horse Heaven Hills 3D survey. Please cite: Girard, A. J., D. H. R. O'Connell, A. Stolzmann, L. Florea, J. Shragge, M. Oristaglio, C. Morgan, J. Turner, R. Beal, A. Bauer, and S. P. Reidel (submitted). An active- and passive-source nodal seismic dataset for CO2 sequestration site characterization in the Columbia River Basalts of south-central Washington, U.S.A. *Seismological Research Letters*.

The public repo carries only the current print, `hhh_survey_dots0p9_vexag3_scale_latlon.stl`. The older STLs below are git-ignored; rebuild them with the commands given, starting from `py_generators/make_print.py` (needs the source files listed under Source data). Model and scripts are Apache-2.0.

## Source data
In ~/Dropbox/CSM_AARON/WA_COLUMBIA_RIVER_VALLEY/:
- DEM: `AGU2026/figure_build/inputs/merged_dem_timeslice.tif` (3 m lidar, EPSG:32611, UTM 11N)
- Receivers: `SRL_paper/figure_data/fig02/receivers_post_plot_deployed.csv` (150 post-plot stations, lat/lon)

## hhh_survey_vexag3.stl, recovered by fitting the STL to those files (Nov 2026)
- Horizontal: 1 mm = 29.42 m, no rotation. Model SW corner at E 268132, N 5092508 (UTM 11N); the model covers 5000 x 5590 m.
- Vertical: Z = 15 + (elev - 247.29 m) x 0.10196 mm/m. This is 3.000x exaggeration with a 15 mm base at the lowest ground (247.3 m), so the underside sits at about 100 m elevation. The highest ground (442.4 m) sits at 34.89 mm. Fit residual is 0.008 mm rms.
- Holes: 145 of the 150 stations. 1019, 1063, 1084, 1090 and 1148 are not on the model; none of them is in the 144-station with-data list. 1138 is on the model but not in that list.
- The 13 holes nearest the edges sat 0.65 to 2.32 mm inside their true station positions.

## Current print files (3x, raised dots)
- `hhh_survey_dots_vexag3_sealevel.stl`: underside = sea level (heights raised 10.214 mm). Thinnest 25.21 mm, tallest 45.10 mm terrain, 45.68 mm with dots.
- `hhh_survey_dots_vexag3.stl`: original 15 mm base (underside about 100 m). Tallest 35.46 mm with dots.
- Dots: 0.7 mm wide, 1.2 mm above the highest terrain under each, at the positions in `dots_true.csv`. The 13 edge dots were moved to their true station positions; 1046, 1103, 1126 and 1149 sit on the outline, so they are trimmed flush with the side wall.

## Scale text on the west wall (added 2026-11-11 22:55 MST)
- `hhh_survey_dots_vexag3_scale.stl`: the 15 mm-base model with "1:29,420" (1 mm = 29.42 m) recessed 0.8 mm into the long west wall segment, Arial Bold, 7 mm cap height, z 4 to 11 mm, centered on the segment.
- `hhh_survey_dots_vexag3_scale_PLAplus_0.20mm_9h13m.gcode`: that model sliced with `../cli_slice` (style `relief`) (PLA+ Olive Green, settings of the 2026-11-11 logo test plus gap fill everywhere and min_width_top_surface 500%). 177 layers, 35.45 mm, 208.4 g. The logo test ran 10% over its estimate, so expect about 10 h.
- The older G-code names are swapped: `hhh_SL_...gcode` is the 35.4 mm (15 mm base) model and `hhh_survey_dots_...gcode` the 45.6 mm sea-level one. Both were sliced on the Marlin `Sovol SV06 0.4 - park` preset; do not print them.

## 1.2 mm dots (added 2026-11-13 05:47 MST)
The 0.7 mm dots on the printed model snap off; 1.2 mm was chosen from the Kilauea dot width test (`../Kilauea/tests/dot_width_sweep`). The dots here are at least 7.3 mm apart, so wider dots never merge.
- `hhh_survey_dots1p2_vexag3.stl`: `stl_holes_to_dots.py py_generators/out/hhh_survey_vexag3.stl hhh_survey_dots1p2_vexag3.stl --dots dots_true.csv --dot_d 1.2`. The same command with `--dot_d 0.7` rebuilds `hhh_survey_dots_vexag3.stl` to within the hole-cap fill (about 33 mm3 differ, of 681,750 mm3). 145 dots, 1.2 mm above the highest terrain under each, edge dots trimmed flush (3.9 mm3). Tallest 35.51 mm.
- `hhh_survey_dots1p2_vexag3_scale.stl`: plus two centred lines on the long west wall segment, same font and 7 mm cap height as before: "1:29,420" at z 14.5 to 21.5 mm over "VE 3×" at z 4 to 11 mm (`add_wall_text.py ... --side west --zc 18`, then `--zc 7.5`). Wall top 29.6 to 31 mm along the text.
- `hhh_survey_dots1p2_vexag3_scale_PLAplus_0.20mm_7h39m.gcode`: sliced with `../cli_slice` (style `relief`). Same settings as the 9h13m slice except sparse infill adaptive cubic (the relief preset since 2026-11-12 20:42). 177 layers, 35.45 mm, 186.0 g, Klipper estimate 7h39m with margin. The 9h13m name was Orca's estimate, which runs low.

## 0.9 mm dots, brown (added 2026-11-17 20:38 MST)
Dots cut to 0.9 mm, the Kilauea width.
- `hhh_survey_dots0p9_vexag3.stl`: `stl_holes_to_dots.py py_generators/out/hhh_survey_vexag3.stl hhh_survey_dots0p9_vexag3.stl --dots dots_true.csv --dot_d 0.9`. 145 dots, 1.2 mm above the highest terrain under each, edge dots trimmed flush (1.6 mm3). Tallest 35.48 mm.
- `hhh_survey_dots0p9_vexag3_scale.stl`: same two west wall lines as the 1.2 mm version ("1:29,420" at `--zc 18`, "VE 3×" at `--zc 7.5`).
- `hhh_survey_dots0p9_vexag3_scale_PLAplus_brown_0.20mm_7h37m.gcode`: `FIL=filament_brown.json ../cli_slice/slice.sh relief ...`, so the relief settings with the PLA+ 2.0 preset renamed Brown (only name and colour differ from Olive Green). Adaptive cubic 15%, 177 layers, 185.9 g, Klipper estimate 7h37m with margin (Orca 6h27m).
- `hhh_survey_dots0p9_vexag3_scale_latlon.stl` (added 2026-11-17 20:42 MST): plus the array center on the long south (front) wall, which runs from the SW corner 109.7 mm east. Same font, cap height and layout as the west wall: `45°58'28"N` at z 14.5 to 21.5 mm over `119°57'38"W` at z 4 to 11 mm (`add_wall_text.py ... --side south --zc 18`, then `--zc 7.5`). Wall top 22.4 to 26.0 mm along the text. The center is the midpoint of the receiver extent in `receivers_post_plot_deployed.csv` (45.974354 N, 119.960650 W, rounded to whole seconds, about 30 m); the 145 on-model stations give the same point, and the station mean is 0.1 km east (45°58'28.0"N 119°57'33.2"W).
- `hhh_survey_dots0p9_vexag3_scale_latlon_PLAplus_brown_0.20mm_7h44m.gcode`: that model, same slice settings. 177 layers, 186.2 g, Klipper estimate 7h44m with margin (Orca 6h32m).

## Scripts
- `add_wall_text.py IN.stl OUT.stl --text "1:29,420" [--side west --cap 7 --depth 0.8 --zc 7.5]`: cuts recessed text into the longest footprint edge facing that side, reading correctly from outside.
- `stl_holes_to_dots.py IN.stl OUT.stl --dots dots_true.csv [--raise_mm 10.2143] [--ve_from 3 --ve_to 3]`: fills the holes, rescales exaggeration, optionally raises the terrain, and adds the dots, working from the STL alone.

## End G-code (Orca, Sovol SV06 ACE with Klipper END_PRINT)
```
G90
G1 Z{min(max_layer_z + 20, max_print_height)} F600
G1 X0 Y{print_bed_max[1]} F6000
END_PRINT
```
