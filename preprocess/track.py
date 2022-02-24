"""
@author Luo-Haohan
@date 2021/12/14
@filename track.py
@desc This program extract bounding boxes from video frames.

"""

import cv2
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm
import pandas as pd


def resize_bbox(cfg, crop):
    """View track of one vehicle.

    Args:
        tube : tube label of a certain vehicle
    """
    bbox = crop['bboxes']  # 2-d
    h1 = int(bbox[0][1]) if bbox[0][1] < cfg.height else cfg.height
    w1 = int(bbox[0][0]) if bbox[0][0] < cfg.width else cfg.width
    h2 = int(bbox[1][1]) if bbox[1][1] < cfg.height else cfg.height
    w2 = int(bbox[1][0]) if bbox[1][0] < cfg.width else cfg.width

    # padding: 144 x 144
    # if (h2 - h1) * (w2 - w1) > 32 * 32:
    edge = 128  # changeable
    h_mean = int((h1 + h2) / 2)
    w_mean = int((w1 + w2) / 2)
    h1, h2 = h_mean - edge // 2, h_mean + edge // 2
    w1, w2 = w_mean - edge // 2, w_mean + edge // 2
    if h2 > cfg.height:
        h1, h2 = cfg.height - edge, cfg.height
    if h1 < 0:
        h1, h2 = 0, edge
    if w2 > cfg.width:
        w1, w2 = cfg.width - edge, cfg.width
    if w1 < 0:
        w1, w2 = 0, edge

    # cropped_img = image[h1:h2, w1:w2]
    # cv2.imshow(frame_id, cropped_img)
    # cv2.waitKey(0)
    # cv2.imwrite(f'./{frame_id}.png', cropped_img)

    return (h1, w1), (h2, w2)


def save_track_dataset(cfg):
    """Generate a full dataset that contains fixed-length
    tracks of vehicles and its information.

    """
    gap = cfg.tube_length * cfg.fps // cfg.tube_size
    scene_dirs = list(Path(cfg.save_dir).glob('scene*'))
    scene_dirs.sort()

    for scene_dir in tqdm(scene_dirs):
        # print(f"Making {str(scene_dir)} tracks:")
        tracks = []
        with open(str(scene_dir / cfg.tube_name), 'r') as read:
            tubes = json.load(read)
        for tube in tubes:
            for i in range(0, len(tube), gap * cfg.tube_size):
                track = []
                # fixed-length tube
                for j in range(0, cfg.tube_size * gap, gap):
                    crop = dict()
                    if i + j < len(tube):
                        crop['vehicle_id'] = tube[i + j]['vehicle_id_dict']

                        crop['data'] = flatten_sensor(tube[i + j])
                        if cfg.os == 'linux':
                            crop['rgb_path'] = cfg.linux_save_dir + '/' + scene_dir.name + \
                                '/out_rgb/' + str(tube[i + j]['frame_ids']).zfill(6) + '.png'
                        else:
                            crop['rgb_path'] = str(scene_dir) + \
                                '\\out_rgb\\' + str(tube[i + j]['frame_ids']).zfill(6) + '.png'
                        crop['bbox'] = resize_bbox(cfg, tube[i + j])

                        crop['timestamp'] = tube[i + j]['timestamp']
                    else:
                        crop['vehicle_id'] = -1  # None, to be masked
                        crop['data'] = [0] * 12
                        crop['rgb_path'] = ''
                        crop['bbox'] = (-1, -1), (-1, -1)
                        crop['timestamp'] = -1.

                    # print(crop)
                    track.append(crop)

                tracks.append(track)

        # for each scene
        with open(str(scene_dir / cfg.track_name), 'w') as write:
            json.dump(tracks, write, indent=4)
        # print("Track file saved!!")


def flatten_sensor(crop):
    sensor = []
    for key in ["locations", "velocities", "angular_velocities", "accelaration"]:
        for sub_key in crop[key]:
            sensor.append(crop[key][sub_key])

    return sensor


def extract_all_tracks(cfg):
    """Extract tracks from tracks.json, save as a new dataset.

    """
    Path(cfg.track_dir).mkdir(parents=True, exist_ok=True)

    scene_dirs = list(Path(cfg.save_dir).glob('scene*'))
    scene_dirs.sort()

    for scene_dir in scene_dirs:
        scene_name = scene_dir.name
        track_scene_dir = cfg.track_dir + '\\' + scene_name
        Path(track_scene_dir).mkdir(parents=True, exist_ok=True)

        tracks_path = str(scene_dir / cfg.track_name)
        with open(tracks_path, 'r') as read:
            track_data = json.load(read)

        for i, track in enumerate(track_data):
            track_dir = track_scene_dir + '\\track-' + str(i + 1).zfill(3)
            bbox_dir = track_dir + '\\bbox'

            Path(track_dir).mkdir(parents=True, exist_ok=True)
            Path(bbox_dir).mkdir(parents=True, exist_ok=True)

            summary = []
            for crop in track:
                log = dict()
                log['data'] = crop['data']
                log['time'] = crop['timestamp']
                log['id'] = str(crop['vehicle_id']) + '-' + Path(crop['rgb_path']).stem
                if crop['rgb_path'] != '':
                    print(crop['rgb_path'])
                    img = cv2.imread(crop['rgb_path'])
                    (h1, w1), (h2, w2) = crop['bbox']
                    img = img[h1:h2, w1:w2, :]
                    bbox_name = bbox_dir + '\\' + log['id'] + '.png'
                    cv2.imwrite(bbox_name, img)
                    summary.append(log)

            with open(track_dir + '\\' + cfg.track_info, 'w') as write:
                json.dump(summary, write, indent=4)


def merge_track_to_csv(cfg):
    all_scene_dir = list(Path(cfg.save_dir).glob('scene-*'))
    all_tracks_paths = [str(_dir / cfg.track_name) for _dir in all_scene_dir]
    # print(all_tracks_paths[0])

    track_id = 0
    full_data = []
    attrbs = ['x', 'y', 'z', 'vx', 'vy', 'vz', 'rx', 'ry', 'rz', 'ax', 'ay', 'az']

    for tracks_path in all_tracks_paths:
        with open(tracks_path, 'r') as read:
            tracks = json.load(read)

        for track_data in tracks:
            track_id += 1

            for point in track_data:
                # point['data'] = [item * 100 if i >= 3 else item for i, item in enumerate(point['data'])]
                rec = dict(zip(attrbs, point['data']))
                rec['h1'] = point['bbox'][0][0]
                rec['w1'] = point['bbox'][0][1]
                rec['h2'] = point['bbox'][1][0]
                rec['w2'] = point['bbox'][1][1]

                rec['timestamp'] = point['timestamp']
                rec['rgb_path'] = point['rgb_path']
                rec['track_id'] = track_id

                full_data.append(rec)

    df = pd.DataFrame(full_data)
    # print(df.describe())
    # print(df.head(100))
    csv_path = cfg.save_dir + '\\' + cfg.all_track_csv
    df.to_csv(csv_path, header=None)
