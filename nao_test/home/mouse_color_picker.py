import cv2
import numpy as np
from typing import Optional, Tuple

# Einfacher Satz vordefinierter HSV-Bereiche (kann angepasst werden)
COLOR_RANGES = {
    'rot': [((0, 100, 100), (10, 255, 255)), ((170, 100, 100), (180, 255, 255))],
    'gelb': [((20, 100, 100), (30, 255, 255))],
    'grün': [((35, 100, 100), (85, 255, 255))],
    'blau': [((90, 100, 100), (130, 255, 255))],
    'orange': [((10, 100, 100), (20, 255, 255))],
}


def detect_color_at_position(frame: np.ndarray, x: int, y: int, sample_size: int = 3) -> Optional[Tuple[Optional[str], Tuple[int, int, int]]]:
    """
    Bestimmt die (vordefinierte) Farbe an einer Bildposition.

    Args:
        frame: BGR-Bild (np.ndarray)
        x, y: Pixelkoordinate (ints)
        sample_size: Radius des zu mittelden Bereichs (kleines Quadrat)

    Returns:
        Tuple (color_name or None, (H, S, V)) oder None wenn außerhalb
    """
    h, w = frame.shape[:2]
    if x < 0 or y < 0 or x >= w or y >= h:
        return None

    x0 = max(0, x - sample_size)
    y0 = max(0, y - sample_size)
    x1 = min(w - 1, x + sample_size)
    y1 = min(h - 1, y + sample_size)

    roi = frame[y0:y1 + 1, x0:x1 + 1]
    if roi.size == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h_mean = int(hsv[:, :, 0].mean())
    s_mean = int(hsv[:, :, 1].mean())
    v_mean = int(hsv[:, :, 2].mean())

    # Prüfen, welche definierte Farbe passt
    for name, ranges in COLOR_RANGES.items():
        for lower, upper in ranges:
            lh, ls, lv = lower
            uh, us, uv = upper
            if lh <= h_mean <= uh and ls <= s_mean <= us and lv <= v_mean <= uv:
                return name, (h_mean, s_mean, v_mean)

    return None, (h_mean, s_mean, v_mean)


# Kleiner Demo-Runner (zeigt Mausbewegung und Lock per Klick)
if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    win = 'Color Picker'
    cv2.namedWindow(win)

    mouse = {'x': -1, 'y': -1, 'locked': False, 'locked_color': None}

    def on_mouse(e, x, y, f, p):
        mouse['x'] = x
        mouse['y'] = y
        if e == cv2.EVENT_LBUTTONDOWN:
            mouse['locked'] = not mouse['locked']
            if not mouse['locked']:
                mouse['locked_color'] = None

    cv2.setMouseCallback(win, on_mouse)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        mx, my = mouse['x'], mouse['y']
        color_name = None
        hsv = None
        if mx >= 0 and my >= 0:
            res = detect_color_at_position(frame, mx, my)
            if res is not None:
                color_name, hsv = res
            if mouse['locked'] and mouse['locked_color'] is None and color_name:
                mouse['locked_color'] = color_name

        # Overlay
        if mx >= 0 and my >= 0:
            cv2.circle(frame, (mx, my), 6, (255, 255, 255), 2)
            lbl = ''
            if mouse['locked_color']:
                lbl = f'LOCKED: {mouse["locked_color"].upper()}'
            elif color_name:
                lbl = f'{color_name.upper()} HSV:{hsv}'
            if lbl:
                cv2.putText(frame, lbl, (mx + 10, my - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow(win, frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
