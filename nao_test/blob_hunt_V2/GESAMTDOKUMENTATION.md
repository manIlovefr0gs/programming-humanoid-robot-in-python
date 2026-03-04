# Blob Hunt V2 + Vosk Server - Vollstaendige Funktionsdokumentation

Stand: 2026-03-04

## 1. Ziel des Systems

Das System laesst einen NAO-Roboter ein farbiges Objekt auf dem Boden finden, darauf zulaufen und es gezielt "umrennen" (Destroy-Phase).  
Optional kann die Zielfarbe per Sprache ausgewaehlt werden (offline, lokal ueber Vosk).

Es gibt zwei Betriebsarten:

1. Direktbetrieb ohne Sprache:
   - Startscript: `nao_test/blob_hunt_V2/head_turner.py`
2. Sprachbetrieb mit Vosk:
   - Server: `voice_recog/vosk_server.py` (Python 3)
   - Robot-App: `nao_test/blob_hunt_V2/voice_color_hunt.py` (Python 2)

## 2. Gesamtarchitektur

### 2.1 Komponenten

1. NAO-Laufzeit (Python 2.7 + NAOqi Proxies)
   - Bewegung, Kopfsteuerung, Kamera, LEDs, TTS.
2. Bildverarbeitung (`vision.py`)
   - BGR-Frame vom NAO lesen, HSV-Maske bilden, groessten gueltigen Blob finden.
3. Verhaltenslogik (`tracker.py`)
   - Zustandsmaschine: Suchen -> Annaehern -> Destroy -> Ende.
4. Konfiguration (`config.py`)
   - Alle Tuning-Werte (Scan, Tracking, Bewegung, Trigger, Video).
5. Sprachserver (`voice_recog/vosk_server.py`, Python 3)
   - Mikrofon aufnehmen, offline transkribieren, Text via TCP liefern.
6. Speech-Client (`voice_recog/speech_client.py`, Python 2/3-kompatibel)
   - Einfache Socket-Kommandos `START`/`STOP`.

### 2.2 Datenfluss

1. Kamera-Frames kommen von `ALVideoDevice`.
2. `vision.detect_blob()` liefert pro Frame entweder `None` oder Blob-Daten (`center`, `area`, `bbox`, `mask`).
3. `tracker.run_head_tracker()` berechnet Bildfehler (x/y), steuert Kopfwinkel und Gehkommandos.
4. Bei unterem Bildrandkontakt wird Finalschub `moveTo(...)` ausgefuehrt und gestoppt.
5. Optional: `voice_color_hunt.py` setzt vorher `config.TRACK_COLOR` aus Sprachtext.

## 3. Voraussetzungen und Laufzeitkontext

### 3.1 Python-Versionen

1. `blob_hunt_V2`: auf Python 2.7/NAOqi ausgelegt.
2. `vosk_server.py`: Python 3.

### 3.2 Externe Abhaengigkeiten

Auf Robot-App-Seite:
1. `naoqi` (ALProxy)
2. `numpy` (Frame-Dekodierung)
3. `opencv-python`/`cv2` (HSV/Contours/Videoaufnahme)

Auf Sprachserver-Seite:
1. `vosk`
2. `pyaudio`
3. lokales Vosk-Modell unter `voice_recog/model`

### 3.3 Netzwerk/Kommunikation

1. Robot-App verbindet sich zum NAO ueber IP/Port aus `nao_test/nao_config.py`:
   - IP: `192.168.1.118`
   - Port: `9559`
2. Sprachclient verbindet lokal per TCP:
   - Host: `127.0.0.1`
   - Port: `65432`

## 4. Datei-fuer-Datei-Erklaerung

### 4.1 `nao_test/blob_hunt_V2/head_turner.py`

Rolle:
1. Einfachster Einstiegspunkt fuer den reinen Blob-Hunt.

Ablauf:
1. Importiert `InitNao` (NAO-Verbindungskonfiguration).
2. Importiert `run_head_tracker` aus `tracker.py`.
3. `scan_area(...)` ruft direkt `run_head_tracker(...)` auf.
4. Bei direktem Script-Start wird `InitNao()` erzeugt und Tracking gestartet.

