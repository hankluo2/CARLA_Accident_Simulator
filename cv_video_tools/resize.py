import cv2
from pathlib import Path


def img_resize(image, new_width):
    height, width, _ = image.shape

    new_height = int(new_width / width * height)
    img_new = cv2.resize(image, (new_width, new_height))
    return img_new


if __name__ == '__main__':
    org_frames = './frames'
    resized_frames_path = './rsz_frames'
    Path(resized_frames_path).mkdir(parents=True, exist_ok=True)

    images = list(Path(org_frames).glob('*.jpg'))
    # print(images)
    images = [str(pos) for pos in images]
    # print(images)

    for image in images:
        img = cv2.imread(image)
        img_new = img_resize(img, 640)
        # cv2.imshow(image, img_new)
        cv2.imwrite(resized_frames_path + '/' + Path(image).name, img_new)
