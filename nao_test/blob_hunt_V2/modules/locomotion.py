# Bewegungs-Helfer: Initialisierung, Extra-Vorwärtsschub, Stopp
#
# Die kontinuierliche Annäherung (moveToward) übernimmt jetzt ALTracker.
# Dieses Modul deckt nur noch Initialisierung und den finalen Stoß ab.

import config


def init_locomotion(motion, posture_proxy):
    """Versetzt den Roboter in Ausgangsposition für die Fortbewegung."""
    try:
        motion.setStiffnesses("Body", 1.0)
    except Exception:
        pass
    try:
        motion.wakeUp()
    except Exception:
        pass
    if posture_proxy is not None:
        try:
            posture_proxy.goToPosture(config.LOCOMOTION_INIT_POSTURE,
                                      config.LOCOMOTION_POSTURE_SPEED)
        except Exception:
            pass
    try:
        motion.moveInit()
    except Exception:
        pass


def move_to(motion, distance_m):
    """Fährt eine feste Strecke vorwärts (blockierend). Für den finalen Stoß."""
    try:
        motion.moveTo(float(distance_m), 0.0, 0.0)
    except Exception:
        pass


def stop_move(motion):
    """Stoppt jede laufende Bewegung des Roboters."""
    try:
        motion.stopMove()
    except Exception:
        pass