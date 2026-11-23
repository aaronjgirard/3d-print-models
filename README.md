# 3D print models

Updated 2026-11-22 21:59 MST

Models, generator scripts, slicer presets and printer notes from my Sovol SV06 ACE.

## About me
I bought a Sovol SV06 ACE (Klipper, 220 x 220 mm bed) that I am learning to use, playing with and having fun with: tuning it, breaking it, fixing it, and printing whatever seems fun. Most of the models are built by code (Python with trimesh and manifold3d) so they can be changed and rebuilt. I like open source, and I learn a lot from the people who share their designs and settings, so this is me sharing back. If you found this by chance, welcome; take what is useful.

## What's here

| folder | what |
|---|---|
| `Marble_Run/` | Marbleworks-compatible marble run: generated buckets, tubes, cascades, merges, plus Pyrce007's set (see licenses below) |
| `Kilauea/` | 190 mm relief of the Kilauea summit with the 2023 nodal array as raised dots |
| `WA_DNR/` | relief of the Horse Heaven Hills (WA) CO2 site survey with its receivers as raised dots |
| `Mountains/` | Mount Rainier (with the Disappointment Cleaver route) and Mount St. Helens before 1980 and in 2022, all at one scale |
| `dragon-egg/` | spirit dragon and a two-part egg, with OrcaSlicer presets |
| `secret_drawers/` | dial and two-drawer puzzle box |
| `biserica_neagra_3dprint/` | the Black Church of Brasov, rebuilt from a public scan as a printable solid |
| `CSM_GP_logos/` | Colorado School of Mines Geophysics logo and banner plaques |
| `train-rails/` | straight, 22.5 degree curve and fit-test piece that join a battery Christmas-train set, with wood-grain ties and full-plate layouts |
| `VLAD_4in_quarter_thick.3mf` | small name plate |
| `cli_slice/` | OrcaSlicer command-line presets, plus a Klipper-accurate print-time estimator |
| `sv06.sh` | run the printer from a terminal through Moonraker (`3dprint`, `3dstatus`, ...) |
| `Printer_Fix/` | longboard pads, a fix Sovol suggested that helped |
| `printer_diagnostics/`, `maintenance/` | input shaping, cruise ratio and camera-light fixes, with before and after configs |

G-code is not included: it is specific to my printer and rebuilds from the models with `cli_slice/slice.sh`. Each folder's README says how its models were made and how to rebuild them.

## License: what you can do
Everything here is mine and licensed under the [Apache License 2.0](LICENSE) unless the exceptions below say otherwise. That covers the models (STL, 3MF), the scripts, the presets and the notes. In plain terms:

- **Share:** copy and pass on any of it, changed or not.
- **Mix and remix:** change it, combine it with your own or other people's work, and publish the result under your own terms.
- **Reuse:** use the code and models in your own projects, personal or commercial.
- **Sell:** sell prints, and sell or bundle the files, with no fee and no need to ask.
- **When you pass the files on:** include a copy of the [LICENSE](LICENSE) and the [NOTICE](NOTICE) file, and say what you changed.
- **What it does not give:** any right to use my name or anyone's trademarks to endorse what you make, and any warranty. Prints are provided as is; check fit and strength yourself before trusting a part with anything that matters.

The license text is the legal version; this list is only a summary.

## Exceptions (not Apache-2.0)

| what | owner | license |
|---|---|---|
| `Marble_Run/stl/marbleworks/`, `Marble_Run/ref/marbleworks/` | [Pyrce007, Marbleworks Marble Mazes](https://www.thingiverse.com/thing:4202442) | CC BY (see `Marble_Run/ref/marbleworks/LICENSE.txt`); renamed only |
| `Marble_Run/stl/custom/twopost_1loop_l.stl`, `clicky_5_half_l.stl` | remixes of Pyrce007's `twopost_1loop` and `clicky_5_half` | CC BY, credit Pyrce007; my changes (made by `src/refit.py`) are Apache-2.0 |
| `biserica_neagra_3dprint/*.stl` | built from [Biserica Neagra din Brasov](https://sketchfab.com/3d-models/biserica-neagra-din-brasov-8458157f7a71408189c4d630ce82133b) by Institutul National al Patrimoniului (cimec) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), credit cimec; `make_stl.py` is Apache-2.0 |
| the logo artwork in `CSM_GP_logos/` | Colorado School of Mines, Department of Geophysics | trademark, not licensed here; the plaque geometry around it is Apache-2.0 |

Elevation data in `Mountains/` comes from USGS (public domain); sources are listed in each README.

## Citing the survey models
The Kilauea and WA DNR reliefs show real seismic arrays. If you use them for anything beyond printing, please cite the work they come from (citations are updated as papers come out):

- **Kilauea:**
  - O'Connell, D. R. H., and A. J. Girard (2026). 2023 Kilauea horizontal-component signal/noise assessment of a large three-component nodal array. *Seismica*, 5(2). https://doi.org/10.26443/seismica.v5i2.3013
  - Kramer, R. L., R. Denlinger, A. J. Girard, D. R. H. O'Connell, S. Roecker, G. Lin, N. Bennington, A. Flinders, and E. Vinarski (submitted). A high-density, active and passive seismic imaging experiment at the summit of Kilauea Volcano, Hawai'i. *Seismological Research Letters*.
  - Denlinger, R., G. Lin, M. Haney, S. Roecker, N. Bennington, A. Flinders, D. O'Connell, and E. Vinarski (2023). Active and passive seismic interferometry of Kilauea volcano [Data set]. International Federation of Digital Seismograph Networks. https://doi.org/10.7914/gqdb-hs97
- **WA DNR (Horse Heaven Hills):**
  - Girard, A. J., D. H. R. O'Connell, A. Stolzmann, L. Florea, J. Shragge, M. Oristaglio, C. Morgan, J. Turner, R. Beal, A. Bauer, and S. P. Reidel (submitted). An active- and passive-source nodal seismic dataset for CO2 sequestration site characterization in the Columbia River Basalts of south-central Washington, U.S.A. *Seismological Research Letters*.

## Contact
Questions, fixes and remixes are welcome through GitHub issues.
