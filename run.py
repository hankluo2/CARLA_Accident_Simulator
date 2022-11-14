import os
import time

if __name__ == "__main__":
    # generate 5 scenes
    for i in range(1, 6):  # x5
        for weather_name in ['clear', 'rain', 'morning_fog', 'evening', 'evening_rain', 'cloudy']:  # x6
            for number_vehicles in range(20, 100, 20):  # x4
                cmd = f"python main.py scene_num={str(i).zfill(2)} weather={weather_name} number_of_vehicles={number_vehicles}"
                print(cmd)
                os.system(cmd)
                time.sleep(20)  # wait for 20 seconds...
