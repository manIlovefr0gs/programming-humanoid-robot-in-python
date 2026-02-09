class TrackerConfig:
    
    TARGET_COLOR = "red"
    
    # Scan parameters
    SCAN_HEAD_YAW_MIN = -2.0  # radians (~-115°)
    SCAN_HEAD_YAW_MAX = 2.0   # radians (~115°)
    SCAN_HEAD_PITCH = 0.0     # radians (horizontal)
    SCAN_SPEED = 0.15         # radians/sec
    SCAN_STEP_TIME = 0.5      # seconds between scan steps
    
    # ALTracker parameters
    TRACKER_MODE = "Head"     # Only move head
    TRACKER_EFFECTOR = "None" # No effector needed
    
    # State machine timeouts
    LOST_TIMEOUT = 4.0        # seconds before returning to scan
    
    # Vision parameters
    BLOB_MIN_SIZE = 40