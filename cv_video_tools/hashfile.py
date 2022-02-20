from pathlib import Path
from math import log10, ceil, floor
import json
from shutil import copy


def make_single_level_category_hash(root, pattern='.mp4', dest='./'):
    rootdirs = list(Path(root).glob('*'))  # Note that the inner part is a generator
    boolcnt = [item.is_dir() for item in rootdirs].count(True)
    assert boolcnt > 0, "No existing directory in " + root
    cls_dgt_cnt = floor(log10(boolcnt)) + 1

    max_ = -1
    for item in rootdirs:
        if item.is_dir():
            max_ = max(max_, len(list(item.glob('*' + pattern))))
    assert max_ > 0, "No any target files found in " + root
    file_dgt_cnt = floor(log10(max_)) + 1

    hash_table = {}

    prf_cnt = 0
    for dir in rootdirs:
        preffix = str(prf_cnt).zfill(cls_dgt_cnt)
        sfx_cnt = 0
        for file in dir.glob("*" + pattern):
            suffix = str(sfx_cnt).zfill(file_dgt_cnt)
            filename = preffix + suffix + pattern
            hash_table[str(file)] = dest + '/' + filename
            sfx_cnt += 1
        prf_cnt += 1

    return hash_table
