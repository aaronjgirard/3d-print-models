# Train track (straight, 22.5 degree curve, connector test piece)

Updated 2026-11-24 15:28 MST (`plate_curve_straight_coupler`: the same plus one coupler from `../train-connectors`; earlier on Nov 24: `plate_curve_straight`, one R 412.3 curve and one straight; original straight re-measured at 163.2, model stays 164.0 to offset the 0.5% print shrink; outer wall back to the stock 200 mm/s, 4 top and 3 bottom shell layers; earlier on Nov 24: curve ties spaced like the originals, print times recalibrated to the Orca settings, curve radius 412.3 from caliper readings, tab block 0.5 mm farther out, first print results)

Printable track that joins an existing battery Christmas-train set, designed Nov 22 2026 from caliper
measurements and photos of an original straight and curve. Everything is generated in `track.py`
(no third-party meshes). Each joint is a tab end (thin plate plus a 3 mm block) that slides under the
next piece's bridge and rises into its window, and a prong end whose two prongs tuck under the next
piece's raised rail ends. Printed pieces join the originals in both directions.

## Measured on the originals

The first batch of caliper photos carried a 35.5 mm zero offset; the numbers below are corrected.

| Feature | mm |
|---|---|
| Gauge, inside rail to inside rail | 31.8 |
| Rail thickness / height | 1.55 to 1.7 / 7.0 |
| Tie top above the table / tie width / tie length | 2.2 / 7.4 / 46 |
| Straight, rail end to rail end (re-measured Nov 24) | 163.2 |
| Curves | 8 make 180 degrees, so 22.5 each |
| Curve, inside rail end to end (caliper) | 153.74 |
| Tab: plate thickness, length past the end tie | 1.0, 5.3 |
| Tab: block height, length, width | 3.0, 8.7, 15.2 |
| Tab: plate width (from photos) | about 20 to 22 |
| Prongs: outside to outside, gap, width | 46, 25.5, 10.25 to 10.5 |
| Prongs: length, past the rail ends | 19, 13.5 |
| Prongs: thin inner part, thick outer rib | 1.0 tall; 2.1 tall x 3.0 wide |
| Prongs: shape | the thin part starts at the rail ends; inside the piece the prong is rib height from the rail's outer face out, so the raised part is an L; tip corners rounded |
| Prong end: bridge, window (from photos) | 4.1 to 5.0 long; about 10.8 x 16.4 |

Curve radius: with the caliper jaws on the two ends of the inside rail, an original curve reads 153.74
and the first printed curve (`CURVE_R = 380`) read 141.16, which was 0.5% under the model's 141.87. Each
1 mm of that reading is 2.56 mm of radius, so `CURVE_R = 412.3` (centerline), which the model reads as
154.47 and a print should read about 153.7. A ring of 8 originals measured 80 to 82 cm across, against
82.5 cm at the centerline for this radius. The first radius came from an earlier single reading of 155.0
taken as the outside rail. The originals turn right going from the tab end to the prong end, and so do
these. Like the originals, the curve has 6 full ties, 23.2 apart along the centerline, the first centred
25.3 from the tab end (read off a photo against the caliper scale, about 1 mm either way) and the last
touching the deck; the straight keeps 7.

Straight length: an original straight reads 163.2 rail end to rail end (Nov 24 2026). Prints come out
0.5% short of the model (the curve above), so `STRAIGHT_L` stays 164.0 (163.2 / 0.995 = 164.02) and a
printed straight should read about 163.2.

## Printed values and clearances

| Feature | Printed | Fits against |
|---|---|---|
| Tab plate | 0.8 thick, 19.0 wide | original bridge clears a 1.0 plate about 20 to 22 wide |
| Block | 15.1 x 8.05, 5.85 to 13.9 past the end face | original window about 16.4 wide; a block from 5.35 went into an original prong end but tightly |
| Recess under the rail ends (tab end) | 1.4 tall, from 12.3 off center, 14.2 long | original prongs 1.0 tall, 12.75 off center, 13.5 long |
| Prongs | 0.8 plate from the rail ends to the tip, 2.2 raised L (3.0 rib plus the 5.5 mm root inside the piece), 26.2 apart, 13.3 past the end, tips rounded 2.0 / 1.5 | original tab end's recesses |
| Bridge / window | 4.6 long / 11.0 x 16.4 | original block from 5.3 to 14.0, 15.2 wide |
| Recess under the bridge | 1.4 tall, 25.2 wide, 6.0 deep | original plate 1.0 x about 22 x 5.3 |
| Ends | last tie and deck 3.0 tall (flush with the block), 0.6 mm chamfer on the top edge of each end face | |

