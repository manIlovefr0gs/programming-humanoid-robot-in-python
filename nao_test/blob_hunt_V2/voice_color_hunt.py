# -*- coding: utf-8 -*-
import os
import re
import sys

from naoqi import ALProxy

try:
    # When run as part of a package
    from ..nao_config import InitNao
except (ImportError, ValueError):
    # When run directly as a script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from nao_config import InitNao

try:
    from . import config
    from .tracker import run_head_tracker
    from .change_eyecolor import set_color
except (ImportError, ValueError):
    import config
    from tracker import run_head_tracker
    from change_eyecolor import set_color




def _import_speech_client():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    voice_dir = os.path.join(repo_root, "voice_recog")
    if voice_dir not in sys.path:
        sys.path.insert(0, voice_dir)
    from speech_client import SpeechRecognizerClient
    return SpeechRecognizerClient


def _extract_color(text):
    aliases = {
        "red": "red",
        "read":"red",
        "rot": "red",
        "green": "green",
        "gruen": "green",
        "yellow": "yellow",
        "gelb": "yellow",
    }
    if not text:
        return None

    lowered = str(text).strip().lower()
    tokens = re.findall(r"[a-zA-Z]+", lowered)
    for token in tokens:
        if token in aliases:
            return aliases[token]
    return None


def _raw_input(prompt):
    try:
        return raw_input(prompt)
    except NameError:
        return input(prompt)


def run_voice_color_hunt():
    SpeechRecognizerClient = _import_speech_client()

    client = SpeechRecognizerClient()
    if not client.connect():
        print("Could not connect to Vosk server at 127.0.0.1:65432")
        print("Start it first with: python3 voice_recog/vosk_server.py")
        return 1

    nao = InitNao()
    try:
        leds = ALProxy("ALLeds", nao.ip, nao.port)
    except Exception:
        leds = None

    print("Voice mode ready.")
    print("Say one of: red, green, yellow")

    try:
        while True:
            cmd = _raw_input("\nPress Enter to listen (or q + Enter to quit): ").strip().lower()
            if cmd == "q":
                return 0

            print("Listening... speak your target color now.")
            client.start_listening()
            _raw_input("Press Enter to stop listening.")
            text = client.stop_listening().strip()
            print("Heard: {}".format(text))

            color = _extract_color(text)
            if color is None:
                print("No supported color found in speech input. Try again.")
                continue

            print("Selected color: {}".format(color))
            config.TRACK_COLOR = color
            set_color(leds, color)
            run_head_tracker(nao)
            return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(run_voice_color_hunt())
