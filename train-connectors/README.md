# Train coupler (kingpin, swivel and hinged hook arm), version 2, and the tender's clip-on loop

Updated 2026-11-25 23:16 MST

Replacement for the red hook that couples the battery Christmas-train cars. Every car has a black tab with
a hole at its front and a black loop at its back; the hook on each car's tab reaches forward into the loop
of the car ahead (the tender's hook goes into the engine's loop). The original broke twice at the corner
above its drop leg. Version 2 is three printed parts per coupler plus two short pieces of 1.75 mm filament,
and it couples to the original loops on the cars and on the engine. Everything is generated in `coupler.py`.

## Brief and status

- Aaron's brief (Nov 23 2026): a better hook and clamp, like a real train connector, that gets stronger as
  it is pulled and has a little joint; PETG or ABS; two of them. All cars are the same.
- Version 1 (Nov 24, files in `v1/`) was printed in PETG and fitted. The clamp held well on the cars.
  Four things to fix (Aaron, Nov 25): the 7.6 mm wide arm barely fit the cars' 10 mm loop opening and did
  not fit the engine's 6.2 mm one; the snap peg (printed 4.1 x 2.5) was loose in the tab hole, which
  measures 4.7 x 5.3, and did not hold; one side of the arm's hinge hole, in the upper cheek that bridged
  the slot, was jammed with PETG strings and needed cutting out; and the hook should be longer, "like a
  2mm straight bar down THEN the same hook we already have".
- Version 2 (Nov 25): designed and checked in code; the plate below was printed in black PLA on Nov 25.
  After that print Aaron asked for the kingpins "1 or 2 layers taller": `KP_EXTRA` (0.4, two layers)
  lowers the lock hole and the tip, so the kingpin is 9.5 long and the lock filament sits 0.55 under the
  swivel (was 9.1 and 0.15). Two of the longer kingpins were printed on their own the same night.
- Tender's clip-on loop (Nov 25, see its section below): designed and checked in code; printed on the plate
  Nov 25. Its snap-off wall became a U under both side rails as well (see Printing in its section).
- Both are on one black PLA plate, sliced with a 3 mm brim (`out/package/black_pla_plate.gcode`, about
  17 minutes in Orca, 3.6 g; the G-code and the sliced `.3mf` are not committed, `slice/plate.py` rebuilds them).
- Next: print the plate, fit a coupler to the tender and couple it to the engine and to a car, fit the
  loop to the tender, and report back.

## What changed from version 1

