# ʻOumuamua

Updated 2026-11-23 21:52 MST

ʻOumuamua, the first interstellar object seen passing through the Solar System, at 1:2000, made from ESO's artist's 3D model, with a name and scale plaque and a display stand. ESO gives its length as about 400 m, so the rock is 200 mm long (40 x 34 mm across). The OrcaSlicer project `oumuamua.3mf` has three plates:

1. **Rock**: lies on its side with the thinnest axis on Z, turned 45 degrees to fit the bed (148 x 148 mm footprint); the curved underside prints on organic tree supports (set on this object only).
2. **Plaque**: 64 x 32 mm (2.5 x 1.25 in) with raised "ʻOumuamua" and "1:2000" (Arial Bold, the ʻokina is U+02BB). The project pauses after layer 12 and before layer 13 (Z 2.65 mm, the first layer above the plate face) prints, so the text and border print in the swapped filament.
3. **Stand** (white PLA): a 200 x 48 mm base, as long as the rock and 4 mm wider each side, with two posts 110 mm apart whose tops are cups cast from the rock's underside, 0.3 mm clearance, and only as high as the rock can lift straight out of. The rock sits 32 mm above the base. Between the posts, under the rock, a 3 mm deep slot holds the plaque at 60 degrees with a small prop behind it; the plaque top clears the rock by 5.7 mm. Turned 45 degrees on its plate.

| file | what |
|---|---|
| `make_stl.py`, `config.json` | load the OBJ, weld the UV-seam vertices (the shell is then closed), align the principal axes, scale to 400 m at 1:2000, decimate to 400k triangles, turn 45 degrees on the bed, rest on z=0 |
| `make_plaque.py`, `plaque.json` | the plaque: 2.4 mm plate, raised 1.2 mm border and text 0.8 mm high |
| `make_stand.py`, `stand.json` | the stand: cups from the rock's lower envelope (triangles rasterized on a 0.25 mm grid), plaque slot and prop |
| `build_project.py`, `project.json` | the three-plate 3MF: `cli_slice/relief` settings over a saved Orca project config, tree supports on the rock, the pause on the plaque plate |
| `make_presets.py`, `presets/overrides.json` | flat presets with tree supports, for slicing the rock STL on its own |
| `add_pause.py` | insert a filament-change pause at the start of one layer of an already sliced G-code |
| `oumuamua_1to2000.stl`, `oumuamua_stand.stl` | the rock and the stand, credit ESO/M. Kornmesser (see below) |
| `oumuamua_plaque.stl` | the plaque |
| `oumuamua_on_stand.stl`, `oumuamua.3mf` | rock placed on the stand (for checks) and the project; rebuilt by the commands below, not in git |

## Rebuild
```bash
../biserica_neagra_3dprint/.venv/bin/python make_stl.py           # --scale 2500 for another size
conda run -n marble-run python make_plaque.py                     # edit plaque.json to change the text or size
conda run -n marble-run python make_stand.py                      # after make_stl.py; edit stand.json for the layout
conda run -n marble-run python -I build_project.py
../cli_slice/slice.sh relief oumuamua.3mf 1 out                    # plates 1, 2, 3
```
Sliced 2026-11-23 (Klipper estimates with margin):

| plate | layers | filament | time |
|---|---|---|---|
| 1 rock | 171 | 53 g PLA+ | 3 h 22 min |
| 2 plaque | 16 | 6 g PLA+, swap at layer 13 | 17 min |
| 3 stand | 240 | 46 g white PLA | 1 h 52 min |

At the plaque pause, swap the filament, then `RESUME`.

## Source and license
Model: ESO/M. Kornmesser, ʻOumuamua (3D model), European Southern Observatory, https://www.eso.org/public/products/models3d/oumuamua/ (downloaded 2026-11-23). Put into `raw/`: the OBJ and Cinema 4D zips and the TIFF render from that page.

`oumuamua_1to2000.stl` is built from that model, and `oumuamua_stand.stl` has cups cast from it; both keep ESO's terms, not Apache-2.0: ESO asks for the full credit line, **ESO/M. Kornmesser**, shown visibly for fee-free use, and says the model "is not available for sale". ESO's copyright page puts its images, videos and music under CC BY 4.0 but does not name 3D models. The ESO downloads (`raw/`) are not in git. The plaque, scripts and presets are Apache-2.0.
