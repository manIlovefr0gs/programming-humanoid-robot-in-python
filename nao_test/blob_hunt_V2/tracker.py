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


def _move_toward(motion, x, y, theta, frequency):
    try:
        motion.moveToward(float(x), float(y), float(theta), [["Frequency", float(frequency)]])
    except Exception:
        motion.moveToward(float(x), float(y), float(theta))


def _stop_move(motion):
    try:
        motion.stopMove()
    except Exception:
        pass


def _safe_head_angles(motion):
    try:
        vals = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return float(vals[0]), float(vals[1])
    except Exception:
        return 0.0, 0.0


def _interp_yaw_pitch_limits(yaw, default_pitch_limits):
    table = getattr(config, "HEAD_YAW_PITCH_LIMITS", None)
    if not table:
        pitch_min = float(default_pitch_limits[0])
        pitch_max = float(default_pitch_limits[1])
    else:
        yaw_abs = abs(float(yaw))
        points = sorted(table, key=lambda x: x[0])
        if yaw_abs <= points[0][0]:
            pitch_min = points[0][1]
            pitch_max = points[0][2]
        elif yaw_abs >= points[-1][0]:
            pitch_min = points[-1][1]
            pitch_max = points[-1][2]
        else:
            pitch_min = points[0][1]
            pitch_max = points[0][2]
            for i in range(len(points) - 1):
                y0, pmin0, pmax0 = points[i]
                y1, pmin1, pmax1 = points[i + 1]
                if y0 <= yaw_abs <= y1:
                    t = 0.0 if y1 == y0 else (yaw_abs - y0) / (y1 - y0)
                    pitch_min = pmin0 + (pmin1 - pmin0) * t
                    pitch_max = pmax0 + (pmax1 - pmax0) * t
                    break

        pitch_min = max(float(default_pitch_limits[0]), float(pitch_min))
        pitch_max = min(float(default_pitch_limits[1]), float(pitch_max))

    track_pitch_min = getattr(config, "TRACK_PITCH_MIN", None)
    if track_pitch_min is not None:
        pitch_min = max(pitch_min, float(track_pitch_min))
    if pitch_min > pitch_max:
        pitch_min = pitch_max
    return (pitch_min, pitch_max)


def _build_scan_targets(yaw_limits, pitch_limits):
    scan_yaws = list(getattr(config, "SCAN_YAWS", []) or [])
    if not scan_yaws:
        return []

    scan_pitches = list(getattr(config, "SCAN_PITCHES", []) or [])
    if not scan_pitches:
        scan_pitches = [0.0]

    targets = []
    for yaw in scan_yaws:
        yaw_target = clamp(float(yaw), yaw_limits[0], yaw_limits[1])
        dyn_pitch_limits = _interp_yaw_pitch_limits(yaw_target, pitch_limits)
        for pitch in scan_pitches:
            pitch_target = clamp(float(pitch), dyn_pitch_limits[0], dyn_pitch_limits[1])
            targets.append((yaw_target, pitch_target))
    return targets


def _english_color_name(color_name):
    key = str(color_name).strip().lower()
    mapping = {
        "rot": "red",
        "red": "red",
        "gruen": "green",
        "green": "green",
        "blau": "blue",
        "blue": "blue",
    }
    return mapping.get(key, key)


def _announce(message, tts_proxy):
    print(message)
    if not getattr(config, "STATUS_SPEECH_ENABLED", True):
        return
    if tts_proxy is None:
        return
    try:
        tts_proxy.say(str(message))
    except Exception:
        pass


