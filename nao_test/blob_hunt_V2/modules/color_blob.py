# Wrapper für ALColorBlobDetection
#
# ALColorBlobDetection läuft intern auf dem Roboter und schreibt Detektionen
# in ALMemory unter dem Key "ALTracker/ColorBlobDetected".
# Dieser Key wird direkt von ALTracker.trackEvent() konsumiert.

import config

# ALMemory-Key, in den ALColorBlobDetection sein Ergebnis schreibt
MEMORY_KEY = "ALTracker/ColorBlobDetected"


def subscribe(blob_proxy, color_name):
    """Konfiguriert ALColorBlobDetection und startet die Erkennung.

    Args:
        blob_proxy:  ALColorBlobDetection-Proxy
        color_name:  Farbname (z.B. "rot", "red")
    """
    key  = str(color_name).strip().lower()
    rgba = config.RGB_COLOR_PRESETS.get(key)
    if rgba is None:
        raise ValueError("Unbekannte Farbe: '{}'. Verfügbar: {}".format(
            color_name, list(config.RGB_COLOR_PRESETS.keys())))

    r, g, b, threshold = rgba
    blob_proxy.setColor(r, g, b, threshold)
    blob_proxy.setObjectProperties(config.OBJECT_MIN_SIZE_PX, config.OBJECT_SPAN_M, "Unknown")
    blob_proxy.subscribe("blob_tracker")


def unsubscribe(blob_proxy):
    """Stoppt ALColorBlobDetection."""
    try:
        blob_proxy.unsubscribe("blob_tracker")
    except Exception:
        pass


def is_detected(memory_proxy):
    """Gibt True zurück wenn gerade ein Blob sichtbar ist.

    Liest den ALMemory-Key, den ALColorBlobDetection befüllt.
    """
    try:
        val = memory_proxy.getData(MEMORY_KEY)
        return val is not None and len(val) > 0
    except Exception:
        return False