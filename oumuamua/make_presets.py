## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Build flat OrcaSlicer presets for the ʻOumuamua print: copy a cli_slice style
and apply the process overrides in presets/overrides.json (tree supports).
'''
import argparse, json, os, shutil

def main(cfg):
    here = os.path.dirname(os.path.abspath(cfg))
    ovr  = json.load(open(cfg))
    base = os.path.normpath(os.path.join(here, '..', ovr['base']))
    for f in ('printer.json', 'filament.json'):
        shutil.copy(os.path.join(base, f), os.path.join(here, f))
    prc = json.load(open(os.path.join(base, 'process.json')))
    prc.update(ovr['process'])
    prc['name'] = prc.get('name', 'process') + ' + tree supports'
    json.dump(prc, open(os.path.join(here, 'process.json'), 'w'), indent=4)
    print('presets from', base, 'with', len(ovr['process']), 'process overrides')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='presets/overrides.json')
    main(ap.parse_args().cfg)
