# Horse Heaven Hills survey, 3D print

Updated 2026-10-29 23:13 MDT

Terrain of the WA DNR 3D survey area cut to `9_Sq_Mi_3D_Boundary.kmz`, with a
blind hole at each of the 145 recovered passive receivers for paint.

| path | what |
|---|---|
| `config.json` | every parameter: sizes, exaggeration, holes, DEM tiles, input paths |
| `make_print.py` | DEM fetch, solid build, STL, report |
| `preview.py` | QC render of the STL |
| `out/hhh_survey_vexag3.stl` | the print, binary STL in mm |
| `out/hhh_survey_vexag3_dem_1m.tif` | 1 m DEM mosaic over the survey (NAD83 / UTM 11N, EPSG:26911), cached so reruns skip the download |
| `out/*_receivers.csv` | receivers, UTM, distance to the boundary, hole position and shift |
| `out/*_report.json`, `out/*_preview.png` | build numbers and the QC render |

Run under conda `base` (needs `pip install manifold3d`):
`python make_print.py && python preview.py`.

## Build of 2026-10-29 23:11 MDT (holes 3.0 to 1.5 mm)

- DEM: USGS 3DEP 1 m lidar, WA_FEMAHQ_2018 tiles x26y510 and x27y510; WA_ColumbiaValley_2018 x27y510 fills any gaps. Read as windowed remote reads.
- Model: 170.0 x 190.0 x 34.9 mm, map scale 1:29,422, vertical exaggeration 3. Ground 247 to 441 m becomes 15.0 mm (thinnest terrain) to 34.9 mm.
- Holes: 1.5 mm diameter (3.0 mm in the 22:51 build, judged too big), 2.0 mm deep below the lowest point of each rim, so the floors sit at 14.0 mm or above.
- Receivers: `receivers_post_plot_deployed.csv` (150 deployed) less the 5 not recovered (1019, 1063, 1084, 1090, 1148), which gives 145. 1138 is kept: it was recovered with a failed drive.
- 12 holes within 1.55 mm of the edge (0.75 mm radius plus 0.8 mm wall) were moved inward, by at most 1.6 mm (46 m ground). 1149 lies 0.7 m outside the polygon. The shifts are in the receivers CSV.
- Checks: manifold status NoError, genus 0, STL has every edge shared by exactly two triangles, 1.34 M triangles, 681 cm^3.
- North is grid north of UTM 11N, about 1.4 deg off true north here.
