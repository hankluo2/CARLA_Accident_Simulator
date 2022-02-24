import time

import generate_traffic as gt
from pca import pca_det
import preprocess_sensor_data
from makevideo import makeVideo


def main():
    # launch carla simulation
    since = time.time()
    try:
        gt.launch()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')
    print("Simulation cost {:.4f} seconds.".format(time.time() - since))

    print(gt.output_dir)
    # outlier detection
    preprocess_sensor_data.main(gt.output_dir)
    pca_det(gt.output_dir + '\\train_x.pkl', gt.output_dir + '\\train_y.pkl')

    # save as mp4
    makeVideo(gt.output_dir, gt.output_dir + '\\demo.mp4', 100)
    print("Video made!")


if __name__ == "__main__":
    main()
