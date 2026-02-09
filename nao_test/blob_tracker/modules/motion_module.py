import time


class MotionModule:
    
    def __init__(self, nao_config, scan_config):
        self.nao = nao_config
        self.config = scan_config
        
        self.motion_proxy = None
        self._scanning = False
        self._scan_direction = 1  # 1 = right, -1 = left
        self._current_yaw = 0.0
    
    
    def initialize(self):
        self.motion_proxy = self.nao.get_proxy("ALMotion")
        
        # Enable head stiffness
        self.motion_proxy.setStiffnesses("Head", 1.0)
        print("[Motion] Initialized and stiffness enabled")
    
    
    def start_scan(self):
        self._scanning = True
        print("[Motion] Started scanning")
    
    
    def stop_scan(self):
        self._scanning = False
        print("[Motion] Stopped scanning")
    
    
    def scan_step(self):
        if not self._scanning:
            return
        
        # Calculate next position
        self._current_yaw += self._scan_direction * self.config.SCAN_SPEED * self.config.SCAN_STEP_TIME
        
        # Reverse direction at limits
        if self._current_yaw >= self.config.SCAN_HEAD_YAW_MAX:
            self._current_yaw = self.config.SCAN_HEAD_YAW_MAX
            self._scan_direction = -1
        elif self._current_yaw <= self.config.SCAN_HEAD_YAW_MIN:
            self._current_yaw = self.config.SCAN_HEAD_YAW_MIN
            self._scan_direction = 1
        
        # Move head
        self.motion_proxy.setAngles(
            ["HeadYaw", "HeadPitch"],
            [self._current_yaw, self.config.SCAN_HEAD_PITCH],
            0.3  # Speed fraction
        )
    
    
    def get_current_head_position(self):
        angles = self.motion_proxy.getAngles(["HeadYaw", "HeadPitch"], True)
        return {'yaw': angles[0], 'pitch': angles[1]}
    
    
    def disable_stiffness(self):
        if self.motion_proxy:
            self.motion_proxy.setStiffnesses("Head", 0.0)
            print("[Motion] Stiffness disabled")
