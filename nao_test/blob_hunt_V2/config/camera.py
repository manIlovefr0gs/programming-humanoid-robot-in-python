# Kamera-Stream und Farbprofile für ALColorBlobDetection

try:
    import vision_definitions as vd
except ImportError:
    class _VD:
        kQVGA          = 1
        kBGRColorSpace = 13
    vd = _VD()

VIDEO_FPS         = 15
VIDEO_RESOLUTION  = vd.kQVGA # kVGA    
VIDEO_CAMERA_ID   = 0
VIDEO_COLOR_SPACE = vd.kBGRColorSpace

# Farbe, die verfolgt werden soll ("rot"/"gruen"/"blau" oder "red"/"green"/"blue")
TRACK_COLOR = "rot"

# Physikalische Größe des Objekts in Metern (Flaschendurchmesser ~0.08m)
# Wird von ALColorBlobDetection für die Distanzschätzung genutzt.
OBJECT_SPAN_M = 0.08

# Minimale Blob-Größe in Pixeln (Falschdetektionen unterdrücken)
OBJECT_MIN_SIZE_PX = 100

# RGB-Farben für ALColorBlobDetection: (R, G, B, colorThreshold)
# colorThreshold: Toleranz der Farberkennung (0-255); höher = toleranter
RGB_COLOR_PRESETS = {
    "red":   (220,  30,  30, 80),
    "rot":   (220,  30,  30, 80),
    "green": ( 30, 180,  30, 80),
    "gruen": ( 30, 180,  30, 80),
    "blue":  ( 30,  30, 220, 80),
    "blau":  ( 30,  30, 220, 80),
}s