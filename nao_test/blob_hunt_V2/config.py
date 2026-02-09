# -*- coding: utf-8 -*-

try:
    import vision_definitions as vd
except Exception:
    class _VisionDefinitions(object):
        kQQVGA = 0
        kQVGA = 1
        kVGA = 2
        kBGRColorSpace = 13
        kYuvColorSpace = 0
    vd = _VisionDefinitions()


# === Simple blob tracking configuration ===
# Search (scan) mode
SCAN_YAWS = [-1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2]
SCAN_PITCH = 0.1
SCAN_SPEED = 0.12
SCAN_HOLD_S = 0.6

# Tracking mode
TRACK_COLOR = "rot"  # "rot"/"gruen"/"blau" or "red"/"green"/"blue"
TRACK_MIN_AREA = 300
TRACK_MAX_AREA = None
TRACK_DEADBAND = 0.05  # normalized error (0..1)
TRACK_YAW_K = 0.6
TRACK_PITCH_K = 0.45
TRACK_MAX_STEP = 0.20  # rad per update
TRACK_SPEED = 0.08
TRACK_LOST_TIMEOUT_S = 0.8
TRACK_CONTROL_INTERVAL_S = 0.12
TRACK_INVERT_YAW = False
TRACK_INVERT_PITCH = False

# Morphology
MASK_KERNEL_SIZE = 5

# Video
VIDEO_FPS = 15
VIDEO_RESOLUTION = vd.kQVGA
VIDEO_CAMERA_ID = 0  # 0 = top, 1 = bottom
VIDEO_COLOR_SPACE = vd.kBGRColorSpace


HSV_COLOR_PRESETS = {
    "red": [((0, 120, 70), (10, 255, 255)),
            ((170, 120, 70), (180, 255, 255))],
    "rot": [((0, 120, 70), (10, 255, 255)),
            ((170, 120, 70), (180, 255, 255))],
    "green": [((36, 80, 70), (85, 255, 255))],
    "gruen": [((36, 80, 70), (85, 255, 255))],
    "blue": [((90, 80, 70), (130, 255, 255))],
    "blau": [((90, 80, 70), (130, 255, 255))],
}
