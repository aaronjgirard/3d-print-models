#!/bin/bash
## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
## slice a model or project 3MF with the presets of one style (a subfolder
## here: relief, tall_thin, ...), check the G-code, then open it in
## OrcaSlicer's preview. never uploads or prints. the time lines in the G-code
## are rewritten with klipper_time.py (klipper planner + margin).
##
## usage: slice.sh <style> <model.stl|project.3mf> [plate] [outdir] [extra orca flags...]
##   style   subfolder holding printer.json, process.json, filament.json
##   plate   0 = all plates (default), N = plate N of a 3MF
##   outdir  default ./out
##   extra flags override the presets, e.g. --layer-height 0.2 --brim-width 5
##   OPEN=0 slice.sh ... skips opening the preview
##   PAD=1  slice.sh ... pads so file progress (Obico) tracks time to within
##                       PAD percentage points (default 0.5; PAD=0 no padding)
##   FIL=filament_brown.json slice.sh ... uses another filament file in the
##                       style folder (default filament.json)
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
ORCA="${ORCA:-/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer}"
usage="usage: slice.sh <style> <model.stl|project.3mf> [plate] [outdir] [flags...]"
style="${1:?$usage}"
model="${2:?$usage}"
plate="${3:-0}"
outdir="${4:-out}"
shift $(( $# < 4 ? $# : 4 ))
pre="$here/$style"
[ -f "$pre/printer.json" ] || { echo "no presets in $pre; styles: $(cd "$here" && ls -d */ | tr -d / | tr '\n' ' ')" >&2; exit 1; }

mkdir -p "$outdir"
"$ORCA" --slice "$plate" --outputdir "$outdir" \
    --load-settings "$pre/printer.json;$pre/process.json" \
    --load-filaments "$pre/${FIL:-filament.json}" \
    "$@" "$model"

## orca names the file plate_N.gcode, N = plate index (1 for an stl)
gcode="$(ls -t "$outdir"/plate_*.gcode 2>/dev/null | head -1)"
[ -n "$gcode" ] || { echo "no G-code in $outdir" >&2; exit 1; }

## checks: required macros present, END_PRINT last, no G28 after the last layer
fail=0
for tag in START_PRINT SET_VELOCITY_LIMIT EXCLUDE_OBJECT; do
    grep -q "^$tag" "$gcode" || { echo "MISSING: $tag"; fail=1; }
done
tail_cmds="$(grep -v -e '^;' -e '^$' "$gcode" | tail -8)"
last="$(echo "$tail_cmds" | grep -v '^M73' | tail -1)"
[ "$last" = "END_PRINT" ]        || { echo "LAST COMMAND IS NOT END_PRINT: $last"; fail=1; }
echo "$tail_cmds" | grep -q G28  && { echo "G28 IN END G-CODE"; fail=1; }
[ $fail -eq 0 ] && echo "checks passed: START_PRINT, SET_VELOCITY_LIMIT, EXCLUDE_OBJECT, ends with END_PRINT"
## orca runs 1.0-1.4x low on klipper: replace its time lines with the planner estimate
grep -m1 "estimated printing time" "$gcode" | sed 's/^; estimated/orca estimated/' || true
python3 -I "$here/klipper_time.py" "$gcode" --write --pad "${PAD:-0.5}" || fail=1
echo "$gcode"

## OPEN=0 skips the preview (for quick tests)
[ $fail -eq 0 ] && [ "${OPEN:-1}" = "1" ] && open -a OrcaSlicer "$gcode"
exit $fail
