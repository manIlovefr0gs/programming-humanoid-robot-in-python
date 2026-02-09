

class TrackerModule:
    
    def __init__(self, nao_config, tracker_config):
        self.nao = nao_config
        self.config = tracker_config
        
        self.tracker_proxy = None
        self._tracking = False
    
    
    def initialize(self):
        """Initialize ALTracker"""
        self.tracker_proxy = self.nao.get_proxy("ALTracker")
        
        # Set tracker mode (only head movement)
        self.tracker_proxy.setMode(self.config.TRACKER_MODE)
        
        print("[Tracker] Initialized in mode: " + self.config.TRACKER_MODE)
    
    
    def start_tracking(self, target="ColorBlob"):
        """Start tracking the color blob"""
        if self._tracking:
            return
        
        # Register target with ALTracker
        self.tracker_proxy.registerTarget(target, 0.1)  # 0.1m diameter estimate
        self.tracker_proxy.track(target)
        
        self._tracking = True
        print("[Tracker] Started tracking: " + target)
    
    
    def stop_tracking(self):
        if not self._tracking:
            return
        
        self.tracker_proxy.stopTracker()
        self.tracker_proxy.unregisterAllTargets()
        
        self._tracking = False
        print("[Tracker] Stopped tracking")
    
    
    def is_tracking(self):
        """Check if currently tracking"""
        return self._tracking
    
    
    def get_target_position(self):
        """Get current target position from tracker"""
        try:
            position = self.tracker_proxy.getTargetPosition(0)  # Frame 0 = Torso
            return {'x': position[0], 'y': position[1], 'z': position[2]}
        except:
            return None