## Wood grain

The tops of the ties, the last tie at the tab end and the deck at the prong end carry wood grain:
wavy grooves running along each tie, 0.65 mm wide and 0.4 mm deep (two 0.2 mm layers), about 1.75 mm
apart, with plain lands of about 0.9 mm between them and 0.5 mm along the tie edges. The lines on the
ties wave nearly in phase and break off once or twice at random; the end planks have straighter grain.
No grooves within 0.4 mm of a rail, 0.8 mm of the window, or on the chamfered top edge of an end face,
and none on the prongs. The grain is generated from fixed seeds, so every copy of a part is identical.
`GRAIN = False` at the top of `track.py` turns it off; `GRAIN_W`, `GRAIN_D` and `GRAIN_PITCH` set the size.
The grooves are sized for the 0.4 mm nozzle (a groove about 1.5 line widths wide stays open).

Free play from `check.py` (side to side / pulling apart / lifting):

| Joint | Side | Pull | Lift male | Lift female |
|---|---|---|---|---|
| original tab into printed prongs | 0.35 | 0.70 | 0.40 | 0.20 |
| printed tab into original prongs (worst case) | 0.45 | 0.85 | 0.20 | 0.40 |
| printed into printed | 0.65 | 1.25 | 0.60 | 0.60 |

The stand-in for the original prong end takes its bridge as 5.0 long (from photos), which the first print
showed is too short: the real one left no pull play against a block starting at 5.35, so expect about 0.5
for the printed tab in an original prong end.

## Print files (`out/package`)

| File | Size | Time | Black PLA |
|---|---|---|---|
| `track_test_piece.3mf` | 60 x 46 x 7 mm | 11 min | 4 g, print first |
| `track_straight.3mf` | 191 x 46 x 7 mm | 36 min | 14 g |
| `track_curve_22_5.3mf` | 192 x 80 x 7 mm | 33 min | 14 g |

Files are in print orientation, flat side down, no supports. STLs of the same parts are in `out/package/stl`.

Times are Klipper planner times from `../cli_slice/klipper_time.py`, replayed on G-code that PrusaSlicer
2.7.2 sliced with `slice/sv06ace_pla.ini` (single pieces with a one-loop skirt). That file copies the
settings of the `../cli_slice` style `track_pla` (the Orca settings below: stock speeds and accelerations,
3 walls, 4 top and 3 bottom shell layers). Checked against the Orca G-code of the first print (sliced with
the earlier settings, outer wall 100 and 5 / 4 shells), it gave the test piece's planner time to the second
and the R 380 curve's within about 6%.
Until Nov 24 the file used slower speeds and these times were about 20% high. Filament is PrusaSlicer's
figure. Every print also spends a few minutes in `START_PRINT` (nozzle clean and adaptive bed mesh), which
is not included.

### Where the time goes

The pieces are small but nearly solid: the ties, decks and webs fill the bottom 2.2 mm. With the settings
used until Nov 24 (outer wall 100, 5 top and 4 bottom shell layers) the curve took 36.5 min: the first
layer alone 6.6 min at the stock 30 and 40 mm/s, the rest of the bottom 2.25 mm 22.8, the planks up to
3 mm 3.0, and the 20 layers of bare rail above 4.2. Savings measured on the curve, one at a time: outer
wall at the stock 200 mm/s, 1.9 min; 4 top and 3 bottom shell layers, 1.3; 2 walls instead of 3, 0.6; no
wood grain, 2.9; hollow undersides under the webs and ties, like the originals (tried in a throwaway
script, not in the model), 2.5. Only the first two are applied (Nov 24); the others save too little for
what they change.

### Full plates (`out/plates`, from `plates.py`)

