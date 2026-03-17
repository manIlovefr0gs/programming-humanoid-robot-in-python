import sys
from naoqi import ALProxy
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from nao_config import *


def change_eye_color(ip, port, color):


    leds = ALProxy("ALLeds", ip, port)
    r, g, b = [c / 255.0 for c in color]
    leds.fadeRGB("FaceLeds", r, g, b, 0.0)

if __name__ == "__main__":
    nao = InitNao()

    color = (
        int(input("R (0-255): ")),
        int(input("G (0-255): ")),
        int(input("B (0-255): "))
    )

    change_eye_color(nao.ip, nao.port, color)
