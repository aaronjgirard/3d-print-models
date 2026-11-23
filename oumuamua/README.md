# 'Oumuamua

Updated 2026-11-23 15:22 MST

'Oumuamua, the first interstellar object seen passing through the Solar System, at 1:2000, made from ESO's artist's 3D model, with a small name and scale plaque. ESO gives its length as about 400 m, so the print is 200 mm long (40 x 34 mm across). It lies on its side with the thinnest axis on Z, turned 45 degrees so it fits the bed diagonally (148 x 148 mm footprint), and the curved underside prints on organic tree supports.

| file | what |
|---|---|
| `make_stl.py`, `config.json` | load the OBJ, weld the UV-seam vertices (the shell is then closed), align the principal axes, scale to 400 m at 1:2000, decimate to 400k triangles, turn 45 degrees on the bed, rest on z=0 |
| `make_presets.py`, `presets/overrides.json` | flat OrcaSlicer presets: the `cli_slice/relief` style (PLA+, 0.20 mm, adaptive cubic) plus organic tree supports from the plate only, 30 degree threshold, 5 mm brim |
| `add_pause.py` | insert a filament-change pause at the start of one layer of a sliced G-code |
| `make_plaque.py`, `plaque.json` | 64 x 32 mm (2.5 x 1.25 in) plaque, 2.4 mm plate with a raised 1.2 mm border and raised text ("ʻOumuamua", "1:2000", Arial Bold), 0.8 mm high |
| `oumuamua_1to2000.stl` | the rock (local only, see below) |
| `oumuamua_plaque.stl` | the plaque |

## Rebuild
```bash
../biserica_neagra_3dprint/.venv/bin/python make_stl.py           # --scale 2500 --rotz 0 for another size or placement
python3 -I make_presets.py
conda run -n marble-run python make_plaque.py                     # edit plaque.json to change the text or size
../cli_slice/slice.sh ../oumuamua/presets oumuamua_1to2000.stl 0 out
../cli_slice/slice.sh relief oumuamua_plaque.stl 0 out
```
Sliced 2026-11-23: the rock is 171 layers, 53 g of PLA+, about 3 h 22 min; the plaque is 16 layers, 6 g, about 17 min (Klipper estimates with margin).

For two-color plaque text, `add_pause.py` puts `M117 Change filament` and `PAUSE` at the start of layer 13 (Z 2.65 mm, the first layer above the plate face at 2.4 mm). Swap the filament at the pause, then `RESUME`. Rerunning it on the same file does nothing.
```bash
python3 -I add_pause.py oumuamua_plaque_PLAplus_0.20mm_17m.gcode --layer 13    # then rename with _pause13
```

## Source and license
Model: ESO/M. Kornmesser, 'Oumuamua (3D model), European Southern Observatory, https://www.eso.org/public/products/models3d/oumuamua/ (downloaded 2026-11-23). Put into `raw/`: the OBJ and Cinema 4D zips and the TIFF render from that page.

ESO asks for the full credit line, shown visibly, for fee-free use, and says the model "is not available for sale". ESO's copyright page puts its images, videos and music under CC BY 4.0 but does not name 3D models, so the license of the model is not settled. Until it is, `raw/` and the rock STL stay out of git. The plaque, scripts and presets are Apache-2.0.
