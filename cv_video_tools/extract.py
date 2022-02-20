import cv2 as cv
import numpy as np
from pathlib import Path
import os
import tqdm


# extract and save frames from a single video
def extract_frames_from_video(src_video_path, dest_dir, interval):
    """ judge whether destination exists
    Args:
        interval: extract and save one frame per `interval` frames.
        interval aka frame rate: in this condition extract one frame per 1 second.
    """
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    vc = cv.VideoCapture(src_video_path)  # set video capture
    cnt = 1
    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval = False

    # timeF = interval, aka frame rate (FR)
    icnt = 1
    while rval:
        if cnt % interval == 0:
            cv.imwrite(dest_dir + '/' + '%06d' % icnt + '.jpg', frame)
            icnt += 1
        cnt += 1
        rval, frame = vc.read()
    vc.release()  # release video capture


# Averaging frames based on extracted frames from a video. Interval set default by num of extracted frames.
def frame_average(frames_dir, dest_dir, alpha=0.1, thresh=5):
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    p = Path(frames_dir)
    # print(p)
    imgs = p.glob('*.jpg')  # type of posix
    imgs = list(imgs)
    imgs.sort()
    # print(imgs)

    former_img = cv.imread(str(imgs[0]))
    img = former_img  # init

    for i in range(len(imgs)):
        now_img = cv.imread(str(imgs[i]))
        if np.mean(np.abs(now_img - former_img)) > thresh:
            img = img * (1 - alpha) + now_img * alpha
        cv.imwrite(dest_dir + '/' + imgs[i].name, img)
        former_img = now_img


def patch_frames(src_dir, dest_dir):
    """
    Segment a single frame into 3 parts, in region W: [0. ,.5], [.25, .75], [.5, 1.]
    """
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    # folders = os.listdir(src_dir).sort()
    p = Path(src_dir)
    imgs = list(p.glob('*.jpg'))

    for f in imgs:
        D = cv.imread(str(f))
        _, W, _ = D.shape
        cv.imwrite(dest_dir + "/" + f.stem + "_1" + ".jpg", D[:, 0:W // 2, :])
        cv.imwrite(dest_dir + "/" + f.stem + "_2" + ".jpg", D[:, W // 4:W // 2 + W // 4, :])
        cv.imwrite(dest_dir + "/" + f.stem + "_3" + ".jpg", D[:, W // 2:, :])
