# Spiky twisty sphere (3DMakerSpace), sliced for the SV06 ACE

Updated 2026-11-27 11:46 MST

A print-in-place twisty ball: 15 spiral segments, 0.5 mm apart, covered in prismatic spikes, flat at both
poles. It prints with supports. This folder holds the presets, the slicing and checking scripts and this
README. The model itself is not here.

- **Model:** "Spiky Sensory Trigger Twisty Spiral Fidget Sphere" by 3DMakerSpace,
  https://makerworld.com/models/2433410
- **Profile used:** the designer's main profile, "0.2mm layer, 2 walls, 15% infill" (full size, not the
  mini profile).
- **License:** Standard Digital File License. It does not allow sharing the files, so the downloaded 3MF,
  the plate and project 3MFs built from it, the G-code and the support picture stay local (`.gitignore`).
  Download the profile from MakerWorld and save it here as `spiky_twisty_sphere_makerworld.3mf` (the
  download is named `shapr3d_export_2026-02-22_00h05m.3mf`). The scripts and this README are mine,
  Apache-2.0.

## Status

- Nov 26 2026: sliced with the OrcaSlicer 2.5.0 command line on the Mac (its first use there), checked,
  and opened in OrcaSlicer in preview-only mode. Not printed yet. Nothing was sent to the printer.
