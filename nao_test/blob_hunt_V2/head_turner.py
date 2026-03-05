# -*- coding: utf-8 -*-
import os
import sys

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
    from .tracker import run_head_tracker
except (ImportError, ValueError):
    from tracker import run_head_tracker


def scan_area(nao, frame_callback=None, show_preview=False, save_local=True):
    return run_head_tracker(nao, frame_callback, show_preview, save_local)


if __name__ == "__main__":
    nao = InitNao()
    scan_area(nao)
