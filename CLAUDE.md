# 3d-print-models: rules for new work

Updated 2026-11-22 21:15 MST

This folder is the public repo `github.com/aaronjgirard/3d-print-models`. Every model Aaron makes goes here and is Apache-2.0 by default.

- **New models:** put each in its own folder with a README (what it is, how it was built, the rebuild command). The root `LICENSE` covers it; add it to the "What's here" table in the root `README.md` and refresh that file's "Updated" line.
- **Third-party models:** before committing anything Aaron did not make, find its source and license (check `mdls -name kMDItemWhereFroms`, 3MF metadata, the model page). Permissive with attribution (CC BY, CC0, MIT, ...): commit it with credit in `NOTICE` and the root README "Exceptions" table, and mark remixes the same way. Non-commercial, no-derivatives, "standard digital file license", or unknown: add it to `.gitignore` and keep it local; ask Aaron if unsure.
- **Trademarks** (logos, brand names): never relicensed; note them as exceptions.
- **Survey and research data:** cite the source papers in the folder README and the root README "Citing" section; update citations when papers are published.
- **Size:** G-code is never committed. Keep each file under 100 MB (GitHub limit); commit only the current version of large reliefs and git-ignore superseded ones, keeping their rebuild commands in the README. Raw inputs (DEMs, scans) stay out.
- **3MF projects:** fill the project License field with `Apache-2.0` (or the third-party license) when saving in OrcaSlicer.
- Commits are authored by Aaron only; no Claude co-author line.
