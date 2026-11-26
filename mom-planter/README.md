# I ♥ MOM planter (Thanksgiving 2026)

Updated 2026-11-26 12:59 MST

A 4 inch planter with arms and print-in-place legs.
The front carries a raised "I ♥ / MOM" (letters painted black, heart red), the back an inset "From / Vlad &
Dad" (painted white), and the bottom "THANKSGIVING / 2026", made only by the toolpaths of the bottom layers.
Blue HyperPLA+. Everything is generated in `planter.py`.

## Status

- Designed, checked in code and sliced (Nov 26 2026); not printed yet.
- Nov 26: the hands were swapped (thumbs pointed away from the pot); fixed, both thumbs now point in
  toward the pot, as for hands lying palm down.
- Aaron's picks: front Courier Prime Bold (I♥NY layout, "I ♥" over "MOM"); back Sriracha; bottom Courier
  Prime Bold in two straight lines.
- Sliced: `out/package/mom_planter_HyperPLA.3mf` (Orca project with the modifier, sliced) and `.gcode`:
  3 h 50 min, 115.8 g, 440 layers, High Temp Plate. Starts with `START_PRINT`, ends with `END_PRINT`, no `G28`.

## Design

- Pot: 101.6 OD at the rim (4.0 in), tapering to 93.0 at the base line, 88 tall, 2.6 wall, 2.25 floor (6
  bottom + 5 top layers, all solid). Bottom edge: 5 mm round whose lowest part is a 45 degree chamfer, so
  nothing overhangs; flat bottom face 87.6 across. Inside: 88 across at the floor, 96 at the rim, 85.75
  deep. No drainage hole: it is a cachepot, and the bottom text is there.
