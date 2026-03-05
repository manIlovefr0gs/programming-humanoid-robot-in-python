# -*- coding: utf-8 -*-

try:
    import numpy as np
except Exception:
    np = None

try:
    import cv2
except Exception:
    cv2 = None

try:
    from . import config
except (ImportError, ValueError):
    import config


def ensure_numpy():
    if np is None:
        raise RuntimeError("NumPy ist erforderlich, um den Bildstream zu dekodieren.")


def fourcc_mjpg():
    if cv2 is None:
        return None
    if hasattr(cv2, "VideoWriter_fourcc"):
        return cv2.VideoWriter_fourcc(*"MJPG")
    if hasattr(cv2, "cv") and hasattr(cv2.cv, "CV_FOURCC"):
        return cv2.cv.CV_FOURCC(*"MJPG")
    return None


def color_ranges(color_name):
    if color_name is None:
        return None
    key = str(color_name).strip().lower()
    return config.HSV_COLOR_PRESETS.get(key)


def grab_frame(video, handle):
    ensure_numpy()
    img = video.getImageRemote(handle)
    if img is None or len(img) < 7:
        return None, None, None
    width = img[0]
    height = img[1]
    data = img[6]
    frame = np.frombuffer(data, dtype=np.uint8)
    frame = frame.reshape((height, width, 3))
    try:
        video.releaseImage(handle)
    except Exception:
        pass
    return frame, width, height


def detect_blob(frame, color_name, min_area, max_area, kernel_size=None):
    if cv2 is None or np is None or frame is None:
        return None
    ranges = color_ranges(color_name)
    if not ranges:
        return None
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = None
    for (lower, upper) in ranges:
        lower_np = np.array(lower, dtype=np.uint8)
        upper_np = np.array(upper, dtype=np.uint8)
        part = cv2.inRange(hsv, lower_np, upper_np)
        mask = part if mask is None else cv2.bitwise_or(mask, part)
    if kernel_size is None:
        kernel_size = config.MASK_KERNEL_SIZE
    if kernel_size and kernel_size > 1:
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    if not cnts:
        return None

    best = None
    best_area = 0.0
    for c in cnts:
        area = cv2.contourArea(c)
        if area < float(min_area):
            continue
        if max_area is not None and area > float(max_area):
            continue
        if area > best_area:
            best_area = area
            best = c

    if best is None:
        return None

    m = cv2.moments(best)
    if m.get("m00", 0) == 0:
        return None
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])
    x, y, w, h = cv2.boundingRect(best)
    return {
        "center": (cx, cy),
        "area": best_area,
        "bbox": (x, y, w, h),
        "contour": best,
        "mask": mask,
    }