- **Kingpin from the top** replaces the snap peg. Its flat head sits on the tab between the tab's two
  ridges, its round 4.55 shaft goes down through the hole and the swivel, and a piece of filament across
  its tip, under the swivel, locks it. Aaron offered the top entry ("the pin could enter the car from the
  top"); it holds by the head and the lock rather than by barbs, and the round shaft prints upright, so it
  stays round.
- **The fork moved to the swivel.** The swivel now carries two cheeks and the arm is a plain bar between
  them. The swivel prints plate down with teardrop hinge holes and the arm prints on its side, so nothing
  bridges and nothing strings across a hole.
- **Arm 4.0 wide** (was 7.6) with 1.5 mm chamfers on its front corners seen from above, so the leg goes
  into the engine's 6.2 mm opening, including on curves.
- **Leg 2 mm longer, straight below the hook.** Aaron asked for a 2 mm straight bar first, then the same
  hook. A straight part above the hook would hold the loop's 1.5 mm end bar against a vertical face, so the
  pull would no longer press it up into the arm's underside: the clamp would turn into a plain catch. The
  extra 2 mm went below the hook instead, so the hook and clamp are unchanged and the leg reaches 2 mm
  deeper under the bar (it has to be lifted about 33 degrees to come out of a car's loop, was 25).
- **Droop stop at -20 degrees** (was -15): the engine's loop sits 2 mm lower than the cars', and the arm
  rests on it at about -10.
- **Hinge holes swapped**: the cheeks have 2.3 teardrop holes that grip the pin (like v1's 2.3 arm holes),
  the arm has a 2.6 hole that turns on it (like v1's 2.6 knuckle hole).

## Where things are

- Local folder `~/3d-print-models/train-connectors`: this README, the four scripts, print files in
  `out/package`, renders in `out/renders`, source photos in `photos/`, version 1 in `v1/`.
- The claude.ai "3D printing" project holds the README and scripts under `train-coupler/` (text only, no
  print files or photos; version 1 is only in the local `v1/`). When one copy changes, update the other.
- The printed track is in `train-track/` in the project (`~/3d-print-models/train-rails` locally). Its
  curves are 412.3 mm radius at the centerline (from Nov 24), rail tops 7.0 above the table.

## Conventions

x along the track from the tab hole toward the car ahead, y across, z up from the table with both cars on
the track; mm. Angles of the arm are about the hinge, positive lifting the leg.

## How it works

- **Kingpin** (sky blue in the renders): dropped in from the top. The head is 6.6 long, so it rests on the
  tab past both ends of the 4.7 hole, and it sits lengthwise between the ridges, which keep it from
  spinning (it can turn about 10 degrees before touching one).
- **Swivel** (blue): a 3 mm plate under the tab that turns on the kingpin, so the coupler follows curves.
  In front of the tab's tip it has two cheeks that carry the hinge pin. It hangs 0.15 under the tab and
  0.55 above the lock filament (`KP_EXTRA` 0.4 more than the 0.15 `CLR_V`).
- **Arm** (violet): hinged between the cheeks by a filament pin. Its flat underside rests on the loop
  ahead and its leg drops through the loop's opening. The back face of the leg is raked 30 degrees, so
  when the train pulls, the loop's end bar is drawn into the throat and clamped between the arm's underside
  and the raked face, harder the harder it pulls. Below the rake the leg runs 2 mm straight down.
- On a car's loop the arm sits level, the clamp is about 0.6 times the pull, and the hinge is level with the
  pull, so pulling puts almost no vertical force on either car (about 0.01 times the pull). On the engine's
  loop, which is 2 mm lower and 2.0 thick, the arm settles about 10 degrees down; the clamp is about 0.5
  times the pull, and the pull lifts the engine's back end with about 0.24 times the pull (and presses the
  tender's front down as much). A toy train pulls with a newton or two, so this is a few tenths of a
  newton; the engine's weight on its back wheels is much more.
- The arm rides up and down with the loop, which keeps the clamp seated over track joints and uneven
  floors; uncoupled, it rests on a stop 20 degrees down.
- **Couple**: lift the arm, set the leg into the opening, let go, then pull the cars apart a little.
  **Uncouple**: push the cars about 2 mm together and lift the arm about 35 degrees from where it rests.
- Why the original broke: a rod about 2.7 mm thick that rises about 13 mm and drops about 18 mm, so every
  pull bent the corner above the leg. The arm is 4.0 x 3.5 mm in section, the pull runs nearly straight
  through it, and it prints on its side, so no layer line crosses the bend.

## Measured on the cars and engine (cars on the track)

| Feature | mm | When |
|---|---|---|
| Tab: hole along the track x across | 4.7 x 5.3 (rounded ends) | Nov 25 (the 4.5 of Nov 23 was one reading) |
| Tab: thickness at the hole, top above the table | 1.5, 27.0 | Nov 23 |
| Tab: width, reach past the hole center, whole length | 16, 6, 14.5 | Nov 23, Nov 25 |
| Tab: ridges on top, their top above the tab's underside | 4.0 | Nov 25 |
| Tab: ridges run 11 of the tab's 14.5 mm (taken as from the root, ending 3.5 short of the tip) | 11 | Nov 25 |
| Car's loop: opening along the track x across | 7.5 x 10 | Nov 23 |
| Car's loop: width, thickness, top above the table, sticks out from the end wall | 16, 1.5, 27.5, 12 | Nov 23 |
| Engine's loop: opening along the track x across | 9.5 x 6.2 | Nov 25 |
| Engine's loop: thickness, top above the table | 2.0, 25.5 | Nov 25 |
| Printed v1 peg (modeled 4.2 x 2.4, printed on its side) | 4.1 x 2.5 | Nov 25 |

## Measurement 9 (spacing), not taken

`X_I` is the distance from the tab hole center to a car loop's end-bar inner edge when the train pulls. It
sets only the gap between cars. It is 22.0, from the glued original (its leg sits 22 to 24 mm past the hole
in photos 06 and 07); version 1 used the same value and Aaron reported no trouble with the spacing. On the
engine the bar seats 0.6 closer (21.4), because the arm droops onto the lower loop.

To measure, if the cars ever touch on curves: hooks off, both cars on a curve, pushed together until
something touches; distance from the tab hole center to the center of the loop's opening (call it d9; a
ruler is fine). Then set `X_I = d9 + 2`. Pulling, a car loop's opening center sits at `X_I + 3.75`; pushed
fully together the leg travels 3.65 mm and brings it to `X_I + 0.1`, so `d9 + 2` keeps about 2 mm before
anything touches on a curve even when pushed. Then re-run `check.py`, `export.py` and `render.py`.

## Assumed

| Value | mm | Source |
|---|---|---|
| `END_BAR`, loop end bar along the track, both loops | 2.25 | opening assumed centered; only shifts the gap |
| Tab and car loop ends | half round across 16 | photos 01 and 05 |
| `RIDGE_IN`, ridges' inner faces from the middle | 2.65 (5.3 apart) | photo 06 read about 5.2 apart; the head is 4.55 wide |
| Engine's loop: width, sticks out | 14, 14 | not measured; used only by the checks |

## The original hook (from the photos)

Red rod about 2.7 mm thick. A plate under the tab carries a split snap peg up through the hole, with barbs
front and back about 5.8 mm across and 3.5 mm above the tab. About 11 mm past the hole a riser climbs about
13 mm, a top bar runs about 12 mm, and a drop leg falls about 18 mm to a hook about 3.7 mm long pointing back
toward its own car. Its leg sat 22 to 24 mm past the hole (photo 06 gives 21.8, photo 07 gives 24.3). The top
bar cleared the loop by about 6 mm and the hook hung about 5 mm under it, so it was a loose catch rather than
a clamp. It broke at the corner between the top bar and the drop leg, twice. All of this is read off photos,
about 10 % either way.

## Printed values and clearances

| Feature | Value |
|---|---|
| Kingpin shaft | 4.55 round in the 4.7 x 5.3 hole: 0.075 a side along the track, 0.375 across |
| Kingpin head | 6.6 x 4.55 x 1.2, rests on the tab 0.95 past each end of the hole; top 28.2, under the ridges' 29.5 |
| Kingpin length, tip | 9.5; tip 18.7 above the table |
| Lock | 2.2 teardrop hole across the kingpin, point toward the tip; the filament sits in the point, 0.55 under the swivel; its ends are bent down, clear of the swivel |
| Swivel plate | 3.0 thick (22.35 to 25.35 above the table), 0.15 under the tab; 5.1 bearing on the 4.55 shaft |
| Cheeks | 2.0 thick, 2.3 to 4.3 either side of the middle; 2.3 teardrop holes (grip the pin) |
| Hinge | axis 9.5 past the hole center, 26.5 above the table |
| Arm | 4.0 wide, 0.3 to each cheek, 1.5 mm 45 degree chamfers on the front corners seen from above; 2.6 hole (turns on the pin) |
| Arm section | underside 27.5, top 31.0; leg 3.0 thick at the loop's top, raked 30 degrees behind down to 23.0, then straight to 21.0; front face vertical, so pushing does not lift it |
| Arm travel | stop at -20 degrees to +45 checked; it lifts to about 82 before touching the tab |
| Pushing | 3.65 mm on a car's loop, 5.0 on the engine's, before the leg meets the far side of the opening |

## Things that move together (when changing the model)

- `X_I` moves only the leg, so it changes only the gap between the cars.
- The droop stop is the swivel's tongue (`TONGUE_X`) meeting the arm's lug (`LUG_X`, `LUG_Z0`). The lug's
  underside is the swivel's middle profile swept from `SWEEP_DOWN` (-15.75 degrees) to `PHI_UP` (45) plus
  `SWEEP_CLR` (0.3); that clearance adds about 4.25 degrees, which puts the stop at -20. Changing any of
  these, or the hinge, moves the stop: re-run `check.py` and retune `SWEEP_DOWN`.
- `KZ` (26.5) sits 0.5 above a car loop bar's bottom inner corner (`LOOP_TOP - LOOP_T` = 26.0), which is what
  makes pulling on a car put almost no vertical force on either car. If `LOOP_TOP` changes, move `KZ` with it.
- `ARM_W` sets the cheeks (`CHEEK_Y0`, `CHEEK_Y1` = `ARM_W / 2 + 0.3` and 2.0 more) and the swivel's width;
  `PLATE_R` (4.3) matches `CHEEK_Y1`. The engine-loop curve checks depend on `ARM_W` and `ARM_CHAMFER`.
- The kingpin's lock follows the swivel: `LOCK_PIN_Z` is `CLR_V + KP_EXTRA` (0.55) under `SW_Z0`, `LOCK_Z` puts the 2.2 hole's
  point under the filament, and `KP_Z0` leaves 1.0 below the point. The swivel's top follows `TAB_TOP`,
  `TAB_T` and `CLR_V`.
- Hole sizes allow for this printer printing holes small (his marble-run fit test came out 0.3 to 0.6 mm
  small on bores with X-Y hole compensation 0.1; v1's 2.3 arm hole gripped the filament and its 2.6 hole let
  it turn). Keep hole compensation at 0.1 with these sizes.

## Checks (`check.py`, Nov 25 2026, in code; about 6 minutes)

- All three parts are single closed solids.
- Kingpin clears the tab, its head rests on the tab, and it touches a ridge if turned 10 degrees. The swivel
  turns on it without touching; the lock filament passes through it 0.55 under the swivel; the swivel has
  0.15 of play up to the tab and 0.55 down to the lock.
- Swivel clears the tab turned up to 25 degrees (first touches at 64.5). Arm clears the swivel over its
  travel and meets the stop at -20 degrees; arm clears the tab and kingpin at every angle, turned up to 25.
- Car's loop: seated level; clamp 0.59 times the pull, vertical -0.01. Pushing travel 3.65. With 1.8 mm or
  more of slack the arm lifts out cleanly; the leg is 0.3 over the loop at 33.3 degrees. Coupling with the
  loop 3 mm low to 3 mm high, and turned 15 degrees either way, the arm settles and the pull seats the bar
  on the raked face. Running onto a curve (loop -1, 0, +2 mm; turned 15 degrees either way and 20) keeps it
  seated, with the leg up to 1 mm off center in the opening.
- Engine's loop: seated at -9.6 degrees; clamp 0.52, vertical +0.24 (lifts the engine). Pushing travel 5.0.
  With 1.8 mm or more of slack the arm lifts out; the leg is 0.3 over the loop at 23.9 degrees. Coupling
  with the loop 2 mm low to 3 mm high (at 2 mm low the arm is on its stop, still caught on the raked face),
  and turned 15 degrees either way with the leg 0.5 off center; running onto a curve as for the cars.
- Loops turn about their end bar's inner edge (a loop held by the pull turns about where its bar sits),
  and the leg may sit up to 1 mm off center: the coupler turning 2.6 degrees on its kingpin moves the leg
  1 mm across.

## Print

**Filament: black PLA** (Aaron's choice, Nov 25, to match the train). Version 2 has nothing that has to
flex (v1's snap peg did), so PLA works. It is stiffer than PETG but brittle: under a hard yank the hook
or a cheek would crack where PETG would bend. PETG is the fallback if one breaks; both cost about
$20/kg and the plate uses about 2 g. **Nozzle**: 0.4 mm brass.

`python3 slice/plate.py <OrcaSlicer binary>` slices the plate to `out/package/black_pla_plate.gcode` (both
coupler sets and the tender's loop, 3 mm brim, 16 min 40 s and 3.6 g by Orca's estimate, 47 layers; not
committed, like all G-code here), sliced with the OrcaSlicer 2.5.0 command line from
the stock SV06 ACE presets with the changes below (`slice/`, see Rebuild). It starts with `START_PRINT`,
ends with `END_PRINT` and has no `G28`. Open it in OrcaSlicer to look at it before sending it to the
printer: `open -a OrcaSlicer black_pla_plate.gcode` (it opens in preview-only mode).
`black_pla_plate.3mf` is the Orca project: same layout, the presets below, and the sliced plate (it carries the G-code, so it is not committed either).

To slice it in the Orca app instead: printer `Sovol SV06 ACE 0.4 nozzle`, filament `Generic PLA @Sovol
SV06 ACE`, process `0.20mm Standard @Sovol SV06 ACE`, plate type High Temp Plate, then (stock in
parentheses):

- `Filament > Print temperature > Nozzle`: First layer 220 (235), Other layers 210 (stock)
- `Filament > Volumetric speed limitation > Max volumetric speed = 18` (21)
- `Cooling > Part cooling fan`: Min fan speed threshold fan speed 80% (50%); Max fan speed threshold fan
  speed 100% (80%), layer time 8 s (6; the kingpins' top layers print alone and are tiny)
- `Strength > Walls > Wall loops = 4` (2)
- `Strength > Infill`: Sparse infill density 40% (10%), Sparse infill pattern Gyroid (Cross Hatch)
- `Strength > Top/bottom shells`: Top shell layers 5, Top shell thickness 1 (3, 0.8); Bottom shell layers
  4 (3). Top and bottom patterns stay Monotonic line and Monotonic: on parts 4 to 9 mm across, Archimedean
  Chords only makes fragments.
- `Quality > Precision`: X-Y hole compensation 0.1 (0; the hole sizes count on it), X-Y contour
  compensation 0 (stock), Elephant foot compensation 0.15 (0.1); Precise wall stays on
- `Quality > Walls and surfaces`: Avoid crossing walls on (off), Top surface flow ratio 1 (0.8)
- `Speed > Other layers speed`: Outer wall 100 (200), Inner wall 180 (270), Sparse infill 200 (300),
  Internal solid infill 180 (200), Top surface 80 (200)
- `Speed > Acceleration`: Normal printing 5000 (10000), Outer wall 3000 (6000), Inner wall 5000 (8000),
  Top surface 3000 (6000)
- `Others > Brim > Brim type = Outer brim only, Brim width = 3` (Auto, 5); `Others > Skirt > Skirt loops = 1` (0)
- `Multimaterial > Prime tower > Enable` off (on)

For PETG instead: filament `Generic PETG @Sovol SV06 ACE`, nozzle 245 / 240 (260 / 245), bed 80 (85), max
volumetric speed 12 (15), no cooling for the first 3 layers, fan 30 / 60% (30 / 30), retraction 1.0 (0.8);
same process.

Wipe the nozzle tip before printing (it is the bed probe). These values are starting points; the PLA ones
are what the track printed well with.

Files (`out/package`), in print orientation: `black_pla_plate.gcode` and `.3mf` (the plate, with the
tender's loop),
`coupler_plate_2_sets.3mf` (two arms on their side, two swivels plate down, two kingpins head down),
`coupler_arm.3mf`, `coupler_swivel.3mf`, `coupler_kingpin.3mf`, and STLs of the parts in `stl/`.

## Assembly

1. Take off the v1 coupler and anything left of the old hook in the tab hole.
2. Hinge: set the arm's round end between the swivel's cheeks, hook pointing away from the swivel's round
   end, and line up the holes. Push a piece of filament through cheek, arm and cheek. Trim it about 0.5 mm
   proud of each cheek and mushroom both ends with the soldering iron. The arm should swing freely.
3. Hold the swivel under the tab, its round hole under the tab's hole and the hinge toward the tab's tip.
4. From the top, drop the kingpin through the tab hole and the swivel, head lengthwise between the ridges,
   so the small hole near its tip runs across the track.
5. Push a 10 mm piece of filament through that small hole, under the swivel, so it sticks out about the
   same on both sides. Warm each end with the soldering iron and bend it down. Bend rather than mushroom
   these ends: a mushroom would catch the swivel's underside as it turns.
6. The swivel should turn freely under the tab. Lift the arm and let it fall: it should swing freely and
   stop about 20 degrees down.

## Fit test

Print one set first and fit it to the tender.

- Kingpin will not go through the tab or the swivel: open the swivel's hole with a 3/16" or 5 mm drill
  turned by hand, or sand the shaft. It should drop through both.
- Kingpin head does not sit flat between the ridges: sand the head's long sides (4.55 wide; the ridges were
  taken as 5.3 apart from a photo).
- Lock filament will not go through the kingpin: open the hole with a 2 mm (5/64") drill.
- Hinge pin will not go through the cheeks: open them with a 2 mm drill. Arm binds on the pin: open the arm's
  hole with a 2.5 mm (3/32") drill. Pick any PETG strings out from between the cheeks first.
- Swivel binds when turning: raise `CLR_V` (0.15) to 0.25 and reprint the swivel and kingpin.
- Leg rubs the sides of the engine's loop on curves, or the arm will not sit down on it: note where, and
  how far the arm stays up.
- Cars too close or too far apart: see Measurement 9.

## Rebuild

```
pip install manifold3d trimesh shapely scipy pyvista vtk matplotlib lxml networkx
python3 coupler.py    # builds the three parts and prints their size
python3 check.py      # fit, travel, coupling on both loops up/down and on curves, forces (about 6 minutes)
python3 tender_loop.py    # builds the tender's loop and prints its size
python3 check_tender.py   # the loop on a stand-in of the tender's beam, and the coupler in it
python3 export.py     # STL + 3MF in out/package
python3 render.py     # previews and side sections in out/renders
python3 slice/plate.py /path/to/OrcaSlicer/AppRun   # lays out and slices the black PLA plate
```

`slice/` holds the presets: `fetch_profiles.py` fetches the stock SV06 ACE presets from the OrcaSlicer
v2.5.0 source and flattens their `inherits` chains (into `slice/stock/`), `make_presets.py` applies the
changes listed under Print, and `plate.py` lays out the plate and runs the OrcaSlicer 2.5.0 command line
(on Linux: the AppImage extracted with `--appimage-extract`, with `libwebkit2gtk-4.1-0` and `libopengl0`
installed; on the Mac it is `/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer`, not tried).

## Files

- `coupler.py`: measured and assumed values at the top; the kingpin (head and shaft, teardrop lock hole),
  the swivel (plate outline extruded up, cheeks as x-z profiles extruded across), the arm (x-z profile
  extruded across, its lug shaped by sweeping the swivel's middle over the arm's travel, front corners
  chamfered); stand-ins of the tab (stadium hole, ridges), a car's loop and the engine's loop.
- `check.py`: the checks above, with a 2D solve of the seated arm for the forces.
- `tender_loop.py`: the tender's clip-on loop, its lock filaments, and a stand-in of the tender's back beam
  (windows, outer wall, top, buffers, the stub); `check_tender.py` checks it.
- `slice/`: `fetch_profiles.py`, `make_presets.py` (the presets and their changes), `plate.py` (layout and
  slicing); `stock/` holds the fetched stock presets, `plate/` the laid-out STLs.
- `export.py`, `render.py`.
- `v1/`: version 1 (Nov 24), printed and tested; its README describes it.
- `photos/` (Aaron's; local folder only):
  - `01_loco_tender_broken_hook.jpg`: engine's loop and tender's tab, broken hook on the counter
  - `02_broken_hook_flat.jpg`, `03_broken_hook_angle.jpg`: the broken hook, its drop leg missing
  - `04_glued_hook_top.jpg`: the glued hook on a car, from above
  - `05_glued_hook_tab.jpg`: the tab from above, snap peg in its hole
  - `06_glued_hook_side_ruler.jpg`: side view, ruler upright beside the drop leg (about 22.75 px/mm there;
    the camera is a little in front, so lengths along the track read short)
  - `07_glued_hook_side_caliper.jpg`: side view, caliper held behind the hook (about 25.1 px/mm on its
    scale; the scale is farther away, so lengths read long)
  - `08_tender_end_broken_loop.jpg` (Nov 25): from above, the tender's back end with its broken loop, the
    printed v1 coupler, and the orange car's intact loop
  - `09_tender_end_underside.jpg` (Nov 25): the tender's back end from below: the beam, the windows next to
    the buffers, the broken stub and the two little tabs beside it

## Tender's clip-on loop (`tender_loop.py`)

Aaron's request (Nov 25): the tender's own loop, at its back end, broke off; it was identical to the one on
the other cars. He will cut off what is left and clip on a printed loop "by printing something that goes
through the holes shown" (photo 08). Coordinates for this part: u along the track away from the tender (the
way the loop sticks out), from the beam's outer face; v across; z up from the table, tender on the track.

| Measured (Aaron, Nov 25) | mm |
|---|---|
| Windows in the top of the beam, one next to each buffer: along the beam x across | 5 x 2.3 (the 2.3 is "approximate, hard to get into") |
| Windows, middle to middle | 29.5 |
| Windows go down through | about 3.5 ("yes, roughly"); under the beam and windows there is "a ton of room" |
| Beam's face, top to bottom | 8 |
| Top of the broken stub below the top of the beam | about 3.5 |
| Stub | the same as the cars' loops (16 wide, 1.5 thick, top 27.5 above the table); sticks out about 2.5 now |

Read off photos 08 (from above, about 14.75 px/mm from the 29.5 window pitch) and 09 (from below): the
beam's outer wall between the windows and the face is about 1.0 thick (`WALL_T`); the buffers sit about
19.9 either side of the middle, heads about 6 across and 3.7 out from the face.

How it works: a 2 mm plate goes down the beam's face where the stub was and carries a new loop like the
cars' (16 wide, 1.5 thick, top 3.5 below the top of the beam, opening 7.5 x 10 starting 2.25 out, 12 out
overall). Its far corners are rounded to 4 mm instead of a full half circle, which keeps the end bar 2.1
thick at the opening's corners; the bar's inner edge, where the coupler's raked face bears, is straight
for 7 mm. Two arms reach back over the top of the beam, and a 1.3 x 4.6 peg from each drops through a
window. Pulling, the pegs bear on the inside of the beam's outer wall (they sit 0.6 off it); they fill the
windows' length (0.2 each end), so the loop stays centered; a piece of filament through each peg, under the
beam's top, stops the clip lifting off (0.5 of play). Small fillets join the loop's side rails to the plate,
outside the opening so the coupler's leg still has its full travel.

Checks (`check_tender.py`, Nov 25, in code; about 2 seconds): one closed solid; fits over a stand-in of the
beam once the stub is cut off (and not before); rests on the top of the beam; located along the beam by
the windows; pulled, the pegs bear on the outer wall after 0.65 mm; the lock filaments clear everything and
catch under the beam's top after 0.55 mm of lift; it fits if the outer wall is 0.6 to 1.6 thick. The coupler
on the car behind seats in the new loop (underside on the bar, bar on the raked face), has the same 3.65 mm
pushing travel as on the cars, uncouples with 2 mm of slack, clears the tender, and fits with the loop
turned 15 degrees either way.

Printing: it is on the black PLA plate, as fitted (plate and pegs on the bed, 9 mm tall). The loop prints
on a thin U-shaped snap-off wall: 0.8 thick under its far end and under the middle of both side rails
(`SUPPORT_U`, `SUPPORT_RAIL_V`, `SUPPORT_RAIL_U0`; Nov 25). With the far-end wall alone, the 3 mm rails
spanned about 8.4 mm of air from the plate, all walls and no bridge infill; on the U only the rails'
outermost and innermost lines hang, about 1 mm past the wall. Snap the whole U off afterwards.

Assembly:

1. Cut what is left of the old loop (the stub and the two little tabs beside it) flush with the beam's
   face, and file it flat, so the plate lies flat on the face.
2. Snap off the thin U-shaped wall under the new loop (far end and both side rails) and file the rails'
   undersides; nothing bears on them.
3. Set the clip on: pegs down into the two windows, the plate against the beam's face, the arms on top.
4. Turn the tender over. Push a 6 mm piece of filament into each peg's small hole from the inside, toward
   the beam's face, until it stops. Warm the end that sticks out and bend it down.

Fit test:

- Pegs do not line up with the windows: measure the beam's outer wall between a window and the face, set
  `WALL_T` (1.0), and re-run `check_tender.py` and `slice/plate.py`.
- Loop sits too high or low against the stub's old place: `STUB_DROP` (3.5) is the loop's top below the
  beam's top. The coupler copes with a loop up to 3 mm off.
- Lock filament will not go through a peg: open the hole with a 2 mm (5/64") drill.

## Not yet done

- Version 2 and the tender's loop not printed. Print the plate and fit them first.
- Measurement 9 (spacing) not taken; `X_I` comes from photos 06 and 07 of the glued original.
- The ridges' spacing, the loops' end bar width, the engine loop's outline and the half-round ends come from
  photos or are assumed.
- The tender loop's fit to the beam rests on photo readings: the outer wall's thickness (1.0) and the
  window's position, the buffer positions, and the 2.3 window width.
