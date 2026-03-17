# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

# Kamera-Konfiguration
CAMERA_ID = 0 
WIDTH = 640
HEIGHT = 480
FPS = 30

def find_available_cameras(max_cameras=5):
    print("Suche nach verfügbaren Kameras")
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                available.append((i, w, h))
                print("Kamera mit ID gefunden: " + str(i))
            cap.release()
    return available


def main():
    # Kamera initialisieren
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print("FEHLER: Kamera " + str(CAMERA_ID) + " konnte nicht geöffnet werden!")
        print("Verfügbare Kameras: " + str([c[0] for c in cameras]))
        return
    
    # Auflösung setzen (wie bei NAO: 640x480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    
    # Tatsächliche Werte auslesen
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print("Kamera initialisiert: " + str(actual_width) + "x" + str(actual_height) + " @ " + str(actual_fps) + " fps")
    print("Drücke 'q' zum Beenden...")
    
    frame_count = 0
    start_time = time.time()
    

    while True:
        # Frame von Kamera holen
        ret, frame = cap.read()
        
        if not ret:
            print("Warnung: Kein Frame empfangen")
            continue
        
        # Optional: Info-Overlay (wie Timestamp bei NAO)
        frame_count += 1
        elapsed = time.time() - start_time
        current_fps = frame_count / elapsed if elapsed > 0 else 0
        
        # Text auf Bild schreiben
        cv2.putText(frame, "Frame: " + str(frame_count), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "FPS: " + str(current_fps), (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Resolution: " + str(actual_width) + "x" + str(actual_height), (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Bild anzeigen (gleicher Fenstertitel wie in test_vision.py)
        cv2.imshow("Desktop Camera Live Feed", frame)
        
        # Mit 'q' beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    
    # Aufräumen
    cap.release()
    cv2.destroyAllWindows()
    
    # Statistik ausgeben
    elapsed = time.time() - start_time
    avg_fps = frame_count / elapsed if elapsed > 0 else 0
    print("\nKamera freigegeben")
    print("Statistik: " + str(frame_count) + " Frames in " + str(elapsed) + "s (Average: " + str(avg_fps) + " fps)")


if __name__ == "__main__":
    main()