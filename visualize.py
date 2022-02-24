import pandas as pd
from pathlib import Path
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import hydra

from cv_video_tools import *


def box_plot(cfg):
    # load data
    data_path = cfg.save_dir + '\\' + cfg.all_track_csv
    data = pd.read_csv(data_path)
    # data = data.drop(columns=0)
    data = data.drop(['rgb_path', 'z', 'vz', 'rz', 'az'], axis=1)

    max_tr_id = int(data.iloc[-1]['track_id'])
    print(int(max_tr_id))
    for i in range(1, max_tr_id, 1):
        track_data = data[data['track_id'].isin([float(i)])]
        track_data = track_data.drop(['track_id'], axis=1)
        track_corr = track_data.corr()
        plt.subplots(figsize=(20, 16))
        sns.heatmap(track_corr, vmax=.8, square=True, annot=True)
        # plt.savefig(f'corr-{i}.png')
        # plt.show()
        # plt.close()
        # print(track_data)
        # break
        # track_data.boxplot()
        # plt.show()
        # plt.savefig(f'boxplot-{i}.png')
        # plt.close()

    # columns = data.columns.tolist()[:]
    # fig = plt.figure(figsize=(4, 6))
    # sns.boxplot(data['x'], orient='v', width=0.5)
    # plt.show()
    # data.boxplot()
    # plt.show()


# @hydra.main(config_path='./configure', config_name='video_settings')
# def convert2video()


if __name__ == '__main__':
    _input = 'D:\\datasets\\Carla\\test\\scene-48\\out_rgb'
    _out = 'D:\\datasets\\Carla\\test\\scene-48\\out.mp4'
    fps = 25
    makeVideo(_input, _out, fps)
