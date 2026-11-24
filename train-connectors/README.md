# Train coupler (swivel and hinged hook arm)

Updated 2026-11-24 00:40 MST

Replacement for the red hook that couples the battery Christmas-train cars. Every car has a black tab with
a 4.5 mm hole at its front and a black loop at its back; the hook snaps into the tab hole and reaches
into the loop of the car ahead. The original broke twice at the corner above its drop leg. This version
is two printed parts per coupler plus a short piece of 1.75 mm filament as the hinge pin, and it couples
to the original loops, so it works with every car. Everything is generated in `coupler.py`.

## How it works

- **Swivel** (blue in the renders): a flat bar under the tab with a peg up through the hole. It snaps in
  from below like the original, with barbs at the front and back of the hole, and turns in the hole so
  the coupler follows curves.
- **Arm** (violet): hinged on the swivel's knuckle by a filament pin. Its flat underside rests on the next
  car's loop and its leg drops through the loop's opening. The back face of the leg is raked 30 degrees,
  so when the train pulls, the loop's end bar is drawn into the throat and clamped between the arm's
  underside and the raked face. The clamp force is about 0.6 times the pull, so it grips harder the harder
  the train pulls.
- The hinge sits level with the pull (0.5 mm above the contact), so pulling puts almost no vertical force
  on either car (about 0.01 times the pull). The arm rides up and down with the loop, which keeps the clamp
  seated over track joints and uneven floors; uncoupled, it rests on a stop 15 degrees down.
- **Couple**: lift the arm, set the leg into the opening, let go, then pull the cars apart a little.
  **Uncouple**: push the cars about 2 mm together and lift the arm about 25 degrees.
- Why the original broke: a rod about 2.7 mm thick that rises 12 mm and drops 18 mm, so every pull bent
  the corner above the leg. The new arm is 7.6 x 3.5 mm in section, the pull runs nearly straight through
  it, and both parts print on their side, so no layer line crosses a bend.

## Measured on the cars (Nov 23 2026, cars on the track)

| Feature | mm |
|---|---|
| Tab: hole diameter, thickness at the hole | 4.5, 1.5 |
| Tab: width, reach past the hole center | 16, 6 |
| Tab: top above the table | 27.0 |
| Loop: opening along the track x across | 7.5 x 10 |
| Loop: width, thickness | 16, 1.5 |
| Loop: top above the table | 27.5 |
| Loop: sticks out from the car's end wall | 12 |

## Assumed (to confirm)

| Value | mm | Source |
|---|---|---|
| `X_I`, tab hole center to the loop's end-bar inner edge when pulling | 22.0 | glued original in the ruler photos: its leg sits 22 to 24 mm past the hole. Measurement 9 (spacing) will confirm. Changing it moves the leg and changes only the gap between cars |
| `END_BAR`, loop end bar along the track | 2.25 | opening assumed centered like the tab's hole; only shifts the cars' gap |
| Tab and loop ends | half round across 16 | photos |
| Ridges on top of the tab beside the hole, channel between them | about 5.2 wide, 1.8 tall | photos; used only to check that the swivel turns freely (it can turn 65 degrees before touching them) |

## Printed values and clearances

| Feature | Value |
|---|---|
| Swivel thickness | 2.4 (the peg is a 4.2 circle cut to this, so the barbs stand out about evenly all round the hole) |
| Peg, barbs | 4.2 in the 4.5 hole; barbs 5.1 across, 0.30 over the hole edge on the centerline and 0.35 at the corners |
| Play at the tab | 0.15 above and below; plate top 25.35, barb undersides 27.15 |
| Snap | front prong is part of the plate and takes the pull; the back prong is a 7 mm finger that bends 0.7 mm (about 3.6 % strain) to let both barbs through |
| Pin holes | arm 2.3 (grips the filament once it prints a little small), swivel knuckle 2.6 (turns freely) |
| Hinge | axis 9.5 past the hole center, 26.5 above the table; knuckle 1.1 clear of the tab's tip |
| Arm | 7.6 wide, slot 3.0 for the 2.4 swivel; travel from the stop at -15 degrees to +40 |
| Leg | 3.0 thick at the loop's top, raked 30 degrees behind, bottom 3 mm under the loop; front face vertical, so pushing does not lift it |
| Pushing | 3.65 mm of travel before the leg meets the far side of the opening |

## Checks (`check.py`, Nov 24 2026, in code; nothing printed yet)

- Both parts are single closed solids.
- Swivel clears the tab turned up to 25 degrees; arm clears the swivel over its whole travel and meets
  the stop at -15 degrees; arm clears the tab at every angle, turned up to 20 degrees.
- Coupled: the underside rests on the end bar and the bar seats against the raked face.
- Uncoupling: with 1.8 mm or more of slack the arm lifts out cleanly; the leg is 0.3 over the loop at
  24.8 degrees.
