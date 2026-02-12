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


# Search pattern
SCAN_YAWS = [-1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2]
SCAN_PITCHES = [0.02, 0.200015]  # ~0 deg and 11.46 deg down
SCAN_SPEED = 0.12
SCAN_HOLD_S = 0.6  # Increase if head misses targets while scanning quickly.


# Blob tracking
TRACK_COLOR = "rot"  # "rot"/"gruen"/"blau" or "red"/"green"/"blue"
TRACK_MIN_AREA = 200  # Increase if false blobs from noise are detected.
TRACK_MAX_AREA = None
TRACK_DEADBAND = 0.05  # Increase if head jitters around a centered object.
TRACK_YAW_K = 0.6  # Increase if yaw reacts too slowly; reduce if it oscillates.
TRACK_PITCH_K = 0.45  # Increase if pitch reacts too slowly; reduce if it oscillates.
TRACK_MAX_STEP = 0.20  # Reduce for smoother motion on weak/old head motors.
TRACK_SPEED = 0.08
TRACK_CONTROL_INTERVAL_S = 0.12  # Lower for tighter tracking, higher for calmer motion.
TRACK_LOST_TIMEOUT_S = 0.8  # Increase if brief occlusions should not reset search.
TRACK_INVERT_YAW = False  # Set True if yaw moves in the wrong direction.
TRACK_INVERT_PITCH = False  # Set True if pitch moves opposite of expected.
TRACK_PITCH_MIN = 0.0  # Never look above horizon: negative pitch means "up".


# NAO yaw-dependent head pitch limits: (abs(yaw_rad), pitch_min_rad, pitch_max_rad)
HEAD_YAW_PITCH_LIMITS = [
    (0.000000, -0.671951, 0.515047),
    (0.486074, -0.671951, 0.422021),
    (0.756077, -0.548033, 0.370010),
    (0.903033, -0.479965, 0.330041),
    (1.089958, -0.430049, 0.300022),
    (1.526988, -0.330041, 0.200015),
    (2.086017, -0.449073, 0.330041),
]


# Destroy behavior
DESTROY_PITCH_MARGIN_RAD = 0.03  # Increase if max-down trigger is reached too late.
DESTROY_YAW_TOLERANCE_RAD = 0.20  # Increase if trigger is too strict while still centered.
DESTROY_EXTRA_FORWARD_M = 0.50  # Extra push distance after max-down pitch is reached.


# Locomotion
LOCOMOTION_ENABLED = True
LOCOMOTION_INIT_POSTURE = "StandInit"
LOCOMOTION_POSTURE_SPEED = 0.5
APPROACH_FORWARD_X = 0.20  # Increase for faster approach; reduce for safer behavior.
APPROACH_THETA_K = 0.45  # Increase if robot does not turn enough toward the target.
APPROACH_MAX_THETA = 0.18
MOVE_FREQUENCY = 0.50
MOVE_CONTROL_INTERVAL_S = 0.18  # Lower for more responsive steering updates.


# Vision cleanup
MASK_KERNEL_SIZE = 5  # Reduce to keep tiny blobs; increase to suppress noisy masks.


# Status announcements
STATUS_SPEECH_ENABLED = True  # Set False for console-only messages.


# Video stream
VIDEO_FPS = 15
VIDEO_RESOLUTION = vd.kQVGA
VIDEO_CAMERA_ID = 0
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
