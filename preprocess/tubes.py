"""
@author Luo-Haohan
@date 2021/12/14
@filename tubes.py
@desc This program extracts raw data from carla simulator.

"""

from pathlib import Path
from queue import Queue as Q
import json
import numpy as np


def get_tubes_from_scene(scene_path: str):
    """Get multi tubes of vehicles from a video.

    Args:
        scene_path (str): Raw data saving dir path.
    """
    bbox_dir = Path(scene_path) / 'out_bbox'
    # img_dir = Path(scene_path) / 'out_rgb'

    bbox_filelist = list(bbox_dir.glob('*.json'))
    frame_list = [str(file).split('\\')[-1].split('.')[0] for file in bbox_filelist]
    frame_list.sort()
    # print(frame_list)
    frame_list = frame_list[50:]  # Eliminate first 58 frames

    monitor = dict()
    update = dict()
    tubes = []

    for frame in frame_list:
        # frame: current frame number (str)
        with open(str(bbox_dir / (frame + '.json')), 'r') as readf:
            frame_data = json.load(readf)

        vehicle_id = frame_data['vehicle_ids']
        for v in vehicle_id:
            vid = str(v)
            vehicle_info = get_vehicle_info(frame_data, vid)  # extract vehicle information

            if vid not in monitor:  # vehicle not captured before
                monitor[vid] = Q()  # build a queue for new vehicle
                update[vid] = "-1"  # new vehicle update status, set default -1

            # vid in monitor: 2 cases: show-uped vehicle appeared again / wait to update
            if int(update[vid]) == int(frame) - 1:  # case 2: await to update
                monitor[vid].put(vehicle_info)  # enqueue
                update[vid] = frame  # update current frame
            else:  # case 1: fake-old vehicle
                if update[vid] != "-1":
                    tubes.append(get_tube(monitor[vid]))  # queue cleared
                monitor[vid].put(vehicle_info)  # then enqueue
                update[vid] = frame  # update current frame

    for vid in monitor:
        if not monitor[vid].empty():
            tubes.append(get_tube(monitor[vid]))

    return tubes


def get_tube(queue):
    """
    """
    tube = []
    while not queue.empty():
        tube.append(queue.get())
    return tube


def get_vehicle_info(frame_data, vid):
    """
    """
    v_record = dict()
    for key in frame_data:
        if key in ['vehicle_ids']:
            continue
        v_record[key] = frame_data[key][vid]
    return v_record


def merge_tubes(tubes):
    new_tube = []
    q = Q()
    q.put(tubes[0])
    for i in range(1, len(tubes)):
        if tubes[i - 1][0]['vehicle_id_dict'] == tubes[i][0]['vehicle_id_dict']:
            # merge these two tube
            q.put(tubes[i])
        else:
            # new_tube.append(tubes[i])
            temp = []
            while not q.empty():
                # temp = temp + q.get()
                crops = q.get()
                for crop in crops:
                    temp.append(crop)
                # print(temp)

            if len(temp) > 25:
                new_tube.append(temp)

            q.put(tubes[i])

    # process the last tube
    temp = []
    while not q.empty():
        crops = q.get()
        for crop in crops:
            temp.append(crop)

    if len(temp) > 25:
        new_tube.append(temp)

    return new_tube


def get_all_merged_tubes_from_scenes(cfg):
    scene_dirs = [str(_dir) for _dir in list(Path(cfg.save_dir).glob('scene*'))]
    scene_dirs.sort()
    # print(scene_dirs)

    for _dir in scene_dirs:
        tubes = get_tubes_from_scene(_dir)
        tubes = merge_tubes(tubes)
        # print(len(tubes))
        tube_lens = []
        for tube in tubes:
            print("track existing time:", len(tube) / cfg.fps, "sec")
            tube_lens.append(len(tube))

        tube_lens = np.array(tube_lens)
        print(np.median(tube_lens))

        # print(tube[0]['vehicle_id_dict'])
        # print(tubes)
        if cfg.save_tube:
            with open(_dir + '\\' + cfg.tube_name, 'w') as write:
                json.dump(tubes, write, indent=4)
