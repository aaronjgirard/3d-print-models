## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""OrcaSlicer presets for the I <3 MOM planter in HyperPLA+: the stock Sovol SV06 ACE presets from
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
    "sparse_infill_density": "15%",              # 10%
    "top_shell_layers": "5",                     # 3
    "top_shell_thickness": "1",                  # 0.8
    "outer_wall_speed": "100",                   # 200
    "inner_wall_speed": "180",                   # 270
    "sparse_infill_speed": "200",                # 300
    "internal_solid_infill_speed": "180",        # 200
    "top_surface_speed": "80",                   # 200
    "default_acceleration": "5000",              # 10000
    "outer_wall_acceleration": "3000",           # 6000
    "inner_wall_acceleration": "5000",           # 8000
    "top_surface_acceleration": "3000",          # 6000
    "enable_prime_tower": "0",                   # 1
    # this model
    "wall_loops": "6",                           # 2: the 2.6 mm pot wall is all perimeters (solid, watertight-ish)
    "bottom_shell_layers": "6",                  # 3: the bottom text runs through all 6 bottom layers (1.25 mm)
    "bottom_surface_pattern": "monotonic",       # monotonic: plain straight lines behind the bottom text
    "brim_type": "no_brim",                      # auto_brim: a brim would bridge the leg hinge gaps on the bed
    "skirt_loops": "1",                          # 0
    "elefant_foot_compensation": "0.15",         # 0.1: keeps the hinge gaps open on the first layer
}
FILAMENT = {
    # HyperPLA+ (a high-speed PLA+): a little hotter than basic PLA
    "nozzle_temperature_initial_layer": ["225"],   # 235
    "nozzle_temperature": ["220"],                 # 210
    "fan_min_speed": ["80"],                       # 50
    "fan_max_speed": ["100"],                      # 80
}
# what the bottom-text modifier sets (written into the 3MF by build_3mf.py)
MODIFIER = {
    "bottom_surface_pattern": "concentric",        # the letters' lines follow the letter shapes
    "internal_solid_infill_pattern": "concentric", # same in bottom layers 2 to 6
}

process = json.load(open(f"{src}/flat_process_0.20mm_Standard_atSovol_SV06_ACE.json"))
process.update(PROCESS)
process["name"] = "0.20mm Mom planter @Sovol SV06 ACE"
process["print_settings_id"] = process["name"]
process["from"] = "User"

filament = json.load(open(f"{src}/flat_filament_Generic_PLA_atSovol_SV06_ACE.json"))
filament.update(FILAMENT)
filament["name"] = "HyperPLA+ @Sovol SV06 ACE"
filament["filament_settings_id"] = [filament["name"]]
filament["from"] = "User"

machine = json.load(open(f"{src}/flat_machine_Sovol_SV06_ACE_0.4_nozzle.json"))
machine["printer_settings_id"] = machine["name"]

for name, d in (("machine", machine), ("process", process), ("filament", filament)):
    json.dump(d, open(f"{out}/{name}.json", "w"), indent=1, sort_keys=True)
json.dump({"process": PROCESS, "filament": FILAMENT, "bottom_text_modifier": MODIFIER},
          open(f"{out}/changes_from_stock.json", "w"), indent=1)
print("wrote presets to", out)
