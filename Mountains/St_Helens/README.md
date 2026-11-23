# Mount St. Helens relief models, pre-1980 and 2022

Updated 2026-11-13 12:36 MST (Rainier resliced to match; seam sizes added; 2022 lidar zip deleted)

Two prints at the same footprint, map scale and vertical exaggeration as `../Rainier/mount_rainier_5in_square_2x.stl`, so all three can sit side by side at one scale.

| file | surface | top | layers | filament | time |
|---|---|---|---|---|---|
| `mount_st_helens_pre1980_5in_square_2x.stl` | 1952 topography (USGS) | 20.72 mm | 170 | 59.8 g | 6h30m |
| `mount_st_helens_2022_5in_square_2x.stl` | Aug 2022 lidar + 3DEP | 17.78 mm | 146 | 59.6 g | 6h27m |
| `../Rainier/mount_rainier_5in_square_2x.stl` | (unchanged STL) | 30.93 mm | 256 | 72.7 g | 7h40m |

G-code sits next to each STL (`*_PLAplus_0.12mm_*.gcode`), sliced with `../../cli_slice/slice.sh relief ... --layer-height 0.12` (PLA+ olive green, High Temp plate, 5 mm brim, 15% adaptive cubic; 0.12 mm layers as in the Rainier 3MF). Times are the Klipper planner estimate plus 5%. Not uploaded. Rainier was resliced from its unchanged STL with the same command (2026-11-13 12:36 MST) so the three prints share settings and layer steps; its 3MF had Generic PLA, 12% gyroid, a variable 0.08 to 0.32 mm layer profile and an end G-code that parked at the front. Sliced tops: 30.97, 20.77 and 17.77 mm, within a layer of the STLs.

## Geometry (matched to Rainier)
The Rainier STL was fitted against 3DEP (rms misfit 0.03 mm): a 36.0 km UTM square centred on the summit, printed 127 mm wide on a 401 x 401 node grid (90 m spacing), with $z = 2 \cdot (127/36000) \cdot h = 0.007056\,h$ mm for elevation $h$ in metres above sea level, and a flat bottom at $z = 0$ (no added base). The St. Helens models use the same numbers, centred on the pre-1980 summit (UTM 10N 562350 E, 5116340 N) so the two prints register. Each node is the mean of the 9 x 9 block of 10 m cells around it. The lowest point (147 m, SW corner) leaves 1.04 mm of solid under it.

## Data
- `dem/pre1980/`: USGS ScienceBase item 650dbee5d34e823a027455f3, 10 m DEM of the summit and North Fork Toutle valley circa 1952, from 1:62,500 maps (80 ft contours). Covers 14% of the print area.
- `dem/lidar2022/`: Mosbrucker (2023), August 2022 airborne lidar of the crater, upper North Fork and South Fork Toutle, 3 ft, NAVD88 feet, https://doi.org/10.5066/P9ASCF0Q (1 GB zip, 5.1 GB tif inside; zip deleted 2026-11-13 after building the cache, metadata kept). Covers 13% of the print area, newest available at the summit.
- Rest of the modern surface: 3DEP 1 m lidar read remotely at 10 m, newest project first (WA_CentralWildfire_D22, then WA_FEMAHQ_2018_D18, WA_Mount_Adams_LiDAR_2016, WA_Western_South_2016), 0.5% gaps from the 3DEP 1/3 arc-second DEM (2025-08-13 release). URLs in `config.json`.
- Pre-1980 surface = modern surface with the 1952 DEM pasted in, feathered over 300 m inside its edge. Outside that DEM the 1980 changes (tephra, lahar deposits of a few metres) are below 0.03 mm at this scale.

## Seams (measured 2026-11-13 12:35 MST)
- 1952 DEM vs modern in the 300 m feather zone: median 7 m, 95th percentile 25 m, max 79 m (0.56 mm printed) at 6.2 km W, 4.3 km N of the summit, where the North Fork Toutle avalanche deposit reaches the edge of the 1952 coverage (modern 1071 m over 1952 991 m). That step is real 1980 fill, ramped over 300 m.
- 2022 lidar vs 3DEP 1 m along the lidar edge (hard switch, not feathered): median offset 0.1 m, median |diff| 0.4 m, 95th percentile 3.3 m, max 27 m (0.19 mm) at one steep spot 3.4 km E, 3.0 km N of the summit.

## Rebuild
```bash
python make_relief.py                                  # conda base (rasterio, manifold3d)
python make_relief.py --lidar-2022 /path/2022dem.tif   # only needed if the cache is deleted (re-download the zip)
```
`dem/cache/modern_10m.tif` is reused when present (delete it to re-mosaic); `modern_10m_source.tif` maps the source per cell (1 lidar 2022, 2 3DEP 1 m, 3 1/3 arc-second); `*_nodes.tif` are the 401 x 401 elevation grids printed.
