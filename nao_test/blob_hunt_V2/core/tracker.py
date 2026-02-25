# Zustandsmaschine: suchen → annähern (ALTracker) → zerstören
#
# Zustände:
#   search   – eigener Kopf-Scan; ALColorBlobDetection läuft im Hintergrund
#   approach – ALTracker "Move" übernimmt Kopf + Laufen bis zur Stopp-Distanz
#   done     – Stopp, Extra-Schub, Ende

import time

try:
    from naoqi import ALProxy
except ImportError:
    ALProxy = None

import config
from modules.color_blob  import subscribe as blob_subscribe, \
                                unsubscribe as blob_unsubscribe, \
                                is_detected, MEMORY_KEY
from modules.head        import clamp, get_head_limits, get_dynamic_pitch_limits
from modules.locomotion  import init_locomotion, move_to, stop_move
from modules.eye_color   import set_color as set_eye_color, reset as reset_eyes
from modules.stream      import subscribe as stream_subscribe, \
                                unsubscribe as stream_unsubscribe, \
                                update as stream_update, is_available as stream_available

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _announce(message, tts):
    print(message)
    if not config.STATUS_SPEECH_ENABLED or tts is None:
        return
    try:
        tts.say(str(message))
    except Exception:
        pass


def _color_english(name):
    mapping = {"rot": "red", "gruen": "green", "blau": "blue"}
    return mapping.get(name.strip().lower(), name.strip().lower())


def _build_scan_targets(yaw_limits, pitch_limits):
    """Gibt eine Liste von (yaw, pitch)-Paaren für die Scan-Bewegung zurück."""
    targets = []
    for yaw in config.SCAN_YAWS:
        yaw = clamp(yaw, *yaw_limits)
        dyn = get_dynamic_pitch_limits(yaw, pitch_limits)
        for pitch in config.SCAN_PITCHES:
            targets.append((yaw, clamp(pitch, *dyn)))
    return targets


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------

