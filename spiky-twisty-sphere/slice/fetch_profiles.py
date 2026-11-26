## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Fetch the stock Sovol SV06 ACE presets from the OrcaSlicer v2.5.0 source and flatten
their `inherits` chains, one self-contained JSON file per preset (from mines-relief/fetch_profiles.py).

Usage: python3 fetch_profiles.py <outdir>
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = "https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/v2.5.0/resources/profiles/"
VENDORS = ("Sovol", "OrcaFilamentLibrary")
WANTED = (("machine", "Sovol SV06 ACE 0.4 nozzle"),
          ("process", "0.20mm Standard @Sovol SV06 ACE"),
          ("filament", "Generic PLA @Sovol SV06 ACE"))


def get(url, dst):
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    if not os.path.exists(dst):
        with urllib.request.urlopen(url, timeout=30) as r:
            open(dst, "wb").write(r.read())
    return json.load(open(dst))


def main(out):
    paths = {}
    for vendor in VENDORS:
        idx = get(ROOT + vendor + ".json", os.path.join(out, "cache", vendor + ".json"))
        for key in ("machine_list", "process_list", "filament_list"):
            for item in idx.get(key, []):
                paths.setdefault((key.split("_")[0], item["name"]), (vendor, item["sub_path"]))
    for kind, name in WANTED:
        merged, chain = {}, []
        while name:
            vendor, sub = paths[(kind, name)]
            d = get(ROOT + vendor + "/" + urllib.parse.quote(sub), os.path.join(out, "cache", vendor, sub))
            chain.append(name)
            for k, v in d.items():
                merged.setdefault(k, v)          # the child's value wins over its parent's
            name = d.get("inherits")
        merged.pop("inherits", None)
        fn = f"flat_{kind}_{chain[0].replace(' ', '_').replace('@', 'at')}.json"
        json.dump(merged, open(os.path.join(out, fn), "w"), indent=1, sort_keys=True)
        print(f"{kind}: {' <- '.join(chain)} ({len(merged)} keys) -> {fn}")


if __name__ == "__main__":
    main(sys.argv[1])
