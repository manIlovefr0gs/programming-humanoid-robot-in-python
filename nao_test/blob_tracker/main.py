import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nao_config import InitNao
from config.tracker_config import TrackerConfig
from modules.vision_module import VisionModule
from modules.motion_module import MotionModule
from modules.tracker_module import TrackerModule
from core.event_handler import EventHandler
from core.tracker_controller import TrackerController


def main():
    print("=" *50)
    print("Start Blob Tracker")
    
    #inti
    nao = InitNao()
    config = TrackerConfig()
    
    # modules   
    vision = VisionModule(nao, config.TARGET_COLOR, config.BLOB_MIN_SIZE)
    motion = MotionModule(nao, config)
    tracker = TrackerModule(nao, config)
    events = EventHandler(nao)
    
    #controller
    controller = TrackerController(nao, config, vision, motion, tracker, events)
    
    try:
        controller.initialize()
        controller.start()
        
        print("[Main] Tracker running. Press Ctrl+C to stop.")
        print("[Main] Tracking color: " + config.TARGET_COLOR)
        print("[Main] Current state: " + controller.get_state().value)
        
        # Main loop
        while True:
            controller.update()
            time.sleep(0.1)  # 10Hz update rate
    
    except KeyboardInterrupt:
        print("[Main] Keyboard interrupt received")
    
    except Exception as e:
        print("[Main] Error: " e.toString())
    
    finally:
        print("[Main] Shutting down...")
        controller.stop()
        print("[Main] Shutdown complete")
        print("=" * 50)


if __name__ == "__main__":
    main()