| File | Layout | Time | Black PLA |
|---|---|---|---|
| `plate_4_straights.3mf` | 4 straights, 9 mm apart, 4.5 mm from the bed edges | 2 h 23 min | 57 g |
| `plate_4_curves.3mf` | 4 curves nested, every other one slid 10 mm, 3.2 mm apart | 2 h 12 min | 54 g |
| `plate_5_straights_tight.3mf` | 5 straights, every other one turned 180 degrees and slid 15.5 mm so the tie ends interleave, 2 mm apart, 1.8 mm from the front and back bed edges | 2 h 58 min | 71 g |
| `plate_curve_straight.3mf` | 1 curve and 1 straight, 3 mm apart (`python3 plates.py --curve-straight`, seconds); Orca's CLI re-arranges them, 6.6 mm apart | 1 h 12 min (Orca, `track_pla`, skirt on) | 27 g |
| `plate_curve_straight_coupler.3mf` | the same plus one coupler (arm and swivel from `../train-connectors/out/package/stl`) in front of the straight (`python3 plates.py --curve-straight --extra coupler ARM.stl SWIVEL.stl`) | 1 h 16 min (Orca, `track_pla`, skirt on) | 28 g |

Four of either piece fit with 3 mm between parts. A fifth straight fits only in the tight layout, and a
fifth curve does not fit at any spacing tried (down to 2 mm gaps and 1.5 mm from the bed edges). Load the
plate 3MF rather than copying pieces in Orca: its arrange spaces curves by their outline and fits only
3, and it never turns every other straight around. Each plate also comes as one STL with the layout
baked in. Plate times are without a skirt: set `Others > Skirt > Skirt loops = 0` for all three plates,
and for the tight plate also `Others > Brim > Brim type = No-brim` (Auto).

### Filament

Black PLA, which is on hand (the PETG on hand is white/purple, white/green and white/blue). The prongs
flex every time a joint goes together and one original prong already broke; PLA is stiffer and more
brittle than PETG, so a prong plate is where a PLA piece would crack. Join the test piece to an
original several times before printing a plate; if a prong cracks, print in PETG.

### OrcaSlicer 2.5.0 settings

Printer `Sovol SV06 ACE 0.4 nozzle`, brass nozzle. Filament `Generic PLA @Sovol SV06 ACE` with these
changes (stock in parentheses):

- `Filament > Print temperature > Nozzle`: First layer 220 (235), Other layers 210 (stock)
- `Filament > Volumetric speed limitation > Max volumetric speed = 18` (21)
- `Cooling > Part cooling fan`: Min fan speed threshold 80% (50%), Max fan speed threshold 100% (80%); 60 / 85% is quieter
- Bed temperature and retraction stay stock.

Process `0.20mm Standard @Sovol SV06 ACE`, then:

- `Strength > Walls > Wall loops = 3` (2)
- `Strength > Top/bottom shells`: Top shell layers 4 (3), Top surface pattern Monotonic line (stock); Bottom shell layers stay at the stock 3. The ties, rails and prongs are narrow strips, where Archimedean Chords breaks into fragments. (5 top and 4 bottom until Nov 24; the ties are only 2.2 tall, so those filled them solid.)
- `Quality > Precision`: Elephant foot compensation 0.15 (0.1), X-Y hole compensation 0 and X-Y contour compensation 0 (the clearances are in the model), Precise wall on
- `Quality > Wall generator > Wall generator = Classic` (stock)
- `Quality > Walls and surfaces`: Walls printing order Inner/Outer, Top surface flow ratio 1 (0.8)
- `Speed > Other layers speed > Outer wall` stays at the stock 200 (100 until Nov 24)
- Full plates: `Others > Skirt > Skirt loops = 0`; the tight plate also `Others > Brim > Brim type = No-brim` (Auto)

All heights in the model are whole 0.2 mm layers. With the stock 0.25 mm first layer, the thin plates
print about 0.85 thick and the recesses about 1.45 tall, which still clears. The bridge over the
recess under the prong end spans 25 mm and the rail ends over their recesses overhang about 5 mm;
both print without supports with PLA's full part-cooling fan. Either side of the PEI sheet works for
PLA, with no glue. These are starting values, untested on this printer.

## Fit test

1. Print `track_test_piece` in the same black PLA.
2. Join its tab end into an original prong end, and an original tab end into its prong end, the same way
   the originals go together, several times each. Both should go together without forcing and stay
   together when lifted, and no prong should crack.
3. Measure it: gauge 31.8, block 15.1 wide, prong plates and tab plate 0.8 to 0.85 thick, prongs 26.2
   apart on the inside.
4. If anything binds, the numbers are at the top of `track.py`: `PLATE_T`, `PLATE_HALF`, `BLOCK_HALF`,
   `BLOCK_S0` (tab end); `PRONG_IN`, `PRONG_THIN_H`, `BRIDGE_L`, `WINDOW_HALF`, `F_RECESS_H` (prong end);
   `M_RECESS_T`, `M_RECESS_H` (recess under the rail ends).
