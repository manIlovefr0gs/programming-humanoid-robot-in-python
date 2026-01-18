# -*- coding: utf-8 -*-

from naoqi import ALProxy
from change_posture import *


IP = "192.168.1.118"
PORT = 9559


def walk_straight(motion_proxy, posture_proxy):
    motion.wakeUp()
    change_posture(posture_proxy, "StandInit")
    velocity = 0.5
    direction = 0.0
    theta = 0.0 # rotation

    motion.moveToward(velocity, direction, theta)

    time.sleep(3) # walking for n seconds

    motion.stopMove() 
    motion_proxy.rest()

def move_to_coordinates(motion_proxy, distance_x, distance_y, theta):
    motion.wakeUp()
    change_posture(posture_proxy, "StandInit")

    motion.moveTo(distance_x, distance_y, theta)

    motion.stopMove()
    motion_proxy.rest()


def main():
    motion_proxy = ALProxy("ALMotion", IP, PORT)
    posture_proxy = ALProxy("ALRobotPosture", IP, PORT)

    #walk_straight(motion_proxy, posture_proxy)
    move_to_coordinates(motion_proxy, 0.5, 0.0, 0.0) 

