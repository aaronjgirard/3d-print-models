# Command-line slicing (SV06 ACE, OrcaSlicer 2.5.0)

Updated 2026-11-17 20:38 MST (`FIL=` picks another filament file; `relief/filament_brown.json` added; G-code padded so Obico's percentage tracks time; relief infill now adaptive cubic 2026-11-12 20:42; `klipper_time.py` added 20:28; merged from `cli_slice_relief` and `cli_slice_tall_thin` 06:35 MST)

One folder per print style, each holding flat OrcaSlicer 2.5.0 presets (`printer.json`, `process.json`, `filament.json`) and the `overrides.json` applied when they are rebuilt. The files have to be flat because the 2.5.0 CLI cannot follow `inherits` into Orca's packed system presets.

```bash
./slice.sh relief    model.stl                 # slice, check, open the Orca preview
./slice.sh tall_thin project.3mf 3 out         # plate 3 of a 3MF, output to ./out
./slice.sh relief    model.stl 0 out --brim-width 8   # extra Orca flags beat the presets
OPEN=0 ./slice.sh relief model.stl             # skip the preview
PAD=0 ./slice.sh relief model.stl              # no progress padding (smaller file)
FIL=filament_brown.json ./slice.sh relief model.stl   # another filament file in the style folder
```
`slice.sh` checks the G-code for `START_PRINT`, `SET_VELOCITY_LIMIT`, `EXCLUDE_OBJECT`, a final `END_PRINT` and no `G28` at the end, prints the estimated time, and opens the file in OrcaSlicer's preview. It never uploads or starts a print. Output is `OUTDIR/plate_N.gcode` (N = 1 for an STL); rename it next to the model.

## Print time (`klipper_time.py`, added 2026-11-12 20:28 MST)
Orca's estimate runs 1.0 to 1.1x low on small prints and 1.3 to 1.4x low on big gyroid-filled ones, because it does not model Klipper's `minimum_cruise_ratio` or its cornering (`square_corner_velocity` 5, extruder corner velocity 1). `klipper_time.py` replays the G-code through Klipper's lookahead planner with the limits in `klipper_limits.json`; it matched four finished prints to within 1%. `slice.sh` runs it with `--write`, which replaces the `; estimated printing time` line (Orca's value is kept on the next line) and every `M73` line with the planner time plus the `margin` (5%), so Moonraker, the phone app and the printer screen count down from it. Name the renamed G-code with that time.
```bash
python3 klipper_time.py file.gcode --types            # estimate, with time per feature type
python3 klipper_time.py file.gcode --mcr 0.5          # what-if for another printer setting
```
Keep `klipper_limits.json` in step with printer.cfg (`mcr` is `minimum_cruise_ratio`).

## Progress padding (`--pad`, added 2026-11-13 09:36 MST)
Obico shows Klipper's file-position progress (`virtual_sdcard.progress`): moonraker-obico sends it as `progress.completion`, and the Obico server, web page and notifications display it unchanged, with no option to switch (checked in the moonraker-obico and obico-server source, 2026-11-13). The printer screen and Mainsail use the M73 lines, which are time based. On a relief the file runs far behind time, because the base is a few long infill moves and the dotted top is most of the bytes: the Kilauea print showed 8% in Obico at 28% of its time. `slice.sh` now runs `klipper_time.py --write --pad 0.5`, which inserts `;PAD ...` comment lines (250 bytes each, ignored by Klipper) after the move that ends each time step, so the file fraction stays within 0.5 percentage points of the elapsed time. Cost: the hhh relief grows from 26 to 38 MB, the 14 min ladder block from 2 to 7 MB (longer upload). Rerunning replaces the pad lines, `--pad 0` (or `PAD=0 ./slice.sh`) removes them, and the file minus the pad lines is byte-identical to the unpadded one.
```bash
python3 klipper_time.py file.gcode --write --pad 0.5  # pad an already sliced file
```

## Styles

**relief**: presets rebuilt from the config block of the CSM GP logo test print (`../CSM_GP_logos/logo_4in_and_banner_6in_PLAplus_0.20mm.gcode`, printed 2026-11-11, came out well apart from slightly rough tops): `Sovol SV06 ACE 0.4 nozzle`, `0.20mm Stepped relief @Sovol SV06 ACE`, `PLA+ 2.0 Olive Green @Sovol SV06 ACE`, High Temp Plate, 5 mm outer brim. `relief/overrides.json` changes from that print:
- sparse infill adaptive cubic instead of gyroid (added 2026-11-12 20:42 MST): same 15%, cuts the hhh relief from about 12.3 h to 7.2 h of real print time and 208 g to 186 g; not yet printed
- `filament_brown.json` (added 2026-11-17): the same PLA+ 2.0 preset named Brown with a brown colour; print settings identical
- gap fill `everywhere` (the logo's `nowhere` left the arrow centers hollow) and `min_width_top_surface` 500%
- end G-code that lifts 20 mm, parks at X0 and the back of the bed, then calls `END_PRINT`
- layer change G-code with `SET_PRINT_STATS_INFO TOTAL_LAYER` and `CURRENT_LAYER`, so Mainsail and `3dstatus` show the layer (added 2026-11-12)

**tall_thin**: Generic PLA on the High Temp plate with 0.15 mm layers, Avoid crossing walls on, travel 250 mm/s at 3000 mm/s², walls 80/120 and sparse infill 150 mm/s, accelerations 3000 (default, outer wall, top surface) and 2000 (inner wall), fan 80 to 100%, Z hop 0.6 mm, 15% gyroid, 3 Arachne walls, 10 mm outer brim, no supports, and the same lift-and-park end G-code (no `G28`).

## Rebuilding presets
```bash
python3 presets_from_gcode.py good_print.gcode --style relief   # from a G-code that printed well
python3 build_presets.py project.3mf --style tall_thin          # from a saved Orca project
```
Both write `STYLE/printer.json`, `process.json` and `filament.json` and apply `STYLE/overrides.json`. A new style name makes a new folder. `presets_from_gcode.py` takes key ownership and value types from the `tall_thin` presets (`--templates`); `build_presets.py` uses `keysets.json`, the key-to-preset map read from Orca's `Preset.cpp`. To confirm a slice matches its source print, diff the two G-code config blocks (only the override keys and host metadata should differ).
