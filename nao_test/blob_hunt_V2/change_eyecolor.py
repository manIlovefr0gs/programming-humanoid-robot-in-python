# -*- coding: utf-8 -*-

# Augenfarbe des NAO setzen via ALLeds
#
# NAO-Augen-LEDs werden über den Proxy "ALLeds" gesteuert.
# fadeRGB(group, rgb_int, duration_s) setzt alle LEDs der Gruppe auf eine Farbe.
# Gruppe "FaceLeds" umfasst beide Augen.

# Vordefinierte Farben als RGB-Integer (0x00RRGGBB)
COLORS = {
    "red":    0x00FF0000,
    "rot":    0x00FF0000,
    "green":  0x0000FF00,
    "gruen":  0x0000FF00,
    "yellow": 0x00FFFF00,
    "gelb":   0x00FFFF00,
    "blue":   0x000000FF,
    "blau":   0x000000FF,
    "white":  0x00FFFFFF,
    "off":    0x00000000,
}


def set_color(leds, color_name, duration=0.2):
    """Setzt beide Augen auf die übergebene Farbe.

    Args:
        leds:        ALLeds-Proxy
        color_name:  Farbname (z.B. "red", "rot", "white", "off")
        duration:    Überblendzeit in Sekunden
    """
    if leds is None:
        return
    rgb = COLORS.get(str(color_name).strip().lower(), COLORS["white"])
    try:
        leds.fadeRGB("FaceLeds", rgb, float(duration))
    except Exception as e:
        print("eye_color: Fehler beim Setzen der Augenfarbe: {}".format(e))


def reset(leds, duration=0.5):
    """Setzt die Augen auf Weiß zurück (NAO-Standard)."""
    set_color(leds, "white", duration)
