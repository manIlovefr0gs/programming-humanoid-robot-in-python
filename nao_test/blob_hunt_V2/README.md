# Blob Hunt V2

Simple NAO blob hunter:
- reads camera stream
- detects a color blob (HSV)
- centers with head yaw + pitch
- approaches until head pitch is max-down
- pushes forward a configurable extra distance, then stops

## Runtime status calls (English)

The robot announces state changes with console output and optional TTS:
- `Searching <color> object.`
- `<color> object found!`
- `Moving to destroy`
- `Target eleminated.`

## Pitch convention

- negative pitch = looking up
- positive pitch = looking down
- tracking uses `TRACK_PITCH_MIN = 0.0`, so it will not look above horizon

## Search behavior

- Yaw scan positions: `SCAN_YAWS`
- Two pitch passes per yaw: `SCAN_PITCHES`
  - near horizon (`~0 rad`)
  - close-floor pass (`0.200015 rad`, 11.46 deg)

## Start

```bash
python2 nao_test/blob_hunt_V2/head_turner.py
```

## Main files

- `head_turner.py`: entrypoint
- `tracker.py`: search/track/approach/destroy logic
- `vision.py`: frame decode + blob detection
- `config.py`: all tuning params
- `walk_forward_test.py`: isolated walk test (without vision)

## Most useful tuning

- Detection:
  - `TRACK_COLOR`, `TRACK_MIN_AREA`
- Head tracking:
  - `TRACK_YAW_K`, `TRACK_PITCH_K`, `TRACK_DEADBAND`
- Destroy trigger:
  - `DESTROY_PITCH_MARGIN_RAD`, `DESTROY_YAW_TOLERANCE_RAD`
- Final hit distance:
  - `DESTROY_EXTRA_FORWARD_M`
