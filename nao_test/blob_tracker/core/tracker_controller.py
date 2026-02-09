import time
from enum import Enum


class State(Enum):
    SCAN = "SCAN"
    TRACKING = "TRACKING"
    LOST = "LOST"


class TrackerController:
    
    def __init__(self, nao_config, tracker_config, vision_module, motion_module, tracker_module, event_handler):
        self.nao = nao_config
        self.config = tracker_config
        
        self.vision = vision_module
        self.motion = motion_module
        self.tracker = tracker_module
        self.events = event_handler
        
        self._state = State.SCAN
        self._running = False
        self._last_detection_time = 0
    
    
    def initialize(self):
        print("[Controller] Initializing all modules")
        
        self.vision.initialize()
        self.motion.initialize()
        self.tracker.initialize()
        self.events.initialize()
        
        print("[Controller] All modules initialized")
    
    
    def start(self):
        if self._running:
            print("[Controller] Already running")
            return
        
        print("[Controller] Starting tracker")
        self._running = True
        self._state = State.SCAN
        
        self.vision.start()
        self.motion.start_scan()
        
        print(f"[Controller] Started in state: {self._state.value}")
    
    
    def stop(self):
        if not self._running:
            return
        
        print("[Controller] Stopping tracker...")
        self._running = False
        
        self.tracker.stop_tracking()
        self.motion.stop_scan()
        self.vision.stop()
        self.motion.disable_stiffness()
        
        print("[Controller] Stopped")
    
    
    def update(self):
        if not self._running:
            return
        
        blob_info = self.vision.get_blob_position()
        
        # State machine logic
        if self._state == State.SCAN:
            self._handle_scan_state(blob_info)
        
        elif self._state == State.TRACKING:
            self._handle_tracking_state(blob_info)
        
        elif self._state == State.LOST:
            self._handle_lost_state(blob_info)
    
    
    def _handle_scan_state(self, blob_info):
        self.motion.scan_step()
        
        if blob_info['detected']:
            print("[Controller] Blob detected! Switching to TRACKING")
            self._transition_to_tracking()
    
    
    def _handle_tracking_state(self, blob_info):
        if blob_info['detected']:
            self._last_detection_time = time.time()
        else:
            # Check if lost for too long
            time_since_last = time.time() - self._last_detection_time
            if time_since_last > self.config.LOST_TIMEOUT:
                print("[Controller] Blob lost! Switching to SCAN")
                self._transition_to_scan()
    
    
    def _handle_lost_state(self, blob_info):
        """Handle LOST state (currently unused, goes directly to SCAN)"""
        pass
    
    
    def _transition_to_tracking(self):
        """Transition from SCAN to TRACKING"""
        self.motion.stop_scan()
        self.tracker.start_tracking("ColorBlob")
        self._state = State.TRACKING
        self._last_detection_time = time.time()
    
    
    def _transition_to_scan(self):
        self.tracker.stop_tracking()
        self.motion.start_scan()
        self._state = State.SCAN
    
    
    def get_state(self):
        return self._state
    
    
    def is_running(self):
        return self._running
