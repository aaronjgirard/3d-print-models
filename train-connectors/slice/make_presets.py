## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Write the OrcaSlicer presets for the coupler plate in black PLA: the stock Sovol SV06 ACE presets from
OrcaSlicer 2.5.0 (flattened by fetch_profiles.py) with the changes below. Stock values in the comments.

Usage: python3 make_presets.py <flattened-presets-dir> <outdir>
"""
import json
import sys

src, out = sys.argv[1], sys.argv[2]

PROCESS = {
    # standing changes (print-settings skill)
    "top_solid_infill_flow_ratio": "1",          # 0.8
    "sparse_infill_pattern": "gyroid",           # crosshatch
    "top_shell_layers": "5",                     # 3
    "top_shell_thickness": "1",                  # 0.8
    "bottom_shell_layers": "4",                  # 3
    "inner_wall_speed": "180",                   # 270
    "sparse_infill_speed": "200",                # 300
    "internal_solid_infill_speed": "180",        # 200
    "top_surface_speed": "80",                   # 200
    "default_acceleration": "5000",              # 10000
    "outer_wall_acceleration": "3000",           # 6000
    "inner_wall_acceleration": "5000",           # 8000
    "top_surface_acceleration": "3000",          # 6000
    "enable_prime_tower": "0",                   # 1
    # small functional parts that must fit (pins, holes, a kingpin in a 4.7 hole)
    "wall_loops": "4",                           # 2
    "sparse_infill_density": "40%",              # 10%
    "outer_wall_speed": "100",                   # 200
    "xy_hole_compensation": "0.1",               # 0: the hole sizes in coupler.py count on it
    "elefant_foot_compensation": "0.15",         # 0.1
    "reduce_crossing_wall": "1",                 # 0 (avoid crossing walls)
    "brim_type": "outer_only",                   # auto_brim: the kingpins stand 9.5 tall on a 6.6 x 4.55 head
    "brim_width": "3",                           # 5: kept narrow, the parts sit 6 apart
    "skirt_loops": "1",                          # 0: primes the nozzle before the small parts
    # top surface pattern stays monotonic line and bottom stays monotonic: on parts 4 to 9 mm across,
    # Archimedean chords would only make fragments
}
FILAMENT = {
    # black PLA, as for the track (train-track/README.md)
    "nozzle_temperature_initial_layer": ["220"],   # 235
    "nozzle_temperature": ["210"],                 # 210
    "filament_max_volumetric_speed": ["18"],       # 21
    "fan_min_speed": ["80"],                       # 50
    "fan_max_speed": ["100"],                      # 80
    "slow_down_layer_time": ["8"],                 # 6: the kingpins' top layers print alone and are tiny
}

process = json.load(open(f"{src}/flat_process_0.20mm_Standard_atSovol_SV06_ACE.json"))
process.update(PROCESS)
process["name"] = "0.20mm Small functional @Sovol SV06 ACE"
process["print_settings_id"] = process["name"]
process["from"] = "User"

filament = json.load(open(f"{src}/flat_filament_Generic_PLA_atSovol_SV06_ACE.json"))
filament.update(FILAMENT)
filament["name"] = "Black PLA @Sovol SV06 ACE"
filament["filament_settings_id"] = [filament["name"]]
filament["from"] = "User"

machine = json.load(open(f"{src}/flat_machine_Sovol_SV06_ACE_0.4_nozzle.json"))
machine["printer_settings_id"] = machine["name"]

for name, d in (("machine", machine), ("process", process), ("filament", filament)):
    json.dump(d, open(f"{out}/{name}.json", "w"), indent=1, sort_keys=True)
json.dump({"process": PROCESS, "filament": FILAMENT}, open(f"{out}/changes_from_stock.json", "w"), indent=1)
print("wrote presets to", out)
