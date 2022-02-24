import pandas as pd
import numpy as np
from pathlib import Path
from typing import List
import pickle as pkl

from pandas.core.reshape.merge import merge


class SensorStucture(object):
    file_dict = {'imu': 'IMUMeasurement.csv', 'radar': 'RadarMeasurement.csv', 'collision': 'CollisionEvent.csv'}
    common_attrbs = ['vehicle_id', 'frame', 'x', 'y', 'z']  # both in imu and radar sensor
    imu_msrs = [
        'accelerometer_Vector3D_x', 'accelerometer_Vector3D_y', 'accelerometer_Vector3D_z', 'compass', 'gyroscope_Vector3D_x',
        'gyroscope_Vector3D_y', 'gyroscope_Vector3D_z'
    ]
    radar_msrs = ['get_detection_count']
    collision_msrs = [
        'normal_impulse_Vector3D_x', 'normal_impulse_Vector3D_y', 'normal_impulse_Vector3D_z', 'other_actor_Vehicle_id'
    ]
    sensor_msrs = {'imu': imu_msrs, 'radar': radar_msrs, 'collision': collision_msrs}

    def __init__(self, workspace: str) -> None:
        for key in self.file_dict:
            self.file_dict[key] = workspace + '\\' + self.file_dict[key]
            assert Path(self.file_dict[key]).is_file(), 'workspace path error, {} not found'.format(self.file_dict[key])

    def merge_sensor_data(self) -> pd.DataFrame:
        """merge all sensor data into one csv

        Returns:
            pd.DataFrame
        """
        df_dict = {}
        for sensor in self.file_dict:
            csv_data = pd.read_csv(self.file_dict[sensor])
            df_dict[sensor] = pd.DataFrame(csv_data, columns=self.common_attrbs + self.sensor_msrs[sensor])

        merge_df = pd.merge(df_dict['imu'], df_dict['radar'], on=self.common_attrbs, how='inner')
        merge_df = pd.merge(merge_df, df_dict['collision'], on=self.common_attrbs, how='left')

        merge_df.fillna(0, inplace=True)

        label = merge_df['other_actor_Vehicle_id'].apply(lambda x: 1 if x != 0 else 0)
        merge_df['anomaly'] = label

        # Collision data only used for labelling. Drop collision measurements after creating labels.
        merge_df.drop(columns=self.collision_msrs, inplace=True)

        return merge_df


def main(workspace):
    ss = SensorStucture(workspace)
    data = ss.merge_sensor_data()
    data.to_csv(workspace + '\\MergeData.csv')  # Total value

    # save as pickle file
    data_y = data['anomaly'].values
    data_x = data.drop(columns=['anomaly']).values
    with open(workspace + '\\train_x.pkl', 'wb') as wf:
        print(data_x.shape)
        pkl.dump(data_x, wf)
    with open(workspace + '\\train_y.pkl', 'wb') as wf:
        print(data_y.shape)
        pkl.dump(data_y, wf)