- Nov 27 2026 11:44 MST: sliced a second time for HyperPLA+ (Aaron's choice of spool). Only the filament
  preset differs, by one value: Other layers nozzle temperature 220 instead of 210. Same toolpaths, same
  check results, opened in OrcaSlicer in preview-only mode. Not printed yet. Nothing was sent to the
  printer.

## The slice

Two slices, one per filament, each with its Orca project next to it (the ball with the designer's support
blocker, the presets below and the sliced plate):

- Basic PLA: `out/spiky_twisty_sphere.gcode` and `out/spiky_twisty_sphere.3mf`
- HyperPLA+: `out/spiky_twisty_sphere_HyperPLA.gcode` and `out/spiky_twisty_sphere_HyperPLA.3mf`

The numbers below are the same for both.

| | |
|---|---|
| Print time (Orca's estimate) | 10 h 32 min |
| Filament | 148.0 g |
| Layers | 383 (0.25 mm first layer, then 0.2 mm; top at 76.65 mm) |
| Ball | 82.9 x 82.7 mm across the spikes, 77.0 mm tall, 87.1 mm across the farthest spike tips |
| Position | centered on the bed at 110, 110 |

Orca's footer line says 385 layers because the model is 77.02 mm tall. The last two would only hold
spike tips too small to print, so the G-code has 383 layer changes.

Look at it before it goes to the printer: `open -a OrcaSlicer out/spiky_twisty_sphere.gcode` (or
`out/spiky_twisty_sphere_HyperPLA.gcode`) opens it in preview-only mode. Sending it is a separate step.

## Settings

Printer `Sovol SV06 ACE 0.4 nozzle`, filament `Generic PLA @Sovol SV06 ACE`, process
`0.20mm Standard @Sovol SV06 ACE`, `Bed type` (sidebar, under the printer) Smooth High Temp Plate, 0.4 mm
brass nozzle, basic PLA or HyperPLA+. Changes from those stock presets, with the stock value in
parentheses ("same" means the stock value already matches):

Filament, basic PLA (`Basic PLA @Sovol SV06 ACE`)

- `Filament settings > Filament > Print temperature > Nozzle`: First layer = 220 (235), Other layers = 210 (same)
- `Filament settings > Filament > Volumetric speed limitation > Max volumetric speed = 18` (21)
- `Filament settings > Cooling > Part cooling fan > Min fan speed threshold`: Fan speed = 80% (50%)
- `Filament settings > Cooling > Part cooling fan > Max fan speed threshold`: Fan speed = 100% (80%)

Filament, HyperPLA+ (`HyperPLA+ @Sovol SV06 ACE`): as basic PLA except

- `Filament settings > Filament > Print temperature > Nozzle`: First layer = 220 (235), Other layers = 220 (210)

The 220 on the other layers is the value of the Hyper PLA+ red marble run slice printed Nov 26 2026
(`Marble_Run/README.md`). The planter's HyperPLA+ preset (`mom-planter/`) has 225 on the first layer; 220
is kept here, the first layer value Aaron gave for this model. Untested on this model: if strings
between the spikes are heavy, try 210 on the other layers.

Process, standing changes

- `Process > Quality > Walls and surfaces > Top surface flow ratio = 1` (0.8)
- `Process > Strength > Infill > Sparse infill pattern = Gyroid` (Cross Hatch)
- `Process > Strength > Top/bottom shells`: Top shell layers = 5 (3), Top shell thickness = 1 (0.8),
  Bottom shell layers = 4 (3)
- `Process > Speed > Other layers speed`: Outer wall = 100 (200), Inner wall = 180 (270),
  Sparse infill = 200 (300), Internal solid infill = 180 (200), Top surface = 80 (200)
- `Process > Speed > Acceleration`: Normal printing = 5000 (10000), Outer wall = 3000 (6000),
  Inner wall = 5000 (8000), Top surface = 3000 (6000)
- `Process > Multimaterial > Prime tower > Enable = off` (on)

Process, this model

- `Process > Strength > Walls > Wall loops = 2` (same), as the designer
- `Process > Strength > Infill > Sparse infill density = 15%` (10%), as the designer
- `Process > Strength > Top/bottom shells`: Top surface pattern = Monotonic line (same),
  Bottom surface pattern = Monotonic (same)
- `Process > Others > Brim > Brim type = No-brim` (Auto). See "First layer" below.

Supports, carried over from the designer's 3MF

- `Process > Support > Support`: Enable support = on (off), Type = Tree (auto) (Normal (auto)),
  Style = Organic (Snug), Threshold angle = 30 (20), On build plate only = off (same),
  Support critical regions only = on (off), Ignore small overhangs = on (same)
- `Process > Support > Advanced`: Top Z distance = 0.26 (0.2), Bottom Z distance = 0.2 (same),
  Base pattern = Default (Rectilinear), Base pattern spacing = 2.5 (same), Top interface layers = 3 (2),
  Bottom interface layers = 2 (Same as top), Interface pattern = Rectilinear Interlaced (Default),
  Top interface spacing = 0.1 (0.5), Support/object XY distance = 0.35 (same),
  Support/object first layer gap = 0.5 (0.2; the designer also has 0.2, see "First layer" below)
- `Process > Support > Tree supports`: Tree support branch distance = 5 (1),
  Tree support branch diameter = 2 (same), Branch Diameter Angle = 5 (same),
  Tree support branch angle = 45 (40)
- `Process > Quality > Line width > Support = 0.42` (0.45)
- The designer's support blocker: one cube, 99.7 mm on a side, that covers the ball from 22.7 mm above
  the plate upward, so supports are only made under the lowest 22.7 mm. It is a part of the object in
  the 3MF and is carried into the plate and the project unchanged. There are no painted supports.

How the designer's values were read: `Metadata/project_settings.config` (Bambu Studio 2.5.0.66, a
Bambu Lab P1S profile) and `Metadata/model_settings.config`. Two names differ between the slicers.
Bambu's style `tree_organic` is `Organic` in Orca (Orca rejects the Bambu name and falls back to its
default). Bambu's organic trees read the plain branch angle, distance and diameter settings, while
Orca's read the ones whose keys end in `_organic`, so the designer's 45, 5 and 2 went into those. Support
speeds stay at the ACE stock values (80 mm/s; the designer's 150 is for the P1S).

### First layer: what differs from the designer and why

The check below found brim and support lines between the segments on the first layer, in three trial
slices:

1. Stock brim (Auto, Brim-object gap 0): brim lines ran down every 0.5 mm gap between the segments and
   would have joined them on the first layer.
2. The designer's brim (Outer brim only, 5 mm, Brim-object gap 0.2): the radial gaps came out clear, but
   brim rings filled the hole on the axis, and brim and support lines sat in slots under 1 mm wide between
   a segment and its neighbor's spike tips (216 sampled points).
3. Brim off and `Support/object first layer gap = 0.5`, the clearance the segments have from each other:
   nothing in the gaps. This is the slice above. The support's first layer surrounds the base of the
   ball anyway, so the brim was adding little.

Untested on the SV06 ACE: all of it. The support values are the designer's and were made for a Bambu
P1S. Brim off and the 0.5 mm first layer gap are my changes and have not been printed by anyone.

## Checks

`python slice/check.py` reads the G-code and the plate 3MF and writes
`out/spiky_twisty_sphere_supports.png`. All pass on both slices, with the same numbers (the HyperPLA+
slice has the same toolpaths; its picture is `out/spiky_twisty_sphere_HyperPLA_supports.png`).

G-code (this is how we know the ACE preset was used):

- `START_PRINT` once, before any move. It is preceded only by the object definition and the bed heating.
- `END_PRINT` is the last command.
- No `G28`.
- `SET_VELOCITY_LIMIT` lines: 176512. `EXCLUDE_OBJECT` lines: 1 define, 383 start, 383 end.

Supports, from the support moves in the G-code against the mesh:

- They stop below the blocker: highest support move at 20.85 mm, blocker from 22.70 mm.
- Every support island stands on the plate (5 islands, none starts above the first layer), and no
  support rests on the ball (0 of 716750 sampled points have ball material within 2 layers below).
- No support in a gap between segments: 0 sampled points lie in a slot up to 1 mm wide between two
  different segments (the gaps are 0.5 mm). 4555 points lie in wider slots, up to 2 mm, between the spike
  tips of neighboring segments near the plate; those are under the ball, not in the gaps.
- No brim in a gap (there is no brim).
- No support inside the ball, and all of it under the ball: the farthest support move is 39.3 mm from
  the axis, the ball reaches 41.7 mm.

The picture shows a side view, a vertical cut through the axis, a plan view and three layers (0.25,
2.05 and 8.05 mm) with the gaps marked. The trees stand in a ring on the plate and lean in under the ball.

## After printing

1. Let the bed cool, then take the ball off.
2. Take the supports off slowly, a tree at a time, so the spike tips survive. The first layer of the
   supports is one sheet around the base, 0.5 mm clear of it.
3. Then twist the segments free.

## Rebuild

```
conda activate marble-run                           # numpy, trimesh, shapely, scipy, matplotlib
python slice/fetch_profiles.py slice/stock          # stock SV06 ACE presets, flattened
python slice/make_presets.py                        # machine.json, process.json, filament.json
python slice/plate.py                               # plate 3MF, then out/*.gcode and out/*.3mf
python slice/check.py                               # the checks and the picture
open -a OrcaSlicer out/spiky_twisty_sphere.gcode    # look at it, preview-only mode
```

The same for HyperPLA+ (`make_presets.py` writes basic PLA unless told otherwise):

```
name=spiky_twisty_sphere_HyperPLA
python slice/make_presets.py --filament hyper_pla
python slice/plate.py --name $name
python slice/check.py --gcode out/$name.gcode --plate slice/plate/${name}_plate.3mf --fig out/${name}_supports.png
open -a OrcaSlicer out/$name.gcode
```

Notes on the OrcaSlicer 2.5.0 command line on the Mac
(`/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer`), first used Nov 26 2026:

- It works. A slice of this model takes about 10 s.
- The stock presets inside the app are packed (`Resources/profiles/Sovol.opc`), so `fetch_profiles.py`
  still takes them from the OrcaSlicer v2.5.0 source.
- A 3MF without printer settings is treated as laid out on a 200 mm bed, and its objects are moved by
  the difference to the real bed center. `plate.py` writes the object at 100, 100 and refuses the slice
  unless the G-code has it at 110, 110.
- The designer painted every face "filament 3". `plate.py` clears that, so the print uses one filament
  and the G-code has no tool change.

## Files

- `slice/fetch_profiles.py`: fetches and flattens the stock presets (as in `train-connectors/slice/`).
- `slice/make_presets.py`: the changes above, with the stock values in comments. Writes the three preset
  files for the filament named by `--filament` (`basic_pla` or `hyper_pla`) and `changes_from_stock.json`
  (the process changes and both filaments).
- `slice/plate.py`: builds the plate 3MF from the designer's 3MF (moved to the 220 mm bed, filament paint
  cleared, Bambu project settings left out; mesh, size and support blocker untouched) and slices it.
- `slice/check.py`: the checks and the picture.
- Local only: `spiky_twisty_sphere_makerworld.3mf`, `slice/plate/`, `slice/stock/`, the preset JSON files
  and `out/`.
