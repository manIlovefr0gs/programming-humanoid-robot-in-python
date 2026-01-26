# -*- coding: utf-8 -*-

from naoqi import ALProxy
import numpy as np

IP = "192.168.1.118"
PORT = 9559

video = ALProxy("ALVideoDevice", IP, PORT)

name = video.subscribeCamera(
    "capture",
    0,      # Top camera
    1,      # QVGA 320x240
    13,     # BGR
    10
)

img = video.getImageRemote(name)

width = img[0]
height = img[1]
data = img[6]

image = np.frombuffer(data, dtype=np.uint8)
image = image.reshape((height, width, 3))

# Bild speichern
from PIL import Image
Image.fromarray(image).save("nao_image.png")

video.unsubscribe(name)

print("Bild gespeichert als nao_image.png")