5. Curve: swap one printed curve into a ring of originals. If the ring does not close without strain,
   change `CURVE_R` and rebuild.

## Rebuild

```
pip install manifold3d trimesh shapely scipy pyvista vtk lxml networkx
python3 track.py      # builds the three parts and prints their size
python3 check.py      # bodies, bed fit, mesh quality, dimensions, every joint against stand-ins of the originals
python3 export.py     # STL + 3MF in out/package, parts.csv
python3 render.py     # previews in out/renders
python3 make_overview.py   # out/track_overview.png from the renders
python3 plates.py     # plate layouts, 3MF + STL + PNG in out/plates (about 5 minutes)
python3 plates.py --curve-straight   # only out/plates/plate_curve_straight.*
cd slice && prusa-slicer --export-gcode --load sv06ace_pla.ini --skirts 0 --dont-arrange \
    -o plate_4_straights.gcode ../out/plates/plate_4_straights.stl   # grams in the G-code footer
python3 ../../cli_slice/klipper_time.py plate_4_straights.gcode     # Klipper planner time
```

## Files

- `track.py`: parameters, the path (straight or arc, straight past both ends so tabs and prongs stay
  straight on a curve), and the features. Each feature is a polygon in track coordinates (s along the
  centerline, t across it) mapped to the bed and assembled band by band in height with 2D booleans,
  so features in different frames meet without slivers. Connector cuts use the end tangent so they
  line up with the straight tab and prongs of the neighbouring piece.
- `check.py`: stand-ins of the original tab and prong ends (worst case where a number came from a photo),
  overlap and free play for every joint, dimensions measured off the built straight, layer heights,
  mesh quality, and the grain (no land or groove narrower than 0.48 mm in the slices through the grooves).
- `plates.py`: packs real outlines of the parts (not bounding boxes) on the 220 x 220 bed and writes the
  plate files.
- `slice/sv06ace_pla.ini`: PrusaSlicer stand-in for the Orca printer, filament and process settings above,
  used only for time and filament estimates.
- `export.py`, `render.py`, `make_overview.py`.

## Verified in code (Nov 22 to 24 2026)

- Each part is one closed solid with no zero-area triangles, still closed after an STL round trip, and
  fits the 220 x 220 bed.
- No overlap in any joint: printed tab into an original prong end, original tab into a printed prong end,
  printed into printed, on the straight, the curve and the test piece. Rail inner faces line up across
  every joint.
- Dimensions measured off the built straight match the targets to 0.02 mm (gauge, rails, ties, length,
  plate, block, prongs, bridge, window, recesses).
- On the curve, the first tie starts 21.6 from the tab end, so its inner end stays 6.9 mm clear of the
  straight prongs of the next piece.
- Wood grain (Nov 22 2026): grooves cut on the ties and end planks of every part, no land or groove
  narrower than 0.48 mm, groove bottoms on whole 0.2 mm layers, joint fits and dimensions unchanged.
- Plates (Nov 24 2026, with the R 412.3 curve): every piece in each plate file is a closed solid inside
  the bed; the closest pieces are 9.0, 3.2 and 2.0 mm apart (4 straights, 4 curves, 5 straights),
  measured on the meshes. On the tight plate the stand-in slicer's extrusion stays within x 8.2 to 211.8
  and y 2.0 to 218.0 mm.

## Printed (Nov 23 to 24 2026, black PLA, sliced with `../cli_slice` style `track_pla`)

- Test piece and an R 380 curve. Both ends joined the originals both ways and the joints work.
- The tab end went into an original prong end only tightly, so the block now starts at 5.85 instead of
  5.35; its far end stays at 13.9. The prong end is unchanged.
- The R 380 curve was short against an original (inside rail 141.16 against 153.74), so the radius is
  now 412.3.
- The undersides over the recesses at both ends print stringy: the prong end's 25 mm bridge and the
  overhangs under the tab end's rail ends. They are hidden and the joints work, so they stay as they are.

## Not yet done

- The 5.85 tab block and the R 412.3 curve with 6 ties are not printed yet; check the curve against an
  original or in a ring of originals.
- No straight printed yet; one should read about 163.2 rail end to rail end.
- The original plate width, bridge length and window size come from photos, not calipers; the check
  uses the worst case of each.
- Print times come from G-code sliced by PrusaSlicer standing in for Orca, replayed through the Klipper
  planner; Orca's toolpaths differ somewhat.
