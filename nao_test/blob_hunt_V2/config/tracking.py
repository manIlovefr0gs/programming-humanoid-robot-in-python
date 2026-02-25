# Parameter für Scan-Bewegung, ALTracker-Annäherung und Destroy

# --- Scan-Bewegung (eigene Implementierung, solange kein Objekt gefunden) ---
SCAN_YAWS    = [-1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2]  # Yaw-Positionen [rad]
SCAN_PITCHES = [0.02, 0.200015]                           # Pitch-Positionen [rad]
SCAN_SPEED   = 0.12
SCAN_HOLD_S  = 0.6    # Haltezeit pro Scan-Position in Sekunden

# --- NAO Kopf-Pitch-Limits in Abhängigkeit vom Yaw (für Scan-Bewegung) ---
# Format: (|yaw| [rad], pitch_min [rad], pitch_max [rad])
HEAD_YAW_PITCH_LIMITS = [
    (0.000000, -0.671951, 0.515047),
    (0.486074, -0.671951, 0.422021),
    (0.756077, -0.548033, 0.370010),
    (0.903033, -0.479965, 0.330041),
    (1.089958, -0.430049, 0.300022),
    (1.526988, -0.330041, 0.200015),
    (2.086017, -0.449073, 0.330041),
]

# --- ALTracker-Annäherung ---
# Der Roboter hält an, sobald er APPROACH_STOP_DISTANCE_M vor dem Ziel ist.
# APPROACH_STOP_TOLERANCE_M ist die erlaubte Abweichung (x, y, Winkel).
APPROACH_STOP_DISTANCE_M  = 0.30   # Stopp-Distanz zum Objekt in Metern
APPROACH_STOP_TOLERANCE_M = 0.05   # Positionstoleranz in Metern
TRACK_LOST_TIMEOUT_S      = 1.5    # Sekunden bis Rückkehr zu SEARCH wenn Ziel verloren

# --- Destroy ---
DESTROY_EXTRA_FORWARD_M = 0.35   # Extra-Schub nach Erreichen der Stopp-Distanz