### 4.2 `nao_test/blob_hunt_V2/tracker.py`

Rolle:
1. Kernlogik des Robotverhaltens.
2. Implementiert Suche, Tracking, Fahrsteuerung, Destroy-Trigger und Cleanup.

Wichtige interne Hilfsfunktionen:
1. `_move_toward(...)`:
   - Kapselt `ALMotion.moveToward` mit optionaler Frequenz.
2. `_stop_move(...)`:
   - Sicheres Stoppen mit Fehlerabfangung.
3. `_safe_head_angles(...)`:
   - Liest aktuelle HeadYaw/HeadPitch oder faellt auf `(0,0)` zurueck.
4. `_interp_yaw_pitch_limits(...)`:
   - Interpoliert pitch-Limits in Abhaengigkeit vom absoluten Yaw.
   - Zusaetzlich wird `TRACK_PITCH_MIN` erzwungen.
5. `_build_scan_targets(...)`:
   - Baut Liste von Scan-Zielen aus `SCAN_YAWS` x `SCAN_PITCHES`.
6. `_english_color_name(...)`:
   - Normalisiert Deutsch/Englisch (`rot` -> `red`).
7. `_announce(...)`:
   - Gibt Status auf Konsole aus und optional per `ALTextToSpeech`.

Hauptfunktion `run_head_tracker(nao, frame_callback=None, show_preview=False, save_local=True)`:

Initialisierung:
1. Verbindet zu `ALMotion`, optional `ALTextToSpeech`.
2. Aktiviert Kopfstiffness, bei aktivierter Lokomotion zusaetzlich Body + `wakeUp()`.
3. Optionales Posture-Setzen auf `LOCOMOTION_INIT_POSTURE` (Default: `StandInit`).
4. Initialisiert Video-Stream via `ALVideoDevice.subscribeCamera(...)`.
5. Optional:
   - Previewfenster (wenn `show_preview=True` und OpenCV verfuegbar)
   - Lokale AVI-Aufzeichnung unter `nao_test/blob_hunt_V2/recordings/`.

Laufende Zustandslogik:
1. Startzustand: `mode = "search"`.
2. Pro Schleife:
   - Frame holen (`grab_frame`).
   - Blob suchen (`detect_blob`).
3. Wenn Blob erkannt:
   - Zustand -> `approach` (falls vorher `search`).
   - Statusmeldungen:
     - `"<color> object found!"`
     - `"Moving to destroy"`
   - Normierte Bildfehler:
     - `err_x = (cx - width/2) / (width/2)`
     - `err_y = (cy - height/2) / (height/2)`
   - Kopfregelung (zeitdiskret, Intervall `TRACK_CONTROL_INTERVAL_S`):
     - Yaw-Korrektur proportional zu `err_x` mit Deadband.
     - Pitch-Korrektur proportional zu `err_y` mit Deadband.
     - Schrittweite begrenzt durch `TRACK_MAX_STEP`.
     - Zielpitch wird dynamisch gegen Yaw-abhaengige Limits geklemmt.
   - Gehregelung (Intervall `MOVE_CONTROL_INTERVAL_S`):
     - Vorwaerts `APPROACH_FORWARD_X`.
     - Drehung `theta` aus aktuellem HeadYaw (`APPROACH_THETA_K`, `APPROACH_MAX_THETA`).
4. Destroy-Trigger:
   - Bounding-Box-Unterkante `blob_bottom = y + h`.
   - Kontaktbedingung:
     - `blob_bottom >= image_bottom - DESTROY_BOTTOM_MARGIN_PX`.
   - Danach:
     - Bewegung stoppen (`stopMove`),
     - finaler Schub `moveTo(DESTROY_EXTRA_FORWARD_M, DESTROY_EXTRA_LATERAL_M, 0)`,
     - Status `"Target eleminated."` (Schreibweise im Code genau so),
     - optional `Sit`,
     - Ende der Hauptschleife.