- Coupling with the loop 3 mm low to 3 mm high, and on curves with the loop turned 15 degrees either way:
  the arm settles on the loop and the pull seats the bar on the raked face every time. Running onto a curve
  while coupled (loop -2, 0, +2 mm, turned 15 degrees either way) keeps it seated.
- Force balance from the geometry: clamp 0.59 times the pull; vertical force at the hinge -0.01 times the pull.

## Print

**Filament: PETG**, solid color (any of the PETG on hand). It bends instead of cracking, which the snap
finger needs (0.7 mm to go in) and the hook wants under a yank. ABS would also do it but warps and splits on
the open printer; both cost about $20/kg, and two sets weigh about 2 g, so cost does not decide it.
**Nozzle**: 0.4 mm brass.

Printer `Sovol SV06 ACE 0.4 nozzle`. Filament `Generic PETG @Sovol SV06 ACE`, then (stock in parentheses):

- `Filament > Print temperature > Nozzle`: First layer 245 (260), Other layers 240 (245)
- `Filament > Bed temperature`: 80 (85), on the row for the plate type selected in the sidebar
- `Filament > Volumetric speed limitation > Max volumetric speed = 12` (15)
- `Cooling > Cooling for specific layer > No cooling for the first = 3` layers
- `Cooling > Part cooling fan > Max fan speed threshold`: fan speed 60% (30%)
- `Cooling > Part cooling fan > Overhangs and external bridges fan speed = 100%` (the arm's upper cheek bridges the slot)
- `Setting Overrides > Retraction > Length = 1.0` (0.8)

Process `0.20mm Standard @Sovol SV06 ACE` (or the saved standard preset), then:

- `Strength > Walls > Wall loops = 4` (2)
- `Strength > Infill > Sparse infill density = 40%` (10%)
- `Quality > Precision`: Precise wall on; X-Y hole compensation 0.1 (pin holes then come out at or a little
  over 2 mm); X-Y contour compensation 0 (the barbs are sized for this); Elephant foot compensation 0.15 (0.1)
- `Quality > Walls and surfaces`: Walls printing order Inner/Outer, Avoid crossing walls on
- `Speed > Other layers speed > Outer wall = 100` (200)

No supports, no brim. Wipe the nozzle tip before printing (it is the bed probe). PETG grabs smooth PEI, so
use glue stick on the smooth side, or the textured side, and let the bed cool before taking the parts off.
These values are starting points, untested on this printer.

Files (`out/package`), in print orientation on their side: `coupler_plate_2_sets.3mf` (two arms and two
swivels, centered on the bed), `coupler_arm.3mf`, `coupler_swivel.3mf`, and STLs of the same in `stl/`.
About 2 g of PETG for both sets.

## Assembly

1. Slide the swivel's knuckle into the slot between the arm's two cheeks, with the swivel's bar pointing
   away from the arm's hook, and line up the holes. Push a piece of filament through all three and trim it
   flush with the arm's outer faces. If it slides, touch each end with the soldering iron to mushroom it, or
   put a drop of glue on the arm's outer faces at the pin, keeping glue off the swivel.
2. Take the old hook out: from above, squeeze its two barbs together and push it down through the hole.
3. From below, push the swivel's peg up through the tab hole, hinge toward the tab's tip, until both barbs
   click over the top. It should turn freely in the hole.
4. Lift the arm and let it fall: it should swing freely and stop about 15 degrees down.

## Fit test

Print one set first and fit it to a car.

- Barbs do not catch, or the swivel drops out: raise `BARB_R` (2.55) by 0.1 and rebuild.
- Swivel will not go in, or the back finger cracks: lower `BARB_R` by 0.05, or print in a different PETG.
- Swivel binds when turning: raise `CLR` (0.15) to 0.25.
- Pin will not go into the arm: open the arm's holes with a 2 mm drill, or raise `ARM_HOLE` (1.15).
- Arm's upper cheek sagged into the slot: trim it with a knife so the swivel's knuckle slides in.
- Cars too close or too far apart: change `X_I` (22.0).

## Rebuild

```
pip install manifold3d trimesh shapely scipy pyvista vtk matplotlib lxml networkx
python3 coupler.py    # builds both parts and prints their size
python3 check.py      # fit, travel, coupling up/down and on curves, force balance (about 2.5 minutes)
python3 export.py     # STL + 3MF in out/package
python3 render.py     # previews and side sections in out/renders
```

## Files

- `coupler.py`: measured and assumed values at the top, the swivel and arm built as x-z profiles extruded
  across the track (the peg is revolved and cut to the swivel's thickness), the arm's slot made by sweeping
  the swivel's profile over the arm's travel, and stand-ins of the tab and loop.
- `check.py`, `export.py`, `render.py`.

## Not yet done

- Nothing printed. Print one set and fit it first.
- Spacing (measurement 9) not taken; `X_I` comes from the ruler photos of the glued original.
- The loop's end bar width, the tab's ridges and the half-round ends come from photos.
- The arm's upper cheek bridges about 5 mm over the slot; untested on this printer.
