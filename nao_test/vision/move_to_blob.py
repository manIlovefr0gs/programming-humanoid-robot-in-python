# -*- coding: utf-8 -*-

from naoqi import ALProxy, ALBroker, ALModule
import time
from blobdetection import *
from nao_config import *



ColorDetector = None


class BlobTracker(ALModule):
    
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.memory = ALProxy("ALMemory")
        self.detected = False
        
        self.memory.subscribeToEvent(
            "ALTracker/ColorBlobDetected",
            name,
            "on_blob_detected"
        )
    
    def on_blob_detected(self, event_name, value, subscriber_id):
        self.detected = True





def setup_blob_detection(blob_proxy, color_name):
    """Konfiguriert Blob Detection"""
    
    colors = {
        "red":   (255, 0, 0, 60),
        "green": (0, 255, 0, 60),
        "blue":  (0, 0, 255, 60)
    }
    
    r, g, b, threshold = colors[color_name]
    
    blob_proxy.setColor(r, g, b, threshold)
    blob_proxy.setObjectProperties(50, 0.05)
    blob_proxy.subscribe("BlobNav")
    
    return blob_proxy


def setup_tracker(tracker_proxy, target_distance):
    """Konfiguriert ALTracker für Navigation"""
        
    tracker_proxy.setMode("Move")
    tracker_proxy.setRelativePosition([
        -target_distance,  
        0.0,
        0.0,
        0.05,  
        0.05,  
        0.1    
    ])
    tracker_proxy.setMaximumDistanceDetection(3.0)
    tracker_proxy.toggleSearch(True)
    
    return tracker_proxy


def get_distance_to_target(tracker_proxy):
    """Berechnet aktuelle Distanz zum Blob"""
    
    target_pos = tracker_proxy.getTargetPosition(1)  # Robot frame
    
    # Handle case when no target is detected
    if not target_pos or len(target_pos) < 2:
        return None
    
    distance = (target_pos[0]**2 + target_pos[1]**2)**0.5
    return distance


def track_blob(tracker_proxy, duration, target_distance):
    """Führt Tracking-Loop aus"""
    
    tracker_proxy.trackEvent("ALTracker/ColorBlobDetected")
    
    start = time.time()
    reached = False
    
    while (time.time() - start) < duration:
        
        if tracker_proxy.isActive():
            distance = get_distance_to_target(tracker_proxy)
            
            # Only check distance if target was detected
            if distance is not None and abs(distance - target_distance) < 0.1 and not reached:
                print("Ziel erreicht!")
                reached = True
        
        time.sleep(0.5)
    
    tracker_proxy.stopTracker()
    return reached





def navigate_to_blob(broker_proxy, blob_detection, tracker_proxy, posture_proxy, color_name, duration=60):

    
    global ColorDetector
    
    ColorDetector = BlobTracker("ColorDetector")
        
    print("Detection")
    detection = setup_blob_detection(blob_detection, color_name)

    print("get distance to target")
    target_distance = get_distance_to_target(tracker_proxy)
    
    # Use default distance if no target detected initially
    if target_distance is None:
        print("No target detected, using default distance")
        target_distance = 0.5
    
    print("Tracker")
    tracker = setup_tracker(tracker_proxy, target_distance)
    
    print("Tracking blob".format(color_name))
    reached = track_blob(tracker, duration, target_distance)
    
    detection.unsubscribe("BlobNav")
    posture_proxy.goToPosture("Sit")
    broker_proxy.shutdown()
    
    return reached


if __name__ == "__main__":
    nao = InitNao()
    broker = ALBroker(
        "MoveToBlobBroker",
        "0.0.0.0",   
        0,          
        "192.168.1.118",
        9559
    )
    blob_detection = nao.get_proxy("ALColorBlobDetection")
    tracker_proxy = nao.get_proxy("ALTracker")
    posture_proxy = nao.get_proxy("ALRobotPosture")
    color = "red"

    navigate_to_blob(broker, blob_detection, tracker_proxy, posture_proxy, color, duration=60)