class BlobTracker:
    """Sucht einen Farb-Blob, lässt ALTracker annähern, stößt dann zu."""

    def __init__(self, nao):
        self.nao = nao

    def run(self):
        motion = tts = posture = leds = blob = tracker = memory = None
        color = _color_english(config.TRACK_COLOR)

        try:
            # ── Verbindung aufbauen ──────────────────────────────────────────
            print("Verbinde mit NAO ({})...".format(self.nao.ip))
            motion  = ALProxy("ALMotion",              self.nao.ip, self.nao.port)
            memory  = ALProxy("ALMemory",              self.nao.ip, self.nao.port)
            blob    = ALProxy("ALColorBlobDetection",  self.nao.ip, self.nao.port)
            tracker = ALProxy("ALTracker",             self.nao.ip, self.nao.port)
            try:
                tts    = ALProxy("ALTextToSpeech",  self.nao.ip, self.nao.port)
                leds   = ALProxy("ALLeds",          self.nao.ip, self.nao.port)
                posture = ALProxy("ALRobotPosture", self.nao.ip, self.nao.port)
            except Exception:
                pass

            # ── Initialisierung ──────────────────────────────────────────────
            motion.setStiffnesses("Head", 1.0)
            time.sleep(0.3)
            if config.LOCOMOTION_ENABLED:
                init_locomotion(motion, posture)

            # Videostream für Live-Anzeige
            stream_video = stream_handle = None
            if stream_available():
                try:
                    stream_video  = ALProxy("ALVideoDevice", self.nao.ip, self.nao.port)
                    stream_handle = stream_subscribe(stream_video)
                    print("Stream-Viewer aktiv (q zum Beenden).")
                except Exception as e:
                    print("Stream-Viewer nicht verfügbar: {}".format(e))

            # ALColorBlobDetection starten (läuft ab jetzt im Hintergrund)
            blob_subscribe(blob, config.TRACK_COLOR)
            print("ALColorBlobDetection aktiv für Farbe '{}'.".format(color))

            # Augen auf Suchfarbe setzen
            set_eye_color(leds, config.TRACK_COLOR)

            # Scan-Positionen berechnen
            yaw_limits, pitch_limits = get_head_limits(motion)
            scan_targets = _build_scan_targets(yaw_limits, pitch_limits)
            scan_idx, scan_dir = 0, 1
            next_scan_ts = 0.0

            mode          = "search"
            last_seen_ts  = 0.0

            if scan_targets:
                motion.setAngles(["HeadYaw", "HeadPitch"],
                                 list(scan_targets[0]), config.SCAN_SPEED)
            _announce("Suche {} Objekt.".format(color), tts)

            # ── Hauptschleife ────────────────────────────────────────────────
            while True:
                now = time.time()

                if mode == "search":
                    # ── Kopf-Scan ────────────────────────────────────────────
                    if now >= next_scan_ts and scan_targets:
                        yaw, pitch = scan_targets[scan_idx]
                        motion.setAngles(["HeadYaw", "HeadPitch"],
                                         [yaw, pitch], config.SCAN_SPEED)
                        next_scan_ts = now + config.SCAN_HOLD_S
                        scan_idx    += scan_dir
                        if not (0 <= scan_idx < len(scan_targets)):
                            scan_dir *= -1
                            scan_idx += scan_dir

                    # ALColorBlobDetection hat etwas in ALMemory geschrieben?
                    if is_detected(memory):
                        mode = "approach"
                        last_seen_ts = now
                        _announce("{} Objekt gefunden! Nähere mich.".format(color), tts)

                        # ALTracker übernimmt: Kopf + Laufen
                        # setRelativePosition: [x, y, z, tolX, tolY, tolTheta]
                        # → stopp APPROACH_STOP_DISTANCE_M vor dem Ziel
                        tol = config.APPROACH_STOP_TOLERANCE_M
                        tracker.setMode("Move")
                        tracker.setRelativePosition([
                            -config.APPROACH_STOP_DISTANCE_M,
                            0.0, 0.0, tol, tol, 0.3
                        ])
                        tracker.trackEvent(MEMORY_KEY)
                        print("ALTracker gestartet (Mode: Move).")

                elif mode == "approach":
                    # ── ALTracker läuft – wir überwachen nur ─────────────────
                    if is_detected(memory):
                        last_seen_ts = now

                    # Ziel verloren?
                    if (now - last_seen_ts) > config.TRACK_LOST_TIMEOUT_S:
                        print("Ziel verloren – zurück zur Suche.")
                        tracker.stopTracker()
                        stop_move(motion)
                        mode = "search"
                        _announce("Suche {} Objekt.".format(color), tts)
                        continue

                    # ALTracker hat Zieldistanz erreicht und sich selbst gestoppt?
                    if not tracker.isActive():
                        mode = "done"

                elif mode == "done":
                    # ── ALTracker stoppen, finalen Stoß ausführen ────────────
                    tracker.stopTracker()
                    stop_move(motion)

                    if config.LOCOMOTION_ENABLED and config.DESTROY_EXTRA_FORWARD_M > 0:
                        _announce("Stoße zu!", tts)
                        move_to(motion, config.DESTROY_EXTRA_FORWARD_M)

                    _announce("Ziel eliminiert.", tts)
                    reset_eyes(leds)
                    break

                # Stream-Frame anzeigen
                if stream_video is not None and stream_handle is not None:
                    stream_update(stream_video, stream_handle,
                                  blob, motion, tracker, mode)

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nDurch Benutzer unterbrochen.")
        except Exception as e:
            print("FEHLER: {}".format(e))
            print("Bitte prüfen: NAO eingeschaltet, IP '{}', Netzwerkverbindung.".format(
                self.nao.ip))
        finally:
            self._cleanup(motion, blob, tracker, leds, stream_video, stream_handle)

    def _cleanup(self, motion, blob, tracker, leds,
                 stream_video=None, stream_handle=None):
        try:
            if tracker:
                tracker.stopTracker()
        except Exception:
            pass
        try:
            stop_move(motion)
        except Exception:
            pass
        try:
            stream_unsubscribe(stream_video, stream_handle)
        except Exception:
            pass
        try:
            blob_unsubscribe(blob)
            print("ALColorBlobDetection gestoppt.")
        except Exception:
            pass
        try:
            reset_eyes(leds)
        except Exception:
            pass
        try:
            motion.setStiffnesses("Head", 0.0)
            print("Motoren deaktiviert.")
        except Exception:
            pass