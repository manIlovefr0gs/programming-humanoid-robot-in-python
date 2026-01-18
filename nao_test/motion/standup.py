-*- coding: utf-8 -*-
import sys
import time
from naoqi import ALProxy, ALBroker, ALModule
from change_posture import *


FallResponder = None
global memory = None   # is this legal in py? -> maybe einfach global memory in der Klasse 

class FallResponderModule(ALModule):
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.name = name

        self.motion = ALProxy("ALMotion")
        self.posture = ALProxy("ALRobotPosture")


        memory = ALProxy("ALMemory")
        memory.subscribeToEvent("robotHasFallen", self.getName(), "onFallen")


    def on_fallen(self, key, value, message):
        print("\nAua, ich bin hingefallen")
        print("Fall Event Details:", value)
        
        posture_family = self.posture.getPostureFamily()
        print("Posture Family:", posture_family)

        if "Lying" in posture_family:
            self.get_up(self.posture)
             
    def get_up(posture_proxy):
        print("Trying to get back up")
        change_posture(posture_proxy, "Stand")


def main():
    global FallResponder
    global memory

    IP = "192.168.1.118"
    PORT = 9559 

    broker = ALBroker("FallBroker", "0.0.0.0", 0, IP, PORT)

    FallResponder = FallResponderModule("FallResponder")

    try:
        print("Fall detection running")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutdown falldetection")
    finally:
        # Cleanup
        if memory:
            memory.unsubscribeToEvent("robotHasFallen", "FallResponder")
        broker.shutdown()
        print("Byebye")

if __name__ == "__main__":
    main()