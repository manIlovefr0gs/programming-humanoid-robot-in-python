import cv2
import numpy as np
import time

hsv_color_range = {"green": ([50, 50, 50], [100, 255, 255]),
                   "blue": ([100, 150, 0], [140, 255, 255]),
                   "red": ([0, 150, 50], [10, 255, 255]),
                   "yellow": ([20, 100, 100], [30, 255, 255])
                   }

def detect_color_from_file(imagepath, color):
    bgr= cv2.imread(imagepath)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    plt.imshow(rgb)

    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    field = (g > 50) & (r < 50) & (b < 100)
    plt.imshow(field, cmap='gray')

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, color[0], color[1])
    res = cv2.bitwise_and(bgr, bgr, mask=mask)
    plt.imshow(res)

def main():
    FILEPATH = "nao_test/images/green.png"
    detect_color_from_file(FILEPATH, hsv_color_range["green"])