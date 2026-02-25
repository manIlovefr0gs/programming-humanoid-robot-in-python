# -*- coding: utf-8 -*-

from config.robot  import IP, PORT
from core.tracker  import BlobTracker


class _Nao:
    """Minimales Objekt mit Verbindungsdaten."""
    def __init__(self, ip, port):
        self.ip   = ip
        self.port = port


def main():
    nao = _Nao(IP, PORT)
    BlobTracker(nao).run()


if __name__ == "__main__":
    main()