5. Wenn kein Blob erkannt:
   - Laufbewegung stoppen.
   - Falls vorher im `approach` und Timeout `TRACK_LOST_TIMEOUT_S` ueberschritten:
     - zurueck in `search`, Statusmeldung erneut.
   - Im `search`-Modus:
     - Scanpositionen nacheinander abfahren (`SCAN_HOLD_S` Pause),
     - an den Enden Richtung umkehren (Ping-Pong-Scan).

Cleanup (`finally`):
1. Stoppt Bewegung.
2. Schreibt Video-Datei sauber zu Ende.
3. Unsubscribed Kamera.
4. Schliesst Preview-Fenster.
5. Setzt Kopfstiffness auf 0.

### 4.3 `nao_test/blob_hunt_V2/vision.py`

Rolle:
1. Bildbezug und Blob-Erkennung.

Funktionen:
1. `ensure_numpy()`:
   - Erzwingt NumPy-Verfuegbarkeit fuer Stream-Dekodierung.
2. `fourcc_mjpg()`:
   - Liefert MJPG-FourCC fuer VideoWriter (kompatibel alt/neu OpenCV APIs).
3. `color_ranges(color_name)`:
   - Holt HSV-Bereiche aus `config.HSV_COLOR_PRESETS`.
4. `grab_frame(video, handle)`:
   - Holt `getImageRemote(...)`,
   - dekodiert Bytebuffer -> `height x width x 3` ndarray,
   - versucht `releaseImage(handle)`.
5. `detect_blob(frame, color_name, min_area, max_area, kernel_size=None)`:
   - BGR -> HSV,
   - erstellt Gesamtmaske aus 1..n HSV-Bereichen (rot hat 2 Hue-Bereiche),
   - Morphologie:
     - `erode(1x)`,
     - `dilate(2x)`,
   - findet externe Konturen,
   - waehlt groesste Kontur innerhalb Flaechenlimits,
   - berechnet Schwerpunkt und Bounding-Box,
   - Rueckgabe-Dictionary mit Geometriedaten.

### 4.4 `nao_test/blob_hunt_V2/head_control.py`

Rolle:
1. Kleine Utilities fuer Grenzwerte.

Funktionen:
1. `clamp(value, lower, upper)`: harte Begrenzung.
2. `get_head_limits(motion)`:
   - Liest NAO-Limits per `getLimits(...)`.
   - Fallbackwerte, falls Proxy-Lesen fehlschlaegt.

### 4.5 `nao_test/blob_hunt_V2/config.py`

Rolle:
1. Zentrale Parametrisierung ohne Codeaenderung in der Logik.

Parametergruppen:
1. Search Pattern:
   - `SCAN_YAWS`, `SCAN_PITCHES`, `SCAN_SPEED`, `SCAN_HOLD_S`
2. Blob Tracking:
   - `TRACK_COLOR`, `TRACK_MIN_AREA`, `TRACK_MAX_AREA`
   - `TRACK_DEADBAND`, `TRACK_YAW_K`, `TRACK_PITCH_K`
   - `TRACK_MAX_STEP`, `TRACK_SPEED`
   - `TRACK_CONTROL_INTERVAL_S`, `TRACK_LOST_TIMEOUT_S`
   - `TRACK_INVERT_YAW`, `TRACK_INVERT_PITCH`, `TRACK_PITCH_MIN`
3. Mechanische Kopfgrenzen:
   - `HEAD_YAW_PITCH_LIMITS` (Stuetzstellen fuer Interpolation)
4. Destroy-Verhalten:
   - `DESTROY_BOTTOM_MARGIN_PX`
   - `DESTROY_EXTRA_FORWARD_M`
   - `DESTROY_EXTRA_LATERAL_M`
5. Lokomotion:
   - `LOCOMOTION_ENABLED`
   - `LOCOMOTION_INIT_POSTURE`, `LOCOMOTION_POSTURE_SPEED`
   - `APPROACH_FORWARD_X`, `APPROACH_THETA_K`, `APPROACH_MAX_THETA`
   - `MOVE_FREQUENCY`, `MOVE_CONTROL_INTERVAL_S`
