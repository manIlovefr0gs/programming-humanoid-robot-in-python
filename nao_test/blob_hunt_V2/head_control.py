# -*- coding: utf-8 -*-


def clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def get_head_limits(motion):
    try:
        yaw_limits = motion.getLimits("HeadYaw")[0]
        pitch_limits = motion.getLimits("HeadPitch")[0]
        return (yaw_limits[0], yaw_limits[1]), (pitch_limits[0], pitch_limits[1])
    except Exception:
        return (-2.0857, 2.0857), (-0.6720, 0.5149)
