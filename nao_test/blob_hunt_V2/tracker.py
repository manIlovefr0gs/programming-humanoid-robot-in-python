# -*- coding: utf-8 -*-
from naoqi import ALProxy
import time
import os

try:
    from . import config
    from .vision import grab_frame, detect_blob, fourcc_mjpg, cv2, np
    from .head_control import clamp, get_head_limits
except (ImportError, ValueError):
    import config
    from vision import grab_frame, detect_blob, fourcc_mjpg, cv2, np
    from head_control import clamp, get_head_limits


def run_head_tracker(nao, frame_callback=None, show_preview=False, save_local=True):
    """Search (scan) for a color blob and track it once detected."""

    motion = None
    video = None
    handle = None
    writer = None

    try:
        # Verbindung zu NAO herstellen
        print("Verbinde mit NAO...")
        motion = ALProxy("ALMotion", nao.ip, nao.port)

        # Stiffness aktivieren (Motoren einschalten)
        print("Aktiviere Motoren...")
        motion.setStiffnesses("Head", 1.0)
        time.sleep(1.0)

        # Stream konfigurieren (BGR für OpenCV)
        video = ALProxy("ALVideoDevice", nao.ip, nao.port)
        handle = video.subscribeCamera(
            "head_turn_stream",
            config.VIDEO_CAMERA_ID,
            config.VIDEO_RESOLUTION,
            config.VIDEO_COLOR_SPACE,
            config.VIDEO_FPS,
        )
        print("Video-Stream abonniert ({} fps).".format(config.VIDEO_FPS))

        # Lokale Videoausgabe vorbereiten
        output_path = None
        if show_preview and cv2 is None:
            print("OpenCV nicht gefunden: Vorschau deaktiviert.")
            show_preview = False
        if save_local and cv2 is None:
            print("OpenCV nicht gefunden: lokales Speichern deaktiviert.")
            save_local = False
        if save_local:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(
                output_dir,
                "head_track_{}.avi".format(time.strftime("%Y%m%d_%H%M%S")),
            )

        if cv2 is None:
            print("Warnung: OpenCV fehlt, Tracking deaktiviert (nur Scan).")
        if np is None:
            print("Warnung: NumPy fehlt, Tracking deaktiviert (nur Scan).")

        # Init
        yaw_limits, pitch_limits = get_head_limits(motion)
        scan_index = 0
        scan_dir = 1
        next_scan_ts = 0.0
        last_seen_ts = 0.0
        last_control_ts = 0.0
        mode = "search"

        if config.SCAN_YAWS:
            motion.setAngles(
                ["HeadYaw", "HeadPitch"],
                [config.SCAN_YAWS[0], config.SCAN_PITCH],
                config.SCAN_SPEED,
            )

        print("Starte Suche/Tracking...")
        print("(Druecken Sie Ctrl+C zum Beenden)")

        next_ts = time.time()
        printed_path = False
        while True:
            now = time.time()
            try:
                frame, width, height = grab_frame(video, handle)
            except Exception:
                frame, width, height = None, None, None

            detection = None
            if frame is not None and cv2 is not None and np is not None:
                detection = detect_blob(
                    frame,
                    config.TRACK_COLOR,
                    config.TRACK_MIN_AREA,
                    config.TRACK_MAX_AREA,
                )

            if detection is not None:
                last_seen_ts = now
                if mode != "track":
                    mode = "track"
                    print("  -> Tracking mode")

                if (now - last_control_ts) >= config.TRACK_CONTROL_INTERVAL_S and width and height:
                    cx, cy = detection["center"]
                    err_x = (float(cx) - (width / 2.0)) / (width / 2.0)
                    err_y = (float(cy) - (height / 2.0)) / (height / 2.0)

                    if config.TRACK_INVERT_YAW:
                        err_x = -err_x
                    if config.TRACK_INVERT_PITCH:
                        err_y = -err_y

                    if abs(err_x) < config.TRACK_DEADBAND:
                        err_x = 0.0
                    if abs(err_y) < config.TRACK_DEADBAND:
                        err_y = 0.0

                    delta_yaw = -err_x * config.TRACK_YAW_K
                    delta_pitch = -err_y * config.TRACK_PITCH_K
                    delta_yaw = clamp(delta_yaw, -config.TRACK_MAX_STEP, config.TRACK_MAX_STEP)
                    delta_pitch = clamp(delta_pitch, -config.TRACK_MAX_STEP, config.TRACK_MAX_STEP)

                    current = motion.getAngles(["HeadYaw", "HeadPitch"], True)
                    target_yaw = clamp(current[0] + delta_yaw, yaw_limits[0], yaw_limits[1])
                    target_pitch = clamp(current[1] + delta_pitch, pitch_limits[0], pitch_limits[1])
                    motion.setAngles(
                        ["HeadYaw", "HeadPitch"],
                        [target_yaw, target_pitch],
                        config.TRACK_SPEED,
                    )
                    last_control_ts = now
            else:
                if mode == "track" and (now - last_seen_ts) > config.TRACK_LOST_TIMEOUT_S:
                    mode = "search"
                    print("  -> Search mode")

                if mode == "search" and now >= next_scan_ts and config.SCAN_YAWS:
                    yaw = config.SCAN_YAWS[scan_index]
                    motion.setAngles(
                        ["HeadYaw", "HeadPitch"],
                        [yaw, config.SCAN_PITCH],
                        config.SCAN_SPEED,
                    )
                    next_scan_ts = now + config.SCAN_HOLD_S
                    scan_index += scan_dir
                    if scan_index >= len(config.SCAN_YAWS) or scan_index < 0:
                        scan_dir *= -1
                        scan_index += scan_dir

            if frame is not None:
                frame_out = frame
                if show_preview or save_local:
                    frame_out = frame.copy()
                    if cv2 is not None:
                        center = (int(width / 2), int(height / 2))
                        cv2.drawMarker(
                            frame_out,
                            center,
                            (255, 255, 255),
                            cv2.MARKER_CROSS,
                            12,
                            1,
                        )
                        if detection is not None:
                            x, y, w, h = detection["bbox"]
                            cv2.rectangle(frame_out, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cx, cy = detection["center"]
                            cv2.circle(frame_out, (cx, cy), 4, (0, 255, 0), -1)
                        cv2.putText(
                            frame_out,
                            "Mode: {}".format(mode),
                            (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 255),
                            1,
                        )

                if save_local and writer is None and output_path is not None:
                    fourcc = fourcc_mjpg()
                    if fourcc is None:
                        writer = cv2.VideoWriter(output_path, 0, config.VIDEO_FPS, (width, height))
                    else:
                        writer = cv2.VideoWriter(output_path, fourcc, config.VIDEO_FPS, (width, height))
                    if hasattr(writer, "isOpened") and not writer.isOpened():
                        writer = None
                        print("Konnte lokales Video nicht oeffnen:", output_path)
                    else:
                        printed_path = True
                if writer is not None:
                    writer.write(frame_out)
                if show_preview and cv2 is not None:
                    cv2.imshow("NAO Stream", frame_out)
                    cv2.waitKey(1)
                if frame_callback is not None:
                    try:
                        frame_callback(frame)
                    except Exception:
                        pass

            if printed_path:
                print("Lokales Video:", output_path)
                printed_path = False

            next_ts += 1.0 / float(config.VIDEO_FPS)
            sleep_s = next_ts - time.time()
            if sleep_s > 0:
                time.sleep(sleep_s)

    except KeyboardInterrupt:
        print("\n\nScan abgebrochen durch Benutzer.")

    except Exception as e:
        print("FEHLER: " + str(e))
        print("Stelle sicher, dass:")
        print("  1. NAO eingeschaltet ist")
        print("  2. IP-Adresse korrekt ist: " + nao.ip)
        print("  3. Netzwerkverbindung besteht")

    finally:
        # Stream sauber beenden
        try:
            if writer is not None:
                writer.release()
                print("Lokales Video gespeichert.")
            if video is not None and handle is not None:
                video.unsubscribe(handle)
                print("Video-Stream beendet.")
            if show_preview and cv2 is not None:
                cv2.destroyAllWindows()
        except Exception:
            pass

        # Motoren ausschalten (Energiesparen)
        try:
            print("\nSchalte Motoren aus...")
            motion.setStiffnesses("Head", 0.0)
            print("Fertig!")
        except Exception:
            pass