def run_head_tracker(nao, frame_callback=None, show_preview=False, save_local=True):
    """Search a color blob, approach until max down pitch, then push forward and stop."""
    motion = None
    posture = None
    tts = None
    video = None
    handle = None
    writer = None

    try:
        print("Connecting to NAO...")
        motion = ALProxy("ALMotion", nao.ip, nao.port)

        try:
            tts = ALProxy("ALTextToSpeech", nao.ip, nao.port)
        except Exception:
            tts = None

        print("Enabling motors...")
        motion.setStiffnesses("Head", 1.0)
        time.sleep(0.5)

        if config.LOCOMOTION_ENABLED:
            try:
                motion.setStiffnesses("Body", 1.0)
            except Exception:
                pass
            try:
                motion.wakeUp()
            except Exception:
                pass
            try:
                posture = ALProxy("ALRobotPosture", nao.ip, nao.port)
                posture.goToPosture(config.LOCOMOTION_INIT_POSTURE, config.LOCOMOTION_POSTURE_SPEED)
            except Exception:
                posture = None
            try:
                motion.moveInit()
            except Exception:
                pass

        video = ALProxy("ALVideoDevice", nao.ip, nao.port)
        handle = video.subscribeCamera(
            "head_turn_stream",
            config.VIDEO_CAMERA_ID,
            config.VIDEO_RESOLUTION,
            config.VIDEO_COLOR_SPACE,
            config.VIDEO_FPS,
        )
        print("Video stream subscribed ({} fps).".format(config.VIDEO_FPS))

        if show_preview and cv2 is None:
            print("OpenCV not found: preview disabled.")
            show_preview = False
        if save_local and cv2 is None:
            print("OpenCV not found: local recording disabled.")
            save_local = False

        output_path = None
        if save_local:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(
                output_dir,
                "head_track_{}.avi".format(time.strftime("%Y%m%d_%H%M%S")),
            )

        if cv2 is None:
            print("Warning: OpenCV missing, blob tracking inactive (scan only).")
        if np is None:
            print("Warning: NumPy missing, blob tracking inactive (scan only).")

        yaw_limits, pitch_limits = get_head_limits(motion)
        scan_targets = _build_scan_targets(yaw_limits, pitch_limits)
        scan_index = 0
        scan_dir = 1
        next_scan_ts = 0.0

        last_seen_ts = 0.0
        last_head_control_ts = 0.0
        last_move_control_ts = 0.0
        move_is_stopped = True
        mode = "search"  # search, approach
        color_name = _english_color_name(config.TRACK_COLOR)

        if scan_targets:
            motion.setAngles(["HeadYaw", "HeadPitch"], list(scan_targets[0]), config.SCAN_SPEED)

        _announce("Searching {} object.".format(color_name), tts)

        next_ts = time.time()
        printed_path = False

        while True:
            now = time.time()
            frame = None
            width = None
            height = None
            detection = None

            try:
                frame, width, height = grab_frame(video, handle)
            except Exception:
                frame, width, height = None, None, None

            if frame is not None and cv2 is not None and np is not None:
                detection = detect_blob(
                    frame,
                    config.TRACK_COLOR,
                    config.TRACK_MIN_AREA,
                    config.TRACK_MAX_AREA,
                )

            if detection is not None and width and height:
                last_seen_ts = now

                if mode != "approach":
                    mode = "approach"
                    _announce("{} object found!".format(color_name), tts)
                    _announce("Moving to destroy", tts)

                cx, cy = detection["center"]
                err_x = (float(cx) - (width / 2.0)) / (width / 2.0)
                err_y = (float(cy) - (height / 2.0)) / (height / 2.0)

                if config.TRACK_INVERT_YAW:
                    err_x = -err_x
                if config.TRACK_INVERT_PITCH:
                    err_y = -err_y

                if (now - last_head_control_ts) >= config.TRACK_CONTROL_INTERVAL_S:
                    head_err_x = 0.0 if abs(err_x) < config.TRACK_DEADBAND else err_x
                    head_err_y = 0.0 if abs(err_y) < config.TRACK_DEADBAND else err_y
                    delta_yaw = clamp(-head_err_x * config.TRACK_YAW_K, -config.TRACK_MAX_STEP, config.TRACK_MAX_STEP)
                    delta_pitch = clamp(head_err_y * config.TRACK_PITCH_K, -config.TRACK_MAX_STEP, config.TRACK_MAX_STEP)
                    current = motion.getAngles(["HeadYaw", "HeadPitch"], True)
                    target_yaw = clamp(current[0] + delta_yaw, yaw_limits[0], yaw_limits[1])
                    dyn_pitch_limits = _interp_yaw_pitch_limits(target_yaw, pitch_limits)
                    target_pitch = clamp(current[1] + delta_pitch, dyn_pitch_limits[0], dyn_pitch_limits[1])
                    motion.setAngles(["HeadYaw", "HeadPitch"], [target_yaw, target_pitch], config.TRACK_SPEED)
                    last_head_control_ts = now

                if config.LOCOMOTION_ENABLED and (now - last_move_control_ts) >= config.MOVE_CONTROL_INTERVAL_S:
                    head_yaw, _ = _safe_head_angles(motion)
                    theta = clamp(head_yaw * config.APPROACH_THETA_K, -config.APPROACH_MAX_THETA, config.APPROACH_MAX_THETA)
                    _move_toward(motion, config.APPROACH_FORWARD_X, 0.0, theta, config.MOVE_FREQUENCY)
                    move_is_stopped = False
                    last_move_control_ts = now

                current_yaw, current_pitch = _safe_head_angles(motion)
                dyn_pitch_limits = _interp_yaw_pitch_limits(current_yaw, pitch_limits)
                pitch_is_max_down = current_pitch >= (dyn_pitch_limits[1] - config.DESTROY_PITCH_MARGIN_RAD)
                yaw_is_forward = abs(current_yaw) <= config.DESTROY_YAW_TOLERANCE_RAD

                if pitch_is_max_down and yaw_is_forward:
                    if config.LOCOMOTION_ENABLED and not move_is_stopped:
                        _stop_move(motion)
                        move_is_stopped = True

                    if config.LOCOMOTION_ENABLED and config.DESTROY_EXTRA_FORWARD_M > 0.0:
                        try:
                            motion.moveTo(float(config.DESTROY_EXTRA_FORWARD_M), 0.0, 0.0)
                        except Exception:
                            pass

                    _announce("Target eleminated.", tts)
                    break

            else:
                if config.LOCOMOTION_ENABLED and not move_is_stopped:
                    _stop_move(motion)
                    move_is_stopped = True

                if mode == "approach" and (now - last_seen_ts) > config.TRACK_LOST_TIMEOUT_S:
                    mode = "search"
                    _announce("Searching {} object.".format(color_name), tts)

                if mode == "search" and now >= next_scan_ts and scan_targets:
                    yaw, pitch = scan_targets[scan_index]
                    motion.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], config.SCAN_SPEED)
                    next_scan_ts = now + config.SCAN_HOLD_S
                    scan_index += scan_dir
                    if scan_index >= len(scan_targets) or scan_index < 0:
                        scan_dir *= -1
                        scan_index += scan_dir

            if frame is not None:
                frame_out = frame
                if show_preview or save_local:
                    frame_out = frame.copy()
                    if cv2 is not None:
                        center = (int(width / 2), int(height / 2))
                        cv2.drawMarker(frame_out, center, (255, 255, 255), cv2.MARKER_CROSS, 12, 1)
                        if detection is not None:
                            x, y, w, h = detection["bbox"]
                            cv2.rectangle(frame_out, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cx, cy = detection["center"]
                            cv2.circle(frame_out, (cx, cy), 4, (0, 255, 0), -1)
                        cv2.putText(frame_out, "Mode: {}".format(mode), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                if save_local and writer is None and output_path is not None:
                    fourcc = fourcc_mjpg()
                    if fourcc is None:
                        writer = cv2.VideoWriter(output_path, 0, config.VIDEO_FPS, (width, height))
                    else:
                        writer = cv2.VideoWriter(output_path, fourcc, config.VIDEO_FPS, (width, height))
                    if hasattr(writer, "isOpened") and not writer.isOpened():
                        writer = None
                        print("Could not open local video:", output_path)
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
                print("Local video:", output_path)
                printed_path = False

            next_ts += 1.0 / float(config.VIDEO_FPS)
            sleep_s = next_ts - time.time()
            if sleep_s > 0:
                time.sleep(sleep_s)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print("ERROR: " + str(e))
        print("Please ensure:")
        print("  1. NAO is powered on")
        print("  2. IP address is correct: " + nao.ip)
        print("  3. Network connection is available")
    finally:
        try:
            _stop_move(motion)
        except Exception:
            pass

        try:
            if writer is not None:
                writer.release()
                print("Local video saved.")
            if video is not None and handle is not None:
                video.unsubscribe(handle)
                print("Video stream closed.")
            if show_preview and cv2 is not None:
                cv2.destroyAllWindows()
        except Exception:
            pass

        try:
            print("\nDisabling motors...")
            motion.setStiffnesses("Head", 0.0)
            print("Done.")
        except Exception:
            pass
