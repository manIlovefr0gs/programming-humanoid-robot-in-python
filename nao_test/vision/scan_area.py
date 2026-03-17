
from naoqi import ALProxy
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from nao_config import *




def scan_area(nao):
    """Bewegt den NAO Kopf von links nach rechts"""
    
    try:
        # Verbindung zu NAO herstellen
        print("Verbinde mit NAO...")
        motion = ALProxy("ALMotion", nao.ip, nao.port)
        
        # Stiffness aktivieren (Motoren einschalten)
        print("Aktiviere Motoren...")
        motion.setStiffnesses("Head", 1.0)
        time.sleep(1.0)
        
        # Geschwindigkeit festlegen (0.0 - 1.0)
        speed = 0.1  # Langsam fuer genaues Scannen
        
        print("Starte Kopf-Scan...")
        print("(Druecken Sie Ctrl+C zum Beenden)")
        
        # Endlos-Schleife: Links -> Rechts -> Links -> ...
        while True:
            # Nach LINKS drehen (positiver Winkel)
            print("  -> Scanne nach links...")
            motion.setAngles("HeadYaw", 2.0, speed)  # ~115 Grad links
            time.sleep(3.0)  # Warten bis Position erreicht
            
            # Nach RECHTS drehen (negativer Winkel)
            print("  -> Scanne nach rechts...")
            motion.setAngles("HeadYaw", -2.0, speed)  # ~115 Grad rechts
            time.sleep(7.0)
            
            # Zurueck zur MITTE
            print("  -> Zurueck zur Mitte...")
            motion.setAngles("HeadYaw", 0.0, speed)
            time.sleep(2.0)
    
    except KeyboardInterrupt:
        print("\n\nScan abgebrochen durch Benutzer.")
    
    except Exception as e:
        print("FEHLER: " + str(e))
        print("Stelle sicher, dass:")
        print("  1. NAO eingeschaltet ist")
        print("  2. IP-Adresse korrekt ist: " + nao.ip)
        print("  3. Netzwerkverbindung besteht")
    
    finally:
        # Motoren ausschalten (Energiesparen)
        try:
            print("\nSchalte Motoren aus...")
            motion.setStiffnesses("Head", 0.0)
            print("Fertig!")
        except:
            pass

if __name__ == "__main__":
    nao=InitNao()
    scan_area(nao)