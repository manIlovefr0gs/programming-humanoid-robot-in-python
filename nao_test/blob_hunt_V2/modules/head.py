# Kopf-Limits auslesen und Hilfsfunktionen für Winkelberechnungen

import config


def clamp(value, lower, upper):
    """Begrenzt value auf [lower, upper]."""
    return max(lower, min(upper, value))


def get_head_limits(motion):
    """Liest Hardware-Limits für HeadYaw und HeadPitch vom Roboter.
    Gibt ((yaw_min, yaw_max), (pitch_min, pitch_max)) zurück."""
    try:
        y = motion.getLimits("HeadYaw")[0]
        p = motion.getLimits("HeadPitch")[0]
        return (y[0], y[1]), (p[0], p[1])
    except Exception:
        return (-2.0857, 2.0857), (-0.6720, 0.5149)


def get_dynamic_pitch_limits(yaw, default_pitch_limits):
    """Interpoliert die Pitch-Limits abhängig vom aktuellen Yaw-Winkel.
    Berücksichtigt HEAD_YAW_PITCH_LIMITS aus der Konfiguration."""
    table = getattr(config, "HEAD_YAW_PITCH_LIMITS", None)
    if not table:
        pitch_min, pitch_max = default_pitch_limits
    else:
        yaw_abs = abs(float(yaw))
        points  = sorted(table, key=lambda x: x[0])
        if yaw_abs <= points[0][0]:
            pitch_min, pitch_max = points[0][1], points[0][2]
        elif yaw_abs >= points[-1][0]:
            pitch_min, pitch_max = points[-1][1], points[-1][2]
        else:
            pitch_min, pitch_max = points[0][1], points[0][2]
            for i in range(len(points) - 1):
                y0, pmin0, pmax0 = points[i]
                y1, pmin1, pmax1 = points[i + 1]
                if y0 <= yaw_abs <= y1:
                    t         = (yaw_abs - y0) / (y1 - y0) if y1 != y0 else 0.0
                    pitch_min = pmin0 + (pmin1 - pmin0) * t
                    pitch_max = pmax0 + (pmax1 - pmax0) * t
                    break
        pitch_min = max(float(default_pitch_limits[0]), pitch_min)
        pitch_max = min(float(default_pitch_limits[1]), pitch_max)

    if pitch_min > pitch_max:
        pitch_min = pitch_max
    return pitch_min, pitch_max