## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Project paths, read from config/project.json.
'''
import json
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_cfg(path=None):
    '''
    Load the project config.

    Args:
        path (str): config file, default config/project.json

    Returns:
        dict: the parsed config
    '''
    with open(path or os.path.join(root, 'config', 'project.json')) as f:
        return json.load(f)


def out_dirs(cfg=None):
    '''
    Absolute output folders from the config, created if missing.

    Returns:
        dict: folder key -> absolute path
    '''
    cfg  = cfg or load_cfg()
    dirs = {k: os.path.join(root, v) for k, v in cfg['dirs'].items()}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs
