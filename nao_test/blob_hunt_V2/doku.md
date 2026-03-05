# Blob Hunt V2 - Doku

## 1) Zielverhalten

Der Roboter soll ein Boden-Objekt "umrennen":
1. Objekt suchen (`search`)
2. Objekt mit Kopf in Yaw + Pitch zentrieren und gleichzeitig vorwaerts laufen (`approach`)
3. Wenn der Blob den unteren Sichtfeldrand beruehrt:
   - Objekt ist direkt vor dem Roboter
4. Dann noch `DESTROY_EXTRA_FORWARD_M` weiterlaufen (default `0.20 m`) und stoppen

## 2) Statusmeldungen (Englisch)

Bei Zustandswechseln:
- `Searching <color> object.`
- `<color> object found!`
- `Moving to destroy`
- `Target eleminated.`

Hinweis:
- Meldungen gehen immer auf die Konsole.
- Wenn `STATUS_SPEECH_ENABLED = True`, spricht NAO diese Texte zusaetzlich ueber `ALTextToSpeech`.

## 3) Pitch-/Yaw-Konvention und Limits

- Pitch:
  - negativ = hoch
  - positiv = runter
- Projektregel:
  - `TRACK_PITCH_MIN = 0.0` -> nie ueber Horizont hochschauen
- Mechanische Limits:
  - `HEAD_YAW_PITCH_LIMITS` begrenzt Pitch in Abhaengigkeit von |Yaw|
  - diese Grenzen werden bei Scan und Tracking angewandt

## 4) Such- und Trackinglogik

### Search
- Scan ueber `SCAN_YAWS`
- Pro Yaw zwei Pitch-Ebenen (`SCAN_PITCHES`):
  - fast geradeaus
  - nach unten fuer nahen Bodenbereich

### Approach
- Blob-Fehler in Bildmitte:
  - X-Fehler steuert HeadYaw
  - Y-Fehler steuert HeadPitch
- Waehrend des Trackings laeuft der Roboter vorwaerts:
  - Vortrieb: `APPROACH_FORWARD_X`
  - Drehkorrektur: aus aktuellem HeadYaw (`APPROACH_THETA_K`, `APPROACH_MAX_THETA`)

### Destroy trigger
- Trigger, wenn die Unterkante der Blob-Bounding-Box den unteren Bildrand erreicht:
  - `blob_bottom >= image_bottom - DESTROY_BOTTOM_MARGIN_PX`
- Danach:
  - `moveTo(DESTROY_EXTRA_FORWARD_M, DESTROY_EXTRA_LATERAL_M, 0)`
  - Stopp

## 5) Wichtige Dateien

- `head_turner.py`: Einstiegspunkt
- `tracker.py`: komplette Lauflogik
- `config.py`: reduzierte Konfiguration mit Tuning-Hinweisen
- `vision.py`: HSV Blob-Erkennung
- `walk_forward_test.py`: reiner Geh-Test

## 6) Start

```bash
python2 nao_test/blob_hunt_V2/head_turner.py
```
