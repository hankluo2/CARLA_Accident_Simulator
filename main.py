"""
Environment: Ubuntu/Windows
"""
import hydra
import img2vid

from datamaker import *


@hydra.main(config_path='./configure', config_name='carla')
def main(cfg):
    # make data
    if cfg.scene_num != 0:
        print("Begin to make raw data ...\n")
        make_data(cfg)
    else:
        print("Data maker unset. Check config file.")

    if cfg.save_mp4:
        if not Path(cfg.video_output_dir).exists():
            Path(cfg.video_output_dir).mkdir(parents=True, exist_ok=True)

        img2vid.dfs_copier(cfg.frame_input_dir, cfg.video_output_dir, cfg)


if __name__ == '__main__':
    main()
    print("Program finished successfully!\n")
