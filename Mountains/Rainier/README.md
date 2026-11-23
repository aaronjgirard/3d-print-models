# Mount Rainier relief, with the Disappointment Cleaver route

Updated 2026-11-13 23:33 MST (print started again)

Geometry of the base model is described in `../St. Helens/README.md` (36 km UTM square centred on the summit, 127 mm wide, VE 2x). The best-fit centre is UTM 10N 594478 E, 5189568 N (rms misfit 0.026 mm).

| file | what | top | layers | filament | time |
|---|---|---|---|---|---|
| `mount_rainier_5in_square_2x.stl` | original, unchanged | 30.93 mm | 256 | 72.7 g | 7h40m |
| `mount_rainier_5in_square_2x_dc_route.stl` | + climbing route ridge and two pads | 32.12 mm | 267 | 72.8 g | 7h42m |
| `mount_rainier_5in_square_3x_dc_route.stl` | same at VE 3x (terrain heights x 1.5) | 47.58 mm | 395 | 93.8 g | 9h59m |
| `mount_rainier_5in_square_2p5x_dc_route_text.stl` | VE 2.5x, route, wall text (chosen) | 39.85 mm | 331 | 83.5 g | 8h59m |

## Route version (2026-11-13 21:09 MST)
- Route: Disappointment Cleaver, the most climbed route (70 to 74% of registered climbers, NPS mountaineering reports 2012 to 2014). Path from OpenStreetMap trails, shortest trail path Skyline Trailhead (Paradise) to Camp Muir to Columbia Crest: Skyline Trail, Alta Vista Trail, Pebble Creek Trail, Camp Muir Route, Disappointment Cleaver Route (OSM ways 371682134 and 819949144). Saved in `route_dc.csv`. The route above Camp Muir changes every season; the OSM line is one recent version.
- Ridge: 40.5 mm long, 0.9 mm wide (the Kilauea receiver dot width), top 1.2 mm above the highest terrain under it, sunk 0.6 mm. It stands 1.2 to 2.7 mm proud depending on side slope.
- Pads: 3 mm across, top 1.5 mm above the highest terrain under them, at Camp Muir (3.96 mm on the downhill side, it sits on the steep Muir Snowfield) and at the Skyline Trailhead (2.85 mm downhill side).
- G-code: `mount_rainier_5in_square_2x_dc_route_PLAplus_0.12mm_7h42m.gcode`, sliced with `../../cli_slice/slice.sh relief ... --layer-height 0.12`, same settings as the original and the St. Helens prints. Klipper estimate plus 5%. Not uploaded.

## 3x version (2026-11-13 21:19 MST)
`mount_rainier_5in_square_3x_dc_route.stl`: the original heights multiplied by 1.5 (exact, since the base is at z = 0), then the same route, ridge and pads in mm. Steeper ground makes the ridge stand 1.2 to 3.4 mm proud and the Camp Muir pad 5.2 mm on its downhill side (trailhead 3.5 mm). G-code `mount_rainier_5in_square_3x_dc_route_PLAplus_0.12mm_9h59m.gcode`, same slice settings. Not uploaded.

## 2.5x version with wall text (2026-11-13 21:39 MST)
Chosen over 1x (too flat), 2x and 3x (too steep). `mount_rainier_5in_square_2p5x_dc_route.stl` is the original heights x 1.25 plus the route; the ridge stands 1.2 to 3.0 mm proud and the Camp Muir pad 1.5 to 4.6 mm. `mount_rainier_5in_square_2p5x_dc_route_text.stl` adds text recessed 0.8 mm (Arial Bold, 5 mm cap height, z 1.1 to 6.1 mm) with `../../WA_DNR/add_wall_text.py`, as on Kilauea and HHH: "Mount Rainier" on the south wall, 34.2 mm from its west end, and "1:283,465   VE 2.5×" (127 mm = 36 km) on the east wall, 83.5 mm from its south end (layout changed 2026-11-13 22:34 MST; it was east and north, centred). The walls are only 4 to 16 mm tall, so the cap height is 5 mm, not Kilauea's 7 mm, and each line was slid along its wall to the spot with the most wall above the actual letter tops: 1.92 mm (south) and 3.89 mm (east) at the tightest point.

G-code `mount_rainier_5in_square_2p5x_dc_route_text_PLAplus_0.12mm_8h59m.gcode`, same relief preset and 0.12 mm layers (filament profile "PLA+ 2.0 Olive Green", 210/220 C, 60 C High Temp plate), printed in white PLA+ of the same brand and style as the grey Kilauea. Uploaded and started 2026-11-13 22:37 MST; clogged on the first layer and cancelled at 23:09 (1.85 m of filament). The nozzle had idled at 210 C for about 45 min during the runout sensor repair and the filament came out with a cooked blob on the end; it was cut off and reloaded, extruded cleanly, and the print restarted 2026-11-13 23:21 MST; that start was cancelled before extruding (webcam troubleshooting) and the print started again 2026-11-13 23:33 MST with a cold nozzle.

## Rebuild
```bash
python add_route.py                       # conda base; reads route_dc.csv, settings in route_config.json
python add_route.py --fetch               # re-download the OSM trails and re-route
python add_route.py --fetch --osm-json saved_overpass.json
python add_route.py --z-scale 1.5 --out mount_rainier_5in_square_3x_dc_route.stl
python add_route.py --z-scale 1.25 --out mount_rainier_5in_square_2p5x_dc_route.stl
python ../../WA_DNR/add_wall_text.py mount_rainier_5in_square_2p5x_dc_route.stl south.stl --text "Mount Rainier" --side south --cap 5 --zc 3.6 --along 34.2
python ../../WA_DNR/add_wall_text.py south.stl mount_rainier_5in_square_2p5x_dc_route_text.stl --text "1:283,465   VE 2.5×" --side east --cap 5 --zc 3.6 --along 83.5
```