- Front: Courier Prime Bold, capital height 16 (MOM 49 wide); heart 21.6 wide; all 1.6 proud of the wall.
- Back: Sriracha, "Vlad & Dad" 72 wide, "From" at 0.8 of that size, cut 1.0 deep (1.6 of wall behind).
- Bottom text: Courier Prime Bold, capitals 6.15 and 9.8, inside a 39 radius. It is mirrored in the model so
  it reads with the pot upside down and the heart facing you ("THANKSGIVING" on the back half; turned 180
  degrees on Nov 26 at Aaron's request). A modifier
  volume (z 0 to 1.25, the 6 bottom layers) sets Bottom surface pattern and Internal solid infill pattern to
  Concentric; the rest of the bottom stays Monotonic lines at 45 degrees, so the letters show as loops that
  follow their outlines against straight lines. Modifier regions differ only in fill, so Orca merges their
  perimeters and the letters get no outline walls (`Layer::is_perimeter_compatible` in Orca 2.5.0).
- Arms: sphere-hull tubes 8.2 to 7.0 thick from shoulders at +-82 degrees, 36 high, to hands flat on the bed
  (3.6 thick, top edge rounded). The arms slope at least 55 degrees, so no supports.
- Legs: centered at x = +-19, 13 wide, 9 tall, three links on hinges 14 apart; feet 18 x 20 x 6. The hip
  axis is 49.5 in front of the pot's axis, 5.6 past the edge of the bottom face, so hanging legs clear a
  shelf edge. Hinges: knuckle radius 4.5, 0.55 radial and 0.45 side clearance, 45 degree cone pins (2.2 base,
  1.5 long) in cone sockets with 0.40 clearance. A 90 degree V notch under each hinge lets the leg bend
  90 degrees down and stop there; it bends about 60 degrees up. The clearance faces over the knuckles have 45
  degree teardrop roofs, so no ceiling hangs over a knuckle.

## Checks (`check.py`, `gcode_check.py`)

- Pot and all six links are single closed solids. Clearance at rest is 0.403 at minimum (the cone pins).
- Each hinge swept from 60 degrees up to 90 down: clearance stays 0.40 from 30 up to 85 down; the parts
  touch only at the 90 degree stop and at about 60 up.
- Sliced G-code: the letters are concentric loops in all 6 bottom layers; at the hinge axis height the links
  are separate islands.

## Print

Sliced with the OrcaSlicer 2.5.0 command line from the stock SV06 ACE presets (`slice/`). Changes, stock in
parentheses:

- Filament `HyperPLA+ @Sovol SV06 ACE` from `Generic PLA @Sovol SV06 ACE`: nozzle 225 first layer, 220
  other layers (235, 210); fan 80 / 100 % (50 / 80).
- Process from `0.20mm Standard @Sovol SV06 ACE`: Wall loops 6 (2, the wall is all perimeters); Top shell
  layers 5, thickness 1 (3, 0.8); Bottom shell layers 6 (3); Bottom surface pattern Monotonic (stock;
  straight lines read best behind the loops, better than Archimedean Chords here); Sparse infill Gyroid 15 %
  (Cross Hatch 10 %); Top surface flow ratio 1 (0.8); Elephant foot compensation 0.15 (0.1, keeps the
  hinge gaps open on the first layer); speeds 100 / 180 / 200 / 180 / 80 for outer wall, inner wall, sparse,
  internal solid, top (200 / 270 / 300 / 200 / 200); accelerations 5000 / 3000 / 5000 / 3000 (10000 / 6000
  / 8000 / 6000); Brim No-brim (Auto: a brim would bridge the hinge gaps); Skirt loops 1 (0); Prime tower off.
- Modifier "bottom text THANKSGIVING 2026": Bottom surface pattern Concentric, Internal solid infill pattern
  Concentric.
- Plate: High Temp Plate (smooth PEI). The bottom text shows as a change in sheen, best on the smooth side.

After printing, bend each leg joint up and down a few times to free it. Paint: raised front tops with a small
brush; for the inset back letters, fill the cuts with white and wipe the surface with a damp towel before
it dries.

## Rebuild

```
pip install manifold3d trimesh uharfbuzz fonttools pyvista vtk matplotlib
python3 planter.py && python3 check.py && python3 export.py && python3 render.py
python3 slice/fetch_profiles.py slice/stock && python3 slice/make_presets.py slice/stock slice
python3 slice/build_3mf.py /path/to/OrcaSlicer/AppRun && python3 gcode_check.py
```

Fonts (from google/fonts, SIL Open Font License) are in `fonts/`: `CourierPrime-Bold.ttf`, `Sriracha-Regular.ttf`.
Each font's license text is next to it (`OFL-CourierPrime.txt`, `OFL-Sriracha.txt`); the fonts are not Apache-2.0.
`build_3mf.py` loads the three STLs with `--assemble` (one object, three parts), turns part 3 into a
`modifier_part` with its settings in `Metadata/model_settings.config`, and slices the result.

## Files

Local folder `~/3d-print-models/mom-planter`:

- `planter.py` (all geometry), `text2d.py` (HarfBuzz-shaped text to 2D), `check.py`, `export.py` (STLs on
  the bed), `render.py` (painted previews), `gcode_check.py` (toolpath plots), `fonts/`.
- `slice/`: `fetch_profiles.py`, `make_presets.py`, `build_3mf.py`, and the presets they wrote
  (`machine.json`, `process.json`, `filament.json`, `changes_from_stock.json`).
- `out/package/`: `mom_planter_HyperPLA.3mf` (sliced Orca project) and `mom_planter_HyperPLA.gcode`.
- `out/stl/`: `planter_pot.stl`, `planter_legs.stl`, `bottom_text_modifier.stl` in print position.
- `out/renders/`: `front.png`, `back.png`, `shelf.png`, `bottom_view_sim.png`, `gcode_layers.png`, and
  `font_options/` (the sheets the fonts were picked from).

Not in the repository (`.gitignore`): the sliced `out/package/mom_planter_HyperPLA.3mf` and `.gcode` (`slice/build_3mf.py` rebuilds them), `out/stl/shift.npy`
(`export.py`), and the preset files `slice/machine.json`, `process.json` and `filament.json`
(`slice/make_presets.py`).

The claude.ai "3D printing" project holds the README and scripts under `mom-planter/` (no print files,
fonts or images). When one copy changes, update the other.
