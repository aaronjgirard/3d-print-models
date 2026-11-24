## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Build the ʻOumuamua OrcaSlicer project: one object per plate (rock, plaque,
stand), per-object settings (tree supports on the rock only), a pause at a
given height on a plate (filament swap for the plaque text), and project
settings from a cli_slice style laid over a saved Orca project config.

The 3MF layout follows secret_drawers/build_project.py.

Usage:
    python -I build_project.py [--cfg project.json]
'''
import argparse, json, os, zipfile
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh

skip = ('name', 'from', 'inherits', 'type', 'version', 'setting_id', 'instantiation')

def project_settings(cfg, here):
    '''
    Saved Orca project config with the style presets laid over it.

    Args:
        cfg  (dict): project config
        here (str):  folder of the project config

    Returns:
        dict: project_settings.config contents
    '''
    prj = json.load(open(os.path.join(here, cfg['base'])))
    ids = {}
    for f, key in (('printer', 'printer_settings_id'), ('process', 'print_settings_id'),
                   ('filament', 'filament_settings_id')):
        pre = json.load(open(os.path.join(here, cfg['style'], f + '.json')))
        prj.update({k: v for k, v in pre.items() if k not in skip})
        ids[key] = pre['name']
    prj.update(ids)
    prj['filament_settings_id'] = [ids['filament_settings_id']]
    return prj

def plate_origin(idx, nplate, bed, gap=0.2):
    '''orca plate origin for 0-based plate idx (column count rule from PartPlateList).'''
    val  = np.sqrt(nplate)
    cols = int(round(val)) + (1 if val > round(val) else 0)
    step = bed * (1.0 + gap)
    return (idx % cols) * step, -(idx // cols) * step

def pause_xml(plates):
    '''custom_gcode_per_layer.xml with a PausePrint (type 1) entry per plate that asks for one.'''
    out = '<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n'
    for i, p in enumerate(plates, start=1):
        if 'pause' not in p:
            continue
        out += ('<plate>\n<plate_info id="%d"/>\n<layer top_z="%g" type="1" extruder="1" color="" extra=%s gcode="PAUSE"/>\n'
                '<mode value="SingleExtruder"/>\n</plate>\n' % (i, p['pause']['top_z'], quoteattr(p['pause']['msg'])))
    return out + '</custom_gcodes_per_layer>\n'

def write_3mf(path, objs, plates, bed, proj):
    '''objs: list of (name, plate, mesh, settings). each object is centered on its plate.'''
    ns   = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" %s>' % ns
    files, res, items, cfg, rels, pl = {}, [], [], [], [], {}
    for i, (name, plate, mesh, sets) in enumerate(objs, start=1):
        mid, wid = 2 * i - 1, 2 * i
        ox, oy   = plate_origin(plate - 1, len(plates), bed)
        ext      = mesh.extents
        verts    = mesh.vertices - mesh.bounds[0] - ext / 2.0
        vts      = ''.join('<vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(v) for v in verts)
        tri      = ''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in mesh.faces)
        fpath    = '/3D/Objects/%s.stl_%d.model' % (name, wid)
        files[fpath[1:]] = (head + '<metadata name="BambuStudio:3mfVersion">1</metadata><resources>'
                            '<object id="%d" p:UUID="%08x-81cb-4c03-9d28-80fed5dfa1dc" type="model"><mesh><vertices>%s</vertices>'
                            '<triangles>%s</triangles></mesh></object></resources><build/></model>' % (mid, mid, vts, tri))
        rels.append('<Relationship Target="%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
                    % (fpath, i + 1))
        res.append('<object id="%d" p:UUID="%08x-61cb-4c03-9d28-80fed5dfa1dc" type="model"><components>'
                   '<component p:path="%s" objectid="%d" p:UUID="%08x-b206-40ff-9872-83e8017abed1" '
                   'transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>' % (wid, wid, fpath, mid, mid))
        items.append('<item objectid="%d" p:UUID="%08x-b1ec-4553-aec9-835e5b724bb4" '
                     'transform="1 0 0 0 1 0 0 0 1 %.6f %.6f %.6f" printable="1"/>'
                     % (wid, wid, ox + bed / 2, oy + bed / 2, ext[2] / 2.0))
        obj_sets = ''.join('<metadata key=%s value=%s/>' % (quoteattr(k), quoteattr(v)) for k, v in sets.items())
        cfg.append('<object id="%d" auto_drop="1"><metadata key="name" value=%s/><metadata key="extruder" value="1"/>%s'
                   '<part id="%d" subtype="normal_part"><metadata key="name" value=%s/>'
                   '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
                   '<metadata key="source_file" value=%s/><metadata key="source_object_id" value="0"/>'
                   '<metadata key="source_volume_id" value="0"/><metadata key="source_offset_x" value="%.6f"/>'
                   '<metadata key="source_offset_y" value="%.6f"/><metadata key="source_offset_z" value="%.6f"/>'
                   '</part></object>'
                   % (wid, quoteattr(name), obj_sets, mid, quoteattr(name), quoteattr(name + '.stl'),
                      ext[0] / 2.0, ext[1] / 2.0, ext[2] / 2.0))
        pl.setdefault(plate, []).append(wid)
    pcfg = ''
    for p in sorted(pl):
        inst = ''.join('<model_instance><metadata key="object_id" value="%d"/><metadata key="instance_id" value="0"/>'
                       '<metadata key="identify_id" value="%d"/></model_instance>' % (w, 100 + w) for w in pl[p])
        pcfg += ('<plate><metadata key="plater_id" value="%d"/><metadata key="plater_name" value=%s/>'
                 '<metadata key="locked" value="false"/><metadata key="filament_map_mode" value="Auto For Flush"/>'
                 '<metadata key="filament_maps" value="1"/><metadata key="filament_volume_maps" value="0"/>%s</plate>'
                 % (p, quoteattr(plates[p - 1]['name']), inst))
    model = (head + '<metadata name="Application">BambuStudio-02.08.01.55</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata><metadata name="OrcaSlicer">2.5.0</metadata>'
             '<metadata name="License">Apache-2.0</metadata>'
             '<resources>%s</resources><build>%s</build></model>' % (''.join(res), ''.join(items)))
    mset  = '<?xml version="1.0" encoding="UTF-8"?>\n<config>%s%s</config>' % (''.join(cfg), pcfg)
    ctype = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '<Default Extension="config" ContentType="text/xml"/></Types>')
    rel0  = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
             '</Relationships>')
    rel1  = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '%s</Relationships>' % ''.join(rels))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ctype)
        z.writestr('_rels/.rels', rel0)
        z.writestr('3D/3dmodel.model', model)
        z.writestr('3D/_rels/3dmodel.model.rels', rel1)
        for fn, txt in files.items():
            z.writestr(fn, txt)
        z.writestr('Metadata/model_settings.config', mset)
        z.writestr('Metadata/project_settings.config', json.dumps(proj, indent=4))
        z.writestr('Metadata/custom_gcode_per_layer.xml', pause_xml(plates))

def main(path):
    here = os.path.dirname(os.path.abspath(path))
    cfg  = json.load(open(path))
    objs = []
    for i, p in enumerate(cfg['plates'], start=1):
        msh = trimesh.load(os.path.join(here, p['stl']))
        if p.get('rotz', 0.0):
            msh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(p['rotz']), [0, 0, 1]))
        name = os.path.splitext(p['stl'])[0]
        objs.append((name, i, msh, p.get('settings', {})))
        print('plate %d %-28s %s mm' % (i, p['name'], np.round(msh.extents, 1).tolist()))
    out = os.path.join(here, cfg['out'])
    write_3mf(out, objs, cfg['plates'], cfg['bed'], project_settings(cfg, here))
    print('wrote', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default='project.json')
    main(ap.parse_args().cfg)
