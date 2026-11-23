# Biserica Neagra (Black Church), Brasov

Updated 2026-11-22 21:15 MST

A watertight, printable 180 mm solid rebuilt from a public photogrammetry scan of the Black Church in Brasov, Romania.

| file | what |
|---|---|
| `make_stl.py`, `config.json` | keep the church meshes of the scan, rotate to z up, scale, voxelize, seal the bottom, fill, marching cubes, decimate (`python make_stl.py`) |
| `biserica_neagra_ready.stl` | the print |
| `work/` | test build and QC images |

The scan (`raw/biserica_neagra_din_brasov.glb`, 200 MB) is not included; download it from the Sketchfab page below and place it in `raw/`.

## Credit and license
Source scan: [Biserica Neagra din Brasov](https://sketchfab.com/3d-models/biserica-neagra-din-brasov-8458157f7a71408189c4d630ce82133b) by Institutul National al Patrimoniului (cimec), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The STLs here are adapted from that scan (non-church meshes dropped, solidified, rescaled and decimated) and are shared under CC BY 4.0; credit cimec when you share them. `make_stl.py` is Apache-2.0.
