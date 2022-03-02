"""
Environment: Ubuntu/Windows
"""
import hydra
import os
import time
from vidtools import file_structured_videos_generator as fsvg

from datamaker import *


@hydra.main(config_path='./configure', config_name='carla')
def main(cfg):
    # make data
    if cfg.scene_num != 0:
        try:
            print("Starting simulator... waiting...")
            os.system(f"docker start {cfg.dockerid}")
            time.sleep(15)
            print("Simulator started successfully!")
        except:
            return

        print("Begin to make raw data ...\n")
        make_data(cfg)

        os.system(f"docker stop {cfg.dockerid}")
        print(f"Carla simulator docker#{cfg.dockerid} terminated.")
        time.sleep(10)

    else:
        print("Data maker unset. Check config file.")

    if cfg.save_mp4:
        if not Path(cfg.video_output_dir).exists():
            Path(cfg.video_output_dir).mkdir(parents=True, exist_ok=True)

        fsvg(cfg.frame_input_dir, cfg.video_output_dir, cfg.fps,
             cfg.frame_shift, cfg.video_format, cfg.img_format)


if __name__ == '__main__':
    main()
    print("Program finished successfully!\n")
