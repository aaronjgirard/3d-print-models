# Marble Run

Updated 2026-11-26 00:45 MST (Epitrochoid 3 tubes tall, 4 loops, Orca tree supports, exit window needs no tree; 2026-11-25 11:34 MST: keel_v4 anchored; 09:56 MST: keel_v3 plug 25.75 / 21.6; 09:55 MST: 45 deg keel, tall trees dropped, top post reworked)

Marbleworks-compatible marble run pieces for the SV06 ACE: the Pyrce007
Marbleworks Marble Mazes set, the 1 to 4 pitch tubes designed here, and
generated pieces (buckets, racing finish, peg trays, cascade, merges).
Units are mm, z up.

## License
The generated pieces, tubes and scripts are Apache-2.0 (root `LICENSE`). The Pyrce007 pieces in `stl/marbleworks/` and `ref/marbleworks/` are [Marbleworks Marble Mazes by Pyrce007](https://www.thingiverse.com/thing:4202442), CC BY (`ref/marbleworks/LICENSE.txt`), renamed only. `stl/custom/twopost_1loop_l.stl` and `clicky_5_half_l.stl` are remixes of his `twopost_1loop` and `clicky_5_half`: they stay CC BY with credit to Pyrce007, and the changes made by `src/refit.py` are Apache-2.0. The `Epitrochoid_*` files are remixes of his `epi_725` (Epitrochoid 7-2-5): CC BY with credit to Pyrce007; the changes (refit, trees, keel, top post) are Apache-2.0.

## Layout

| folder | contents |
|---|---|
| `stl/marbleworks/` | Pyrce007 pieces, renamed (43) |
| `stl/tubes/` | `tube_1` .. `tube_4`, straight tubes 1 to 4 pitches tall |
| `stl/custom/` | generated pieces, printable |
| `preview/` | cut-aways and marble spheres for viewing only, do not print |
| `ref/marbleworks/` | Pyrce007 README, LICENSE, images, `names.md` (short name to original name) |
| `ref/catalog.png` | picture sheet of every piece with name and file name (`python src/catalog.py`) |
| `src/` | generator and import scripts |
| `config/` | `project.json` (folders, tube names, span variants, refit pieces), `marbleworks_names.json` |

## Environment and builds

```bash
conda activate marble-run                      # python 3.12, manifold3d, trimesh, matplotlib, scipy
python src/build.py                            # all generated pieces (about 5 s)
python src/build.py pieces                     # one script: stand | bucket_v2 | pieces | tubes | refit | cascade
python src/import_parts.py ZIP1 ZIP2           # re-import the Marbleworks zips and tubes (--force to overwrite)
```

## Connector and marble

Generated pieces use the fit-ladder connector (`connector` in `config/project.json`):

| part | size [mm] |
|---|---|
| post OD | 29.6 |
| socket bore | 25.6 |
| plug | split ring, OD 25.75 (fit-ladder step 1.5), bore 21.6, 11 long, 12.8 slot facing +x, the two top corners of the slot rounded r 2 (`plug_slot_r`) |
| shoulder | 45 deg, 2 mm, bore 25.6 to 21.6 |

Rule (Aaron, 2026-11-23): every plug keeps its split-ring gap, and the two corners at the very top
of the gap (where each ring end meets the plug top) are rounded; never one without both.
`src/rounds.py` makes the gap cut; `parts.add_plug`, `stand.post` (the buckets) and
`cascade.plug_open` all use it, so every generated piece gets it.

Fit-ladder steps 1/2/3 are plug OD 25.7/25.8/25.9. Change `plug_od` and
rebuild to switch. Marble diameter is 14.5 (`marble`); channels, windows and
the finish-lane place spacing scale with it.

## Generated pieces

| file | script | piece |
|---|---|---|
| `bucket_ring` | `stand.py` | post in the middle, round trough all around |
| `bucket_side` | `stand.py` | post at one end, 100 x 90 rounded bucket |
| `bucket_kid` | `stand.py` | smaller 74 x 66 side bucket |
| `bucket_side2` | `bucket_v2.py` | side bucket rev 3, 200 x 118 x 58.3: 145.4 mm cavity (`--w`; 130 gives the 184.6 mm length printed 2026-11-14), post one tube pitch tall (`--post_h`); marbles drop onto a concave curve in the post (`--fil_rise`) that runs flat into a floor falling 6 mm away from the post (`--tilt`); slot open from the floor to the shoulder, 25.6 wide at the post and 30 at the bucket wall, never narrower than the bore; far-end bottom radius 45 (`--r_end`); beaded rim with lip, flared base, rim flat at the post top within 5 mm of the post, ramping up to 50 over 30 mm (`ramp_gap`, `ramp_len`) |
| `finish_raised` | `pieces.py` | racing finish lane, 10 places, raised labels |
| `finish_inset` | `pieces.py` | racing finish lane, inset labels |
| `plinko_1out` | `pieces.py` | peg tray, one outlet to a receiver post |
| `plinko_2out` | `pieces.py` | peg tray, two outlets to two receiver posts |
| `cascade` | `pieces.py` | three stacked switchback ramps |
| `merge_y` | `pieces.py` | two emit posts merging into one receiver |
| `merge_opp` | `pieces.py` | two emit posts on opposite sides of one receiver |
| `tube_1_v2` .. `tube_4_v2` | `tubes.py` | straight tubes 1 to 4 pitches tall (47.3 mm, `tube_pitch`) with the fit-ladder plug; the old `stl/tubes` have a 25.4 plug |
| `twopost_1loop_l` | `refit.py` | Pyrce007 `twopost_1loop` refit to the long span: posts 185.8 apart, 216.8 x 95 x 105.6, both posts two levels (94.6) plus the plug |
| `clicky_5_half_l` | `refit.py` | Pyrce007 `clicky_5_half` refit to the long span: posts 185.8 apart, 216.8 x 31 x 105.6, upper post one level up, ramp about 19.5 deg (15 as imported); 45 deg keel 5 mm deep under the ramp, cone ceiling over the raised post's socket, pointed top on the lower ramp opening, upper exit opening cut back to 45 deg with its slot open to the top, so only the raised post needs support |
| `cascade_l` | `cascade.py` | switchback cascade on 183.8 mm post spacing (the clicky span less 2 mm), 213.4 x 29.6 x 152.9: raised post two pitches up (bottom 94.6), low post on the bed, three ramps stacked in one plane at 5.4 deg with 31.5 mm floor-to-floor drops through holes open to the front; a back plate on the bed carries each ramp on a 45 deg shelf; raised socket under a 45 deg cone; both windows 17 wide, open to the top through the shoulder and a C plug (config `cascade`) |

Last build (2026-11-13 10:50 MST): all 11 watertight, one body each.
`bucket_side2` and `tube_*_v2` rebuilt 2026-11-13 17:14 MST: watertight, one body each, plug 25.75 / 21.6, socket 25.6.
`bucket_side2` rev 3 built 2026-11-14 20:46 MST: watertight, one body, 311 cm3. The staged
`bucket_side2_short_*` G-code below is the rev 2 bucket.
`bucket_side2` lengthened to 200 mm (cavity 145.4, same 6 mm floor fall, now about 4 deg) and rebuilt 2026-11-14 22:10 MST:
watertight, one body, 336 cm3. With the 5 mm brim it spans 5 to 215 mm on the bed, 5 mm past the
probed area (10 to 210 mm) at each end; Aaron chose that over 190 mm. Every `bucket_side2_rev3_*`
G-code below is the 184.6 mm bucket. A plate of the 200 mm bucket plus three `tube_3_v2` sliced to
5 h 36 min (5 h 53 min with margin) in the scratchpad; layout not checked, not staged, not sent.
`twopost_1loop_l` and `clicky_5_half_l` built 2026-11-15 11:59 MST after Aaron approved preview
images, rebuilt 12:32 MST at the remeasured span (185.8, was 184.5) with the leftover source plug
slots under the new shoulders filled (Aaron: "fill it, no tree"): watertight, one body each
(94.4 and 37.8 cm3), sockets 25.6 for 16 mm, plugs 25.75 / 21.6.
Both are 216.8 mm long, so each goes on the bed turned 45 deg (168.5 and 162.4 mm square), one per
plate; the two cannot share a plate with a brim.
`clicky_5_half_l` rebuilt 2026-11-15 13:02 MST with the support-free options (Aaron: "add the clicky
ramp 45 deg keel so I can see"; the ceiling and the two window changes were added to clear the trees
he pointed at inside the posts): watertight, one body, 46.8 cm3. Checked against the previous mesh:
the channel floor, the inlet floor and everything else seen from above are unchanged except at the
two openings; the keel ridge is 5.15 mm under the old underside and at least 16.5 mm off the bed;
2.2 mm of inlet floor is left over the cone at its thinnest. `twopost_1loop_l` is unchanged.
`cascade_l` built 2026-11-17 16:30 MST: watertight, one body, 183.7 cm3. Every downward face is
45 deg or steeper except the raised post's bottom ring, and a 0.2 mm layer check finds nothing else
starting in the air.
All pieces rebuilt 2026-11-24 00:00 MST with the gap top corners rounded (r 2): every STL in
`stl/custom` watertight, one body each; each changed only by about 4.14 mm3 per plug (6.29 on the
`cascade_l` open-slot plug). Every G-code staged before this has square gap corners.
`plinko_*` (234 to 237 mm) and `merge_opp` (240 mm) are longer than the
220 mm bed side and need a diagonal placement; `finish_*` is 217 mm.

## Printed

2026-11-13 17:14 MST: `bucket_side2_tubes_1x2_2x2_PLA_0.20mm_4h29m.gcode`, `bucket_side2` plus two
`tube_1_v2` and two `tube_2_v2` on one plate, black PLA. Sliced with
`cli_slice/slice.sh relief` plus the fit_ladder_1p5 wall settings (Classic, 2
loops, outer line 0.35, X-Y hole compensation 0.1, walls 200/270 mm/s at
6000/8000) and its infill and shells (10%, 3 top, 3 bottom, gap fill nowhere),
Orca auto-arrange. Planner estimate 4 h 29 min, 137 g. That bucket has the
old 70 mm post (81 mm with the plug).

2026-11-13 20:54 MST: `bucket_side2_short_tubes_1x2_2x2_PLA_0.20mm_4h23m.gcode`, the same plate
and settings with the bucket post cut to one tube pitch (58.3 mm with the plug) and the
rim ramped down to the post top beside it. Staged, not sent.

2026-11-14 20:48 MST: `bucket_side2_rev3_PLA_0.20mm_2h43m.gcode`, the rev 3 bucket alone with the
settings of the 2026-11-13 plate (G-code config blocks identical). Planner estimate 2 h 35 min,
2 h 43 min with the 5% margin, 90.5 g, 291 layers. Staged, not sent.

2026-11-14 21:57 MST: `bucket_side2_rev3_tubes_3x3_PLA_0.20mm_5h40m.gcode`, the rev 3 bucket plus
three `tube_3_v2` (152.9 mm tall) on one plate, black PLA, same settings (G-code config block
identical to the bucket-alone slice), Orca auto-arrange: tubes in a row in front of the bucket,
2 mm apart. Planner estimate 5 h 24 min, 5 h 40 min with the 5% margin, 175.5 g, 764 layers.
Sent and started 21:55 MST at Aaron's request. Finished; Aaron reported 2026-11-15 that the bucket
and the triple tubes fit the real set well.

2026-11-15 13:04 MST: `twopost_1loop_l_PLA_0.20mm_8h06m.gcode` and
`clicky_5_half_l_PLA_0.20mm_1h56m.gcode`, one piece per plate at the 185.8 span, same wall, infill
and shell settings as the plates above, plus an 8 mm brim and slim tree supports from the bed only
(`tree_slim`, 150 mm/s), as Aaron asked. They replace the organic-tree loop (11 h 02 min, 189 g)
and the unkeeled clicky (3 h 01 min, 62.7 g) staged at 12:33, which were deleted.
Loop: threshold 40 deg, planner 7 h 43 min, 8 h 06 min with margin, 183.0 g (81 g of it support);
the inlet floor inside the first post is not reached by the slim trees, and trees still stand
inside both posts under the track (z 34 and 52).
Clicky with the keel: threshold 20 deg, planner 1 h 51 min, 1 h 56 min with margin, 38.8 g
(3.8 g of it support, all under the raised post, which starts 47.3 mm in the air). At 40 deg the
slicer also puts thin trees under the keel ridge (8.2 g of support, 2 h 13 min); the ridge runs at
19.5 deg, so a threshold of 20 or less leaves it alone. Only 0.4 cm2 of this piece's undersides lie
between 20 and 40 deg.
Slicing notes: each piece is sliced from a copy of the STL turned 45 deg about z, because the Orca
CLI `--rotate 45` sank the part halfway into the bed. A flat or sloped edge across an opening still
gets a tree (its first layer starts in the air); only a pointed top, closing from both sides at
45 deg, is left alone. Staged, not sent; untested on the printer.

2026-11-17 13:29 MST: `tubes_1x3_2x2_PLA_0.20mm_2h37m.gcode`, three `tube_1_v2` and two
`tube_2_v2` on one plate, same settings as the 2026-11-14 tube plate (config block identical),
Orca auto-arrange, 2 mm apart. Planner 2 h 30 min, 2 h 37 min with margin, 71.3 g, 528 layers.
Seven `tube_1_v2` instead slice to 2 h 46 min and 74.8 g. Staged, not sent.

2026-11-17 16:51 MST: `cascade_l_PLA_0.20mm_3h33m.gcode`, `cascade_l` alone turned 45 deg, same
settings as the `clicky_5_half_l` slice (slim trees from the bed, 8 mm brim) at threshold 40 deg,
with thin branches (`--tree-support-branch-diameter 2 --tree-support-wall-count 1`; Aaron asked for
thin, minimal trees). Planner 3 h 23 min, 3 h 33 min with margin, 96.7 g, 5.5 g of it support, one
tree, all under the raised post. It replaces the 5 mm branch slice (3 h 36 min, 7.0 g of support).
Staged, not sent.

2026-11-24 00:03 MST: `tubes_2x3_4x2_matte_PLA_0.20mm_4h50m.gcode`, two `tube_3_v2` and four
`tube_2_v2` (gap top corners rounded) on one plate, matte rainbow PLA. Presets rebuilt from the
2026-11-17 tube plate with `cli_slice/presets_from_gcode.py`; the config block differs from it only
in the filament name, colour and max volumetric speed (15 mm3/s for matte, was 18); temperatures
220 / 210, fan 80 to 100%. Orca auto-arrange: a 2 x 3 grid, 2 mm apart. Planner 4 h 36 min,
4 h 50 min with margin (Orca says 3 h 03 min), 135.0 g, 764 layers. Sent and started 2026-11-24 00:06 MST at Aaron's request.

## Epitrochoid (`epi_725` remix)

Pyrce007's Epitrochoid 7-2-5 refit to the 47.3 mm pitch, with designed-in trees, then reworked for
printing (Aaron, 2026-11-25). One solid, 193 x 194 x 247.5 mm. The plug top is exactly five
`tube_1_v2` pitches plus the plug (shoulder 236.5 = 5 x 47.3, plug 11), so it lines up with a stack
of five single tubes. Its plug is the current fit-ladder plug (25.75 OD, 21.6 ID, 11 tall, as on the
v2 tubes; replaced the Nov 8 25.36 / 19.96 plug 2026-11-25 09:56 MST); the post's funnel bore under it is kept and
only its last 1 mm is opened to 21.6.

| file | what |
|---|---|
| `Epitrochoid_refit_47p3.stl` | the refit without trees (2026-11-08) |
| `Epitrochoid_supports_only.stl` | the designed-in trees alone (37 bodies, 68 cm3; from the 2026-11-08 build) |
| `Epitrochoid_plain.stl` | the refit with the reworked top post and exit window, no keel or trees (for slicer supports) |
| `Epitrochoid_3tube.stl` | **print this one**: 3 tubes tall (152.9 mm), 4 loops, slicer tree supports |

`Epitrochoid_3tube.stl` (`src/epi_top.py --plain`, then `src/epi_short.py`; config `epi_top`, `epi_short`;
Aaron 2026-11-26: 3 single tubes tall, 4 loops, a toy for a 4.5 year old, so a rough underside is
fine but no trees that fall over):
- The track is one loop repeated: turned -102.85 deg about the post and raised 29.275 mm, every loop
  lies on the one above (measured by matching the piece to itself between Z 60 and 100: median 0.36,
  max 1.2 mm; 7-2-5 gives 720 / 7 = 102.86 deg). Three loops are cut out at Z 80 and the two parts
  joined, the lower one turned to meet the upper (the upper holds the fine exit-window work). The
  last 6.8 mm come out of Z 17 to 95 by scaling z there by 0.913 (the channel is 8.7% lower inside
  there, about 18.4 mm for a 14.5 mm marble); socket, exit window and plug keep their sizes. Plug top
  152.9 = 3 x 47.3 + 11.
- Exit window (in `src/epi_top.py`, also in the 5-tube pieces): nothing that needs a tree. The ramp
  under the landing floor is cut 0.1 mm into the bore so the 0.04 mm ledge at Z 206 is gone; the gap
  between the landing floor and that ramp (the floor was only about 14 deg there) is filled, so the
  floor's underside is the 45 deg ramp; a bracket under the flat start of the track outside the
  window has a 45 deg underside rising from the post wall. The opening itself is unchanged.
- Checks: watertight before writing (a dozen hairline faces under 0.06 mm2 at the bracket top
  after rounding to float32; the piece loads as a valid solid with an exact vertex merge).

```bash
python src/epi_top.py --plain --src Epitrochoid_refit_47p3.stl --out Epitrochoid_plain.stl   # about 1 min
python src/epi_short.py                                                                     # writes Epitrochoid_3tube.stl
```

Slice, 2026-11-26 00:25 MST: `epitrochoid_3tube_hyperred_PLA_0.28mm_6h55m.gcode`, Hyper PLA+ red
(220 / 220, 18 mm3/s, fan 80 to 100%), stock `0.20mm Standard @Sovol SV06 ACE` with layer height
0.28, Orca supports on: Tree (auto), hybrid style, threshold 10 deg, hollow base, independent support
layer height on (Aaron asked for it back), z-hop 1.0 (was 0.4), avoid crossing walls. Planner 6 h 55
min with margin, 187.1 g, 914 layers. The tallest unbraced support column scores 16 on a knock-over
index (1000 L / d^3, L the height above a level, d its filled diameter) where the v4 bed trees that
fell score 1,305. Sent and started 2026-11-26 00:36 MST at Aaron's request.

`Epitrochoid_keel_v5.stl` (git-ignored, never printed; `python src/epi_top.py` with config
`epi_keel.struts`): v4 plus a thin fin under each keel ridge with 45 deg arches between 57 struts
(`src/epi_struts.py`) landing on lower outer walls or the bed, and tapered sleeves on every
freestanding column over 25 mm (bed trees and struts). It halves the area flatter than 45 deg, but
the struts on the walls stay about 4 mm thick (no room to widen them beside the track) and still
score about 1,000 on the knock-over index, so it was set aside for slicer supports.

`Epitrochoid_keel_v4.stl` (superseded, git-ignored; commit 661a57b) (`src/epi_keel.py`, then `src/epi_top.py`; config `epi_keel`, `epi_top`):

`Epitrochoid_keel_v4.stl` (`src/epi_keel.py`, then `src/epi_top.py`; config `epi_keel`, `epi_top`):
- 45 deg V keel under every track underside, like `clicky_5_half_l`, followed layer by layer where the
  track passes over itself, never within 16.5 mm of the layer below (marble 14.5 + 2).
- No keel starts in midair. Every keel bottom is raised where needed until it climbs, by at least
  0.02 mm per mm, from an anchor: the bed, a kept tree, the post, or track with no keel under it. The
  flood that does this runs over exactly the squares the keel mesh is built from.
- The keel is joined to the post (tube). Its inner edge runs 1.4 mm into the post wall. Within 6 mm of
  the wall, the keel bottom falls at 45 deg straight in to it, so the lowest ridge grows out of the
  post from about Z 10 (at most 14.7 mm under the old underside there).
- Trees: the 12 bed trees no taller than 117.5 mm (one turn, against shaking) and the 20 short struts
  between turns are kept; the five tall bed trees (147 to 210 mm) are gone.
- Top post: current plug (25.75 / 21.6); its gap faces the exit window with the window's own side faces (+-49 deg) carried
  straight up through the shoulder and plug, top corners rounded r 2; the midair cone under the landing
  floor is now a 45 deg underside rising from the exit-side wall (Z 196.2) to the back wall; a web
  fills the slit between the right-hand track wall and the window edge, flat at the shoulder top and
  falling 45 deg along the wall.
- Checks: watertight, one body, **0 islands starting in the air** (slices every 0.2 mm, Z 0 to 247.5);
  area flatter than 45 deg 6,569 mm2 (17,661 with the full trees).

```bash
python src/epi_top.py          # wrote Epitrochoid_keel_v4.stl (now writes v5; drop "struts" from epi_keel for v4)
```
Superseded and git-ignored: `Epitrochoid_refit_with_supports.stl` (47p3 + every tree, 2026-11-08),
`Epitrochoid_refit_with_supports_v2.stl` (that with the top-post changes, no keel; set `"keel": false`
in `epi_top` to rebuild it from the first) and `Epitrochoid_keel_v3.stl` (commit ffd6530).

v3 failed on the printer, 2026-11-25 about 11:00 MST: spaghetti from layer 75 (Z 15). Its keel was
masked 0.7 mm short of the post. The lowest point of its ridge (Z 13.65, beside the post) had nothing
under it, and every bump along the ridge (it climbs only about 5 deg with the track) started a new
island: 323 in all. The island check had reported them before slicing.

Slice, 2026-11-25 11:28 MST: `epitrochoid_keel_v4_matte_PLA_0.20mm_12h27m.gcode`, stock
`0.20mm Standard @Sovol SV06 ACE` with Orca supports off, matte rainbow PLA (220 / 210, 15 mm3/s,
fan 80 to 100%). Planner 11 h 52 min, 12 h 27 min with margin (Orca 9 h 37 min), 277.8 g, 1237
layers. Sent and started by Aaron 2026-11-25 about 11:30 MST.

v4 on the printer, 2026-11-25, cancelled 20:04 MST at layer 405 of 1237: its keel bottom climbed at
only 1 deg from its anchors, so each layer reached up to 10 mm into the air and hung loops of
filament. Strings collected on the tops of the 4.8 mm bed trees, and the nozzle (z-hop 0.4) knocked
three of them over (they stood 68 to 110 mm unbraced). With no trees under it, the track above them
could not be printed. A partial clog from hours paused hot also made the extruder slip, so the
runout switch tripped five times. Aaron cleared it with the needle and a cold pull.

## Naming

Short `snake_case` names, family first (`hypo_`, `liss_`, `cycloid_`,
`split_`, `bucket_`, `plinko_`, `merge_`), then what sets the piece apart.
Two-post pieces will get a span suffix: `_s` (short) and `_l` (long), for
example `merge_y_s.stl`, `merge_y_l.stl`.

## Span variants

Two versions of each two-post piece, from measurements of the physical set
(raw readings in `config/project.json`):

- short: 125.5 mm, socket inner wall to socket inner wall. Centre spacing not derived: which
  inner walls is unconfirmed.
- long: 156.2 mm gap between the outsides of the two sockets, remeasured by Aaron 2026-11-15
  12:30 MST (first reading 154.9, tape about 155). Centre spacing 185.8 mm: the gap plus a 29.6
  socket, which is the design diameter and has not been measured on the set.
- the set's plugs measure 25.4 mm.

The Pyrce007 pieces do not fit the set as imported: two-post pieces are 134.0 mm centre to
centre (232.1 for the out-and-back pieces and the clicky ramp), sockets are 27.0, plugs taper
from 27.0 to 26.6, and levels are 50 mm, against 25.6 / 25.75 and 47.3 here.

`src/refit.py` rebuilds an imported piece for the set (`refit` in `config/project.json`): the run
between the two posts is stretched or squeezed to the span with the posts left unchanged, heights
are scaled by 47.3 / 50, each socket gets a sleeve down to 25.6 for 16 mm with a 45 deg lead-out,
and the plugs are replaced by the fit-ladder plug. A source plug slot that ends in the wall is
closed with the post's own wall; one that opens into a window is left open to the top. Options in
the config take away the need for supports: `keel` (45 deg keel under the track between the
posts), `ceiling` (45 deg cone ceiling over a socket nothing passes through; the socket keeps its
16 mm), `gable` (a window top made into a 45 deg point) and `arch` (the shallow shoulders of a
round window top cut back to 45 deg). Output is `<name>_l` in `stl/custom`.

Design goal (Aaron, 2026-11-15 13:46 MST): a piece should need support only on its higher, floating side,
under a post that starts in the air. `clicky_5_half_l` meets it; `twopost_1loop_l` does not yet.

## Attribution

`stl/marbleworks/` is "Marbleworks Marble Mazes" by Pyrce007,
https://www.thingiverse.com/thing:4202442, licensed CC BY. Files are renamed
only; `ref/marbleworks/names.md` maps each to its original name.
`twopost_1loop_l` and `clicky_5_half_l` in `stl/custom` are modified from those pieces by
`src/refit.py` (span, heights and connectors changed), same licence.
The `Epitrochoid_*` files are modified from `epi_725` (refit, trees, keel, top post, loops removed), same licence.