6. Vision:
   - `MASK_KERNEL_SIZE`
7. Status:
   - `STATUS_SPEECH_ENABLED`
8. Video:
   - `VIDEO_FPS`, `VIDEO_RESOLUTION`, `VIDEO_CAMERA_ID`, `VIDEO_COLOR_SPACE`
9. Farbpresets:
   - `HSV_COLOR_PRESETS` mit Synonymen Deutsch/Englisch.

### 4.6 `nao_test/blob_hunt_V2/voice_color_hunt.py`

Rolle:
1. Sprachgesteuerte Zielfarbwahl vor Start des Blob-Hunts.

Details:
1. Importiert `SpeechRecognizerClient` dynamisch aus `voice_recog/speech_client.py`.
2. Baut TCP-Verbindung zu lokalem Vosk-Server auf.
3. Interaktive Schleife:
   - Enter -> `START`
   - Sprechen
   - Enter -> `STOP`
4. `_extract_color(text)`:
   - extrahiert Farbwort aus Text (Alias-Mapping, inkl. `"read"` -> `"red"`).
5. Bei gueltiger Farbe:
   - setzt `config.TRACK_COLOR`,
   - setzt Augenfarbe via `ALLeds` (`set_color`),
   - startet `run_head_tracker(nao)`.

### 4.7 `nao_test/blob_hunt_V2/change_eyecolor.py`

Rolle:
1. Bedienung der Gesichts-LEDs.

Details:
1. Farbmapping `COLORS` (red/green/yellow/blue/white/off + deutsche Aliase).
2. `set_color(leds, color_name, duration=0.2)`:
   - `ALLeds.fadeRGB("FaceLeds", rgb, duration)`.
3. `reset(...)`:
   - setzt auf weiss.

### 4.8 `nao_test/blob_hunt_V2/walk_forward_test.py`

Rolle:
1. Isolierter Geh-Test ohne Kamera/Blob.

Ablauf:
1. WakeUp + `StandInit` + `moveInit`.
2. `moveTo(0.08, 0, 0)` als Sanity-Check.
3. `moveToward(...)` mit Ramp-up (1.5 s) und konservativer Schrittkonfiguration.
4. Regelmaessige Velocity-Logs.
5. Stoppen und Endpose ausgeben.

Zweck:
1. Verifizieren, ob Gehparameter stabil sind, bevor Vision-Loop genutzt wird.

### 4.9 `voice_recog/vosk_server.py`

Rolle:
1. Lokaler Offline-Spracherkennungsdienst fuer die Python-2-Robot-App.

Initialisierung:
1. Konfiguration:
   - Host `127.0.0.1`, Port `65432`
   - Modellpfad `model`
   - Sample Rate `16000`, Chunk `4000`
2. Laedt beim Start das Modell in den Speicher (`Model(MODEL_PATH)`).
3. Erstellt globalen `KaldiRecognizer`.

Klasse `VoskServer`:
1. `_init_stream()`:
   - oeffnet einmalig PyAudio-Inputstream.
2. `_record_loop()`:
   - laeuft in Hintergrund-Thread,
   - liest Audiochunks,
   - fuettert `AcceptWaveform`.
3. `start()`:
   - initialisiert Stream,
   - setzt Recording-Flag,
   - startet Thread.
4. `stop()`:
   - setzt Recording-Flag auf False,
   - wartet per `join()` auf Thread-Ende,
   - holt Finalresultat (`FinalResult()`),
   - fuehrt `Reset()` aus,
   - gibt erkannten Text zurueck.

Socket-Server `run_server()`:
1. TCP-Server mit `SO_REUSEADDR`, `listen(1)`.
2. Pro Client werden Textbefehle verarbeitet:
   - `START` -> Aufnahme starten, Antwort `ACK_START`
   - `STOP` -> Aufnahme stoppen, erkannter Text zurueck
3. Nach Disconnect wartet Server auf naechsten Client.

Wichtiger Hinweis:
1. Der Code nutzt ein globales `rec` und einen Engine-Instanzzustand.
2. Design ist auf sequentielle Ein-Client-Nutzung ausgelegt.

