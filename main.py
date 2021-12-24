"""
Environment: Windows
"""
import hydra
from pathlib import Path
import json

from datamaker import *
from preprocess import *


@hydra.main(config_path='./configure', config_name='carla')
def main(cfg):
    # make data
    if cfg.scene_num != 0:
        print("Begin to make raw data ...\n")
        make_data(cfg)
    else:
        print("Data maker unset. Check config file.")

    # organize data
    if cfg.save_tube:
        get_all_merged_tubes_from_scenes(cfg)

    if cfg.save_track:
        save_track_dataset(cfg)

    if cfg.save_track_dataset:
        extract_all_tracks(cfg)


if __name__ == '__main__':
    main()
