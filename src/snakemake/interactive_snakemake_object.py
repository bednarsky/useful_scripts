import logging
# don't set basicConfig in utils scripts!
logger = logging.getLogger(__name__)

import os
import sys
from pathlib import Path
PROJECT_ROOT = Path(os.popen("git rev-parse --show-toplevel").read().strip())
sys.path.append(str(PROJECT_ROOT / 'workflow'))

import numpy as np
import pandas as pd
import json

def pretty_print_nested_dict(d, indent=0):
    for key, value in d.items():
        if isinstance(value, dict):
            logger.info(' ' * indent + str(key) + ':')
            pretty_print_nested_dict(value, indent + 2)
        else:
            value_str = str(type(value).__name__)
            if isinstance(value, np.ndarray):
                value_str += ' of shape ' + str(value.shape)
            elif isinstance(value, pd.DataFrame):
                value_str += ' of shape ' + str(value.shape)
            elif isinstance(value, str):
                value_str += ' ' + value
            elif isinstance(value, (int, float, np.integer, np.floating)):
                value_str += ' ' + str(value)
            logger.info(' ' * indent + str(key) + ': ' + value_str)

def replace_posixpaths_with_strings(obj):
    if isinstance(obj, dict):
        # If the object is a dictionary, recursively process each key-value pair
        return {key: replace_posixpaths_with_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        # If the object is a list, recursively process each element
        return [replace_posixpaths_with_strings(element) for element in obj]
    elif isinstance(obj, tuple):
        # If the object is a tuple, recursively process each element and return as a tuple
        return tuple(replace_posixpaths_with_strings(element) for element in obj)
    elif isinstance(obj, Path):
        # If the object is a Path, convert it to a string
        return str(obj)
    else:
        # If the object is neither a dict, list, tuple, nor Path, return it as is
        return obj

def snakemake_object_to_dict(smk):
    res_dict = {}
    for attr in dir(smk):
        try:
            if attr in ['log_fmt_shell']:
                continue
            attr_value = getattr(smk, attr)
            
            # Skip private attributes
            if attr.startswith('_'):
                continue
            
            # Try to convert to dict if possible
            try:
                res_dict[attr] = dict(attr_value)
            except (TypeError, ValueError):
                res_dict[attr] = attr_value
        
        except Exception as e:
            logger.warning(f'Could not save {attr} from snakemake object in dict: {e}')
        
        # drop keys that are methods manually (cannot be dumped to JSON)
        for key in ['report_href']:
            if key in res_dict:
                del res_dict[key]
    
    res_dict = replace_posixpaths_with_strings(res_dict)
    return res_dict

def snakemake_object_to_json(smk, json_path=None, print_dict=False):
    smk_dict = snakemake_object_to_dict(smk)

    if print_dict:
        logger.info('Snakemake object (parsed into dict):')
        pretty_print_nested_dict(smk_dict)

    if json_path is None:
        wcs = list(smk.wildcards)
        file_dir = PROJECT_ROOT / 'results/smk_objects' / smk.rule
        file_dir.mkdir(parents=True, exist_ok=True)
        if len(wcs) == 0:
            json_path = file_dir / f'{smk.rule}.json'
        else:
            json_path = file_dir / f'{"__".join(wcs)}.json'
    try: 
        with open(json_path, 'w') as f:
            json.dump(smk_dict, f)
            logger.info(f'Saved snakemake object to {json_path}')
    except Exception as e:
        logger.warning(f'Could not save snakemake object to {json_path}: {e}')

class SnakelikeObject:
    """ class to allow indexing of object like this: smk.input['adata_superset'] """
    def __init__(self, smk_dict):
        for k, v in smk_dict.items():
            setattr(self, k, v)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        return str(self.__dict__)
    
    def __str__(self):
        return str(self.__dict__)
    
    def keys(self):
        return self.__dict__.keys()
    
def read_json_into_smk_obj(json_path):
    with open(json_path, 'r') as f:
        smk_dict = json.load(f)
    smk_obj = SnakelikeObject(smk_dict)
    return smk_obj