### 4.10 `voice_recog/speech_client.py` (fuer Vollverstaendnis relevant)

Rolle:
1. Leichte Bruecke fuer Python-2-App zum Python-3-Sprachserver.

Protokoll:
1. `connect()` baut TCP-Verbindung.
2. `start_listening()` sendet `START`, wartet auf ACK.
3. `stop_listening()` sendet `STOP`, liest Ruecktext.
4. `close()` schliesst Socket.

## 5. Detaillierte Zustandsmaschine des Blob-Hunts

1. `BOOT`:
   - Proxies, Stiffness, Posture, Video abonnieren.
2. `SEARCH`:
   - Kopf scannt in diskreten Zielpunkten (`SCAN_YAWS` x `SCAN_PITCHES`).
3. `APPROACH`:
   - erkannter Blob wird mit Kopf nachgefuehrt,
   - Roboter laeuft vorwaerts und richtet sich mit Theta nach HeadYaw aus.
4. `DESTROY_TRIGGER`:
   - Blob beruehrt unteren Bildrand.
5. `DESTROY_PUSH`:
   - optionaler finaler Vorwaertsschub.
6. `FINISH`:
   - Statusmeldung, optional Sit, Cleanup.
7. `RECOVERY`:
   - wenn Blob weg und Timeout ueberschritten: `APPROACH -> SEARCH`.

## 6. Regler- und Geometrieprinzipien

1. Bildkoordinaten:
   - Zentrum `(width/2, height/2)` ist Sollwert.
2. Fehlernormierung:
   - Werte etwa im Bereich `[-1, 1]`.
3. Kopfregelung:
   - Proportionale Korrektur mit `Kp`-aehnlichen Parametern (`TRACK_YAW_K`, `TRACK_PITCH_K`).
   - Deadband vermeidet Zittern nahe Soll.
   - Step Clamp begrenzt Einzelschritte.
4. Fahrregelung:
   - x-Komponente konstant.
   - theta proportional zu aktuellem Kopf-Yaw (indirekte Zielrichtung).
5. Bottom-Trigger:
   - Heuristik: Wenn Blob unten im Bild anliegt, ist Ziel sehr nah.

## 7. Konfigurationsleitfaden (praxisnah)

1. Wenn er zu spaet "rammt":
   - `DESTROY_BOTTOM_MARGIN_PX` erhoehen.
2. Wenn er zu frueh stoppt:
   - `DESTROY_BOTTOM_MARGIN_PX` reduzieren.
3. Wenn Tracking pendelt:
   - `TRACK_YAW_K`/`TRACK_PITCH_K` reduzieren,
   - `TRACK_DEADBAND` leicht erhoehen.
4. Wenn Tracking zu traege:
   - `TRACK_YAW_K`/`TRACK_PITCH_K` erhoehen,
   - `TRACK_CONTROL_INTERVAL_S` senken.
5. Wenn Objekt oft "verloren" wird:
   - `TRACK_LOST_TIMEOUT_S` erhoehen,
   - `TRACK_MIN_AREA` passend einstellen.
6. Wenn Ziel seitlich verfehlt wird:
   - `APPROACH_THETA_K` erhoehen (vorsichtig),
   - `DESTROY_EXTRA_LATERAL_M` feintrimmen.
7. Wenn viele Falschdetektionen:
   - `TRACK_MIN_AREA` erhoehen,
   - HSV-Bereich enger setzen,
   - `MASK_KERNEL_SIZE` erhoehen.

## 8. Sprachmodus End-to-End

Startreihenfolge:
1. Terminal A:
   - `cd voice_recog`
   - `python3 vosk_server.py`
2. Terminal B:
   - `python2 nao_test/blob_hunt_V2/voice_color_hunt.py`

Interaktion:
1. Enter -> Server startet Aufnahme.
2. Nutzer spricht Farbe.
3. Enter -> Server stoppt und sendet Text.
4. Farbe wird extrahiert, Augenfarbe gesetzt, Blob-Hunt startet.

