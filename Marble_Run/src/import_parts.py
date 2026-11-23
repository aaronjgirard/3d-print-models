## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Copy the Marbleworks (Pyrce007) STLs and the 1-4 pitch tubes into the project
under short names.

Marbleworks STLs are read straight from the Thingiverse zips and renamed with
config/marbleworks_names.json; their images, README and LICENSE go to the ref
folder. Tubes are copied from the project root with the "tubes" table in
config/project.json. Existing outputs are kept unless --force.

Usage:
    python src/import_parts.py ZIP [ZIP ...] [--cfg config/project.json]
        [--names config/marbleworks_names.json] [--force]
'''
import argparse
import json
import os
import shutil
import zipfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_member(zf, info, path, force):
    '''
    Write one zip member to path, skipping it if path exists and not force.

    Returns:
        bool: True if the file was written.
    '''
    if os.path.exists(path) and not force:
        return False
    with zf.open(info) as src, open(path, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    return True


def import_marbleworks(zips, names, stl_dir, ref_dir, force=False):
    '''
    Extract the renamed STLs and the reference files from the Marbleworks zips.

    Args:
        zips    (list): paths to the Thingiverse zip files
        names   (dict): original STL stem -> short name
        stl_dir (str) : output folder for the STLs
        ref_dir (str) : output folder for images, README and LICENSE
        force   (bool): overwrite existing files

    Returns:
        dict: original stem -> written path, for every STL found
    '''
    img_dir = os.path.join(ref_dir, 'img')
    for d in (stl_dir, ref_dir, img_dir):
        os.makedirs(d, exist_ok=True)
    done = {}
    for zp in zips:
        with zipfile.ZipFile(zp) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ## only flat names are trusted, never paths stored in the zip
                folder, base = os.path.split(info.filename)
                stem, ext    = os.path.splitext(base)
                if folder == 'files' and ext.lower() == '.stl':
                    if stem not in names:
                        print(f'  no short name for {base}, skipped')
                        continue
                    out = os.path.join(stl_dir, names[stem] + '.stl')
                    write_member(zf, info, out, force)
                    done[stem] = out
                elif folder == 'images':
                    out = os.path.join(img_dir, names.get(stem, stem) + ext.lower())
                    write_member(zf, info, out, force)
                elif folder == '' and base in ('README.txt', 'LICENSE.txt'):
                    write_member(zf, info, os.path.join(ref_dir, base), force)
    miss = sorted(set(names) - set(done))
    if miss:
        print('  names with no STL in the zips:', ', '.join(miss))
    return done


def import_tubes(table, src_dir, out_dir, force=False):
    '''
    Copy the tube STLs from src_dir to out_dir under their short names.

    Returns:
        list: written paths
    '''
    os.makedirs(out_dir, exist_ok=True)
    done = []
    for src, dst in table.items():
        sp, dp = os.path.join(src_dir, src), os.path.join(out_dir, dst)
        if not os.path.exists(sp):
            print(f'  missing tube {sp}')
            continue
        if force or not os.path.exists(dp):
            shutil.copy2(sp, dp)
        done.append(dp)
    return done


def write_name_table(names, path):
    '''
    Write a markdown table of short name -> original Marbleworks name.
    '''
    rows = ['| file | original name |', '|---|---|']
    rows += [f'| `{v}.stl` | {k} |' for k, v in sorted(names.items(), key=lambda kv: kv[1])]
    with open(path, 'w') as f:
        f.write('\n'.join(rows) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('zips'   , nargs='+')
    ap.add_argument('--cfg'  , default=os.path.join(root, 'config', 'project.json'))
    ap.add_argument('--names', default=os.path.join(root, 'config', 'marbleworks_names.json'))
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()

    cfg   = json.load(open(a.cfg))
    names = json.load(open(a.names))
    dirs  = {k: os.path.join(root, v) for k, v in cfg['dirs'].items()}

    done = import_marbleworks(a.zips, names, dirs['marbleworks'], dirs['ref'], a.force)
    print(f'marbleworks: {len(done)} STLs in {dirs["marbleworks"]}')
    write_name_table(names, os.path.join(dirs['ref'], 'names.md'))
    tubes = import_tubes(cfg['tubes'], root, dirs['tubes'], a.force)
    print(f'tubes      : {len(tubes)} STLs in {dirs["tubes"]}')


if __name__ == '__main__':
    main()
