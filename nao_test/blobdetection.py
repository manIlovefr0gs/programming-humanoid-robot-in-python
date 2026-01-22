# -*- coding: utf-8 -*-
"""
NAO Color Blob Detection mit ALColorBlobDetection
Erkennt Rot, Grün oder Blau über die Live-Kamera
Python 2.7 kompatibel
"""

from naoqi import ALProxy, ALBroker, ALModule
from nao_config import *
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from nao_config import *

# Globale Variable für Callback
ColorDetector = None

class ColorBlobDetectorModule(ALModule):
    """Modul zum Empfangen der Color Blob Detection Events"""
    
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.memory = ALProxy("ALMemory")
        self.detected = False
        self.blob_info = None
        
        # Event abonnieren
        self.memory.subscribeToEvent(
            "ALTracker/ColorBlobDetected",
            "ColorDetector",
            "onColorBlobDetected"
        )
        print("Event abonniert: ALTracker/ColorBlobDetected")
    
    def onColorBlobDetected(self, eventName, value, subscriberIdentifier):
        """Callback wenn ein Farb-Blob erkannt wurde"""
        self.detected = True
        self.blob_info = value
        print("Farb-Blob erkannt!")
        print("Event-Daten:", value)


def detect_color(color_detection, myBroker, color_name):
    """
    Erkennt eine bestimmte Farbe über die Roboter-Kamera
    
    Args:
        robot_ip (str): IP-Adresse des Roboters
        robot_port (int): Port des Roboters (normalerweise 9559)
        color_name (str): "rot", "gruen" oder "blau"
    
    Returns:
        dict: Informationen über erkannten Blob oder None
    """
    
    # Farbdefinitionen (RGB + Schwellenwert)
    colors = {
        "rot":   {"r": 255, "g": 0,   "b": 0,   "threshold": 60},
        "gruen": {"r": 0,   "g": 255, "b": 0,   "threshold": 60},
        "blau":  {"r": 0,   "g": 0,   "b": 255, "threshold": 60}
    }
    
    if color_name.lower() not in colors:
        print("Fehler: Farbe muss 'rot', 'gruen' oder 'blau' sein")
        return None
    
    color = colors[color_name.lower()]
    
    # Broker für Event-Callbacks erstellen

    

    ColorDetector = ColorBlobDetectorModule("ColorDetector")
    
    try:
        # Proxies erstellen
        
        print("\n=== NAO Color Blob Detection ===")
        print("Suche nach Farbe: {}".format(color_name))
        print("RGB: ({}, {}, {})".format(color["r"], color["g"], color["b"]))
        
        # Farbe konfigurieren
        color_detection.setColor(
            color["r"],
            color["g"],
            color["b"],
            color["threshold"]
        )
        print("Farbe konfiguriert (Schwellenwert: {})".format(color["threshold"]))
        
        # Objekt-Eigenschaften setzen
        min_size = 50      # Minimale Größe in Pixeln
        span = 0.05        # Größe des Objekts in Metern (5cm)
        color_detection.setObjectProperties(min_size, span)
        print("Objekt-Eigenschaften: min_size={} px, span={} m".format(min_size, span))
        
        # Optional: Auto-Exposure deaktivieren für bessere Farberkennung
        # color_detection.setAutoExposure(False)
        
        # Extractor starten
        color_detection.subscribe("ColorDetectionApp")
        print("\nFarberkennung gestartet...")
        print("Warte auf Erkennung (10 Sekunden)...")
        
        # Warten auf Erkennung
        timeout = 10.0
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if ColorDetector.detected:
                print("\n=== Farb-Blob gefunden! ===")
                
                # Kreis-Informationen abrufen
                try:
                    circle = color_detection.getCircle()
                    print("Position (x, y, radius):", circle)
                except Exception as e:
                    print("Konnte Kreis-Info nicht abrufen:", e)
                
                # Event-Daten
                if ColorDetector.blob_info:
                    print("Event-Daten:", ColorDetector.blob_info)
                
                # Extractor stoppen
                color_detection.unsubscribe("ColorDetectionApp")
                
                return {
                    "found": True,
                    "circle": circle if 'circle' in locals() else None,
                    "event_data": ColorDetector.blob_info
                }
            
            time.sleep(0.1)
        
        # Timeout erreicht
        print("\nKein Farb-Blob gefunden (Timeout)")
        color_detection.unsubscribe("ColorDetectionApp")
        
        return {"found": False}
        
    except Exception as e:
        print("Fehler:", e)
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Broker schließen
        myBroker.shutdown()


def main():

    nao = InitNao()
    """Hauptprogramm"""
    
    # Farbe hardcoded festlegen
    # Mögliche Werte: "rot", "gruen", "blau"
    COLOR_NAME = "gruen"
    nao = InitNao()
    detect_color_blob_proxy = nao.get_proxy("ALColorBlobDetection")
    # Farberkennung starten
    result = detect_color(nao.ip, nao.port, COLOR_NAME)
    
    if result and result.get("found"):
        print("\n=== ERFOLG ===")
        print("Farbe '{}' wurde erkannt!".format(COLOR_NAME))
    else:
        print("\n=== KEINE ERKENNUNG ===")
        print("Farbe '{}' wurde nicht gefunden.".format(COLOR_NAME))


if __name__ == "__main__":
    main()