Unterstuetzte Farbwoerter:
1. red, green, yellow
2. rot, gruen, gelb
3. zusaetzlich `"read"` als Alias fuer red

## 9. Logging, Statusmeldungen und Artefakte

Konsole (Tracker):
1. `Searching <color> object.`
2. `<color> object found!`
3. `Moving to destroy`
4. `Target eleminated.`

Optional Sprache:
1. gleiche Meldungen ueber `ALTextToSpeech`, wenn `STATUS_SPEECH_ENABLED=True`.

Video-Artefakte:
1. Bei `save_local=True` wird AVI gespeichert in:
   - `nao_test/blob_hunt_V2/recordings/`
2. Im Overlay:
   - Bildzentrum, Blob-Box, Modus.

## 10. Fehlerbilder und Ursachen

1. Keine Blob-Erkennung:
   - OpenCV/NumPy fehlen,
   - falscher HSV-Bereich,
   - Objektflaeche unter `TRACK_MIN_AREA`,
   - falsche Kamera/Belichtung.
2. Robot bewegt sich nicht:
   - `LOCOMOTION_ENABLED=False`,
   - `moveInit`/Posture fehlgeschlagen,
   - Stiffness/WakeUp nicht aktiv.
3. Sprachmodus verbindet nicht:
   - Vosk-Server laeuft nicht,
   - falscher Host/Port,
   - Mikrofon/Audio-Permissions problematisch.
4. Server startet nicht:
   - Modellpfad `voice_recog/model` fehlt,
   - `pyaudio`/`vosk` nicht installiert.

## 11. Sicherheits- und Robustheitsaspekte

1. Bewegungsabbruch:
   - Bei nicht mehr sichtbarem Blob wird laufende Bewegung gestoppt.
2. Cleanup:
   - In `finally` werden Bewegung/Video/Kamera sauber beendet.
3. Kopfgrenzen:
   - Doppelte Absicherung ueber NAO-Limits und yaw-abhaengige Pitch-Limits.
4. Risiko:
   - Endstoss `moveTo` ist offen-loop.
   - Auf freies Umfeld achten und ausreichenden Sicherheitsabstand halten.

## 12. Bekannte Grenzen des aktuellen Designs

1. Nur 2D-Farbheuristik, keine Tiefenschaetzung.
2. Destroy-Trigger basiert nur auf Bildrandkontakt.
3. Keine Mehrziel-Strategie, immer groesster Blob.
4. Sprachserver ist nicht fuer parallele Clients ausgelegt.
5. Typische Schreibfehler bleiben unveraendert im Statustext (`eleminated`).

## 13. Typische Fragen und kurze Antworten (FAQ-Basis)

1. Warum zwei Python-Versionen?
   - NAO-App ist Python 2/NAOqi-nah, Vosk laeuft stabil unter Python 3.
2. Wie waehlt das System den Blob?
   - Groesste Kontur innerhalb Flaechenlimits im definierten HSV-Bereich.
3. Wann startet Vorwaertsbewegung?
   - Sobald mindestens ein gueltiger Blob erkannt wird (`approach`).
4. Warum stoppt er bei Blob-Verlust sofort?
   - Sicherheits-/Stabilitaetsprinzip, dann Rueckfall auf Suche.
5. Wie wird die Richtung beim Laufen korrigiert?
   - Ueber Theta aus aktuellem HeadYaw.
6. Wie kann ich auf eine neue Farbe erweitern?
   - HSV-Preset in `config.HSV_COLOR_PRESETS` ergaenzen und Alias im Sprachparser ergaenzen.
7. Wo aendere ich die NAO-IP?
   - In `nao_test/nao_config.py` (`InitNao.IP`).

## 14. Schnellstart (kompakt)

Ohne Sprache:
1. `python2 nao_test/blob_hunt_V2/head_turner.py`

Mit Sprache:
1. `cd voice_recog && python3 vosk_server.py`
2. `python2 nao_test/blob_hunt_V2/voice_color_hunt.py`

Test nur Gehen:
1. `python2 nao_test/blob_hunt_V2/walk_forward_test.py`

