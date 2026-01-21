# -*- coding: utf-8 -*-
import time
from naoqi import ALProxy
from change_posture import *
from nao_config import *



def walk_straight(motion_proxy, posture_proxy):
    print("Waking up")
    change_posture(posture_proxy, "StandInit")
    velocity = 0.5
    direction = 0
    theta = 0.5 # rotation

    motion_proxy.moveToward(velocity, direction, theta)

    time.sleep(6) # walking for n seconds

    motion_proxy.stopMove() 
    motion_proxy.rest()

def move_to_coordinates(motion_proxy, distance_x, distance_y, theta, posture_proxy):
    motion_proxy.wakeUp()
    change_posture(posture_proxy, "StandInit")

    motion_proxy.moveTo(distance_x, distance_y, theta)

    motion_proxy.stopMove()
    motion_proxy.rest()


def main():
    nao = InitNao()
    motion_proxy = nao.get_proxy("ALMotion")
    posture_proxy = nao.get_proxy("ALRobotPosture")
    #walk_straight(motion_proxy, posture_proxy)
    move_to_coordinates(motion_proxy, 0.5, 0.5, 0.0, posture_proxy) 

if __name__ == "__main__":
    main()