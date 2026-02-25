# Live-Videostream mit Blob-Overlay und HUD
#
# Zeigt auf der ausführenden Maschine ein Fenster mit:
#   - Kamerabild des NAO
#   - Eingezeichnetem Farb-Blob (Kreis + Mittelpunkt)
#   - HUD: Roboter-Position, Blob-Koordinaten, Distanz, Modus

try:
    import numpy as np
except ImportError:
    np = None

try:
    import cv2
except ImportError:
    cv2 = None

import config

WINDOW_NAME = "NAO Stream"


def subscribe(video_proxy):
    """Abonniert den Kamerastream und gibt das Handle zurück."""
    handle = video_proxy.subscribeCamera(
        "stream_viewer",
        config.VIDEO_CAMERA_ID,
        config.VIDEO_RESOLUTION,
        config.VIDEO_COLOR_SPACE,
        config.VIDEO_FPS,
    )
    return handle


def unsubscribe(video_proxy, handle):
    """Beendet den Kamerastream."""
    try:
        video_proxy.unsubscribe(handle)
    except Exception:
        pass
    try:
        if cv2 is not None:
            cv2.destroyWindow(WINDOW_NAME)
    except Exception:
        pass


def update(video_proxy, handle, blob_proxy, motion_proxy, tracker_proxy, mode):
    """Holt einen Frame, zeichnet Overlay und zeigt ihn an.

    Gibt False zurück wenn OpenCV fehlt oder das Fenster geschlossen wurde.
    """
    if cv2 is None or np is None:
        return False

    # ── Frame holen ──────────────────────────────────────────────────────────
    img = video_proxy.getImageRemote(handle)
    if img is None or len(img) < 7:
        return True
    width, height = img[0], img[1]
    frame = np.frombuffer(img[6], dtype=np.uint8).reshape((height, width, 3))
    try:
        video_proxy.releaseImage(handle)
    except Exception:
        pass

    vis = frame.copy()

    # ── Blob einzeichnen ─────────────────────────────────────────────────────
    blob_cx_px = blob_cy_px = None
    try:
        circle = blob_proxy.getCircle()   # [x_norm, y_norm, radius_norm]
        if circle and len(circle) == 3 and circle[2] > 0:
            cx_px = int(circle[0] * width)
            cy_px = int(circle[1] * height)
            r_px  = int(circle[2] * width)
            blob_cx_px, blob_cy_px = cx_px, cy_px
            cv2.circle(vis, (cx_px, cy_px), r_px,  (0, 255, 0), 2)
            cv2.circle(vis, (cx_px, cy_px), 4,      (0, 255, 0), -1)
            cv2.line(vis,
                     (width // 2, height // 2),
                     (cx_px, cy_px),
                     (0, 255, 255), 1)
    except Exception:
        pass

    # Bildmittelpunkt
    cv2.drawMarker(vis, (width // 2, height // 2),
                   (255, 255, 255), cv2.MARKER_CROSS, 16, 1)

    # ── Daten sammeln ─────────────────────────────────────────────────────────
    robot_x = robot_y = robot_theta = None
    try:
        pos = motion_proxy.getRobotPosition(True)   # True = Sensor-basiert
        robot_x, robot_y, robot_theta = pos[0], pos[1], pos[2]
    except Exception:
        pass

    dist = None
    try:
        tp = tracker_proxy.getTargetPosition(2)     # 2 = FRAME_ROBOT
        if tp and len(tp) >= 1:
            dist = tp[0]
    except Exception:
        pass

    # ── HUD zeichnen ─────────────────────────────────────────────────────────
    _draw_hud(vis, mode, robot_x, robot_y, robot_theta,
              blob_cx_px, blob_cy_px, width, height, dist)

    cv2.imshow(WINDOW_NAME, vis)

    # Fenster geschlossen? (q-Taste oder X-Button)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        return False
    return True


def is_available():
    """Gibt True zurück wenn OpenCV und NumPy verfügbar sind."""
    return cv2 is not None and np is not None


# ---------------------------------------------------------------------------
# Intern
# ---------------------------------------------------------------------------

def _draw_hud(vis, mode, rx, ry, rtheta, bx, by, w, h, dist):
    """Zeichnet das HUD (Heads-Up-Display) in den Frame."""
    lines = []

    # Modus
    lines.append("Modus: {}".format(mode.upper()))

    # Roboter-Position (Odometrie)
    if rx is not None:
        lines.append("Roboter: x={:.2f}m  y={:.2f}m  theta={:.1f}deg".format(
            rx, ry, _deg(rtheta)))
    else:
        lines.append("Roboter: ---")

    # Blob-Position im Bild
    if bx is not None:
        lines.append("Blob px: x={}  y={}".format(bx, by))
        # Normalisierte Abweichung vom Bildmittelpunkt
        err_x = (bx - w / 2.0) / (w / 2.0)
        err_y = (by - h / 2.0) / (h / 2.0)
        lines.append("Blob err: dx={:.2f}  dy={:.2f}".format(err_x, err_y))
    else:
        lines.append("Blob: nicht sichtbar")

    # Distanz zum Ziel
    if dist is not None:
        lines.append("Distanz: {:.2f} m".format(dist))
    else:
        lines.append("Distanz: ---")

    # Hintergrund-Box für Lesbarkeit
    line_h   = 18
    padding  = 6
    box_w    = 310
    box_h    = len(lines) * line_h + padding * 2
    overlay  = vis.copy()
    cv2.rectangle(overlay, (0, 0), (box_w, box_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, vis, 0.5, 0, vis)

    for i, text in enumerate(lines):
        y = padding + (i + 1) * line_h
        cv2.putText(vis, text, (padding, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def _deg(rad):
    if rad is None:
        return 0.0
    import math
    return math.degrees(rad)