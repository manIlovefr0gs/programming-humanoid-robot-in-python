# -*- coding: utf-8 -*-

import sys
import time
import os
from naoqi import ALProxy, ALBroker, ALModule

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from nao_config import *
from change_posture import *

FallResponder = None
memory = None

class FallResponderModule(ALModule):
    def __init__(self, name, ip, port):
        ALModule.__init__(self, name)
        self.name = name
        
        self.motion = ALProxy("ALMotion", ip, port)
        self.posture = ALProxy("ALRobotPosture", ip, port)
        global memory
        memory = ALProxy("ALMemory", ip, port)
        
        # Korrekter Event-Name und Callback
        memory.subscribeToEvent("robotHasFallen", self.name, "onFallen")
        print("Subscribed to robotHasFallen event")

    def onFallen(self, key, value, message):
        """Callback wird aufgerufen wenn Roboter gefallen ist"""
        print("\n=== FALL DETECTED ===")
        print("Event:", key)
        print("Value:", value)
        
        time.sleep(1)  # Kurz warten bis Roboter zur Ruhe kommt
        
        posture_family = self.posture.getPostureFamily()
        print("Current posture:", posture_family)
        
        if posture_family in ["LyingBack", "LyingBelly"]:
            print("Robot is lying down - getting up...")
            self.get_up()
        else:
            print("Robot is not lying - no action needed")
    
    def get_up(self):
        """Steht auf"""
        try:
            print("Attempting to stand up...")
            change_posture(self.posture, "Stand")
            print("Successfully stood up!")
        except Exception as e:
            print("Error getting up:", e)


def main():
    global FallResponder, memory
    
    nao = InitNao()
    
    broker = ALBroker(
        "FallBroker",
        "0.0.0.0",
        0,
        nao.IP,
        nao.PORT
    )
    
    FallResponder = FallResponderModule("FallResponder", nao.IP, nao.PORT)
    
    try:
        print("Fall detection active - waiting for falls...")
        print("Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping fall detection...")
    finally:
        if memory:
            memory.unsubscribeToEvent("robotHasFallen", "FallResponder")
        broker.shutdown()
        print("Shutdown complete")


def test_fall_event():
    """Testet die Fall-Erkennung durch manuelles Auslösen des Events"""
    nao = InitNao()
    
    broker = ALBroker(
        "TestFallBroker",
        "0.0.0.0",
        0,
        nao.IP,
        nao.PORT
    )
    
    global FallResponder, memory
    FallResponder = FallResponderModule("FallResponder", nao.IP, nao.PORT)
    
    print("\n=== FALL EVENT TEST ===")
    print("Triggering robotHasFallen event in 3 seconds...")
    
    try:
        time.sleep(3)
        
        # Event manuell auslösen
        memory.raiseEvent("robotHasFallen", True)
        print("Event triggered!")
        
        # Warten damit Callback ausgeführt werden kann
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\nTest abgebrochen")
    finally:
        if memory:
            memory.unsubscribeToEvent("robotHasFallen", "FallResponder")
        broker.shutdown()
        print("Test beendet")


if __name__ == "__main__":

    #test_fall_event()
    main()