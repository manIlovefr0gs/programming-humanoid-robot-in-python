import cv2
import numpy as np
import time
from typing import Optional, Dict, List



CAMERA_ID = 0  
WIDTH = 640
HEIGHT = 480
FPS = 30

COLOR_RANGES = {
    'rot': [
        [(0, 100, 100), (10, 255, 255)],      
        [(170, 100, 100), (180, 255, 255)]    
    ],
    'gelb': [(20, 100, 100), (30, 255, 255)],
    'Gruen': [(35, 100, 100), (85, 255, 255)],
    'blau': [(90, 100, 100), (130, 255, 255)],
    'orange': [(10, 100, 100), (20, 255, 255)],
}

# Minimale Objektgröße in Pixeln
MIN_OBJECT_AREA = 500


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def find_available_cameras(max_cameras=5):
    """Findet alle verfügbaren Kameras"""
    print("Suche nach verfügbaren Kameras...")
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                available.append((i, w, h))
                print(f"  ✓ Kamera {i}: {w}x{h}")
            cap.release()
    return available


def create_color_mask(hsv_frame: np.ndarray, color_name: str) -> Optional[np.ndarray]:
    """
    Erstellt eine Maske für die angegebene Farbe
    
    Args:
        hsv_frame: Frame im HSV-Farbraum
        color_name: Name der zu erkennenden Farbe
        
    Returns:
        Binäre Maske oder None
    """
    if color_name not in COLOR_RANGES:
        return None
    
    color_range = COLOR_RANGES[color_name]
    
    # Spezialbehandlung für Rot (zwei HSV-Bereiche)
    if isinstance(color_range[0], list):
        masks = []
        for lower, upper in color_range:
            mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
            masks.append(mask)
        mask = cv2.bitwise_or(masks[0], masks[1])
    else:
        lower, upper = color_range
        mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
    
    # Morphologische Operationen (Rauschen entfernen)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    return mask


def detect_object(frame: np.ndarray, color_name: str, min_area: int = MIN_OBJECT_AREA) -> Optional[Dict]:
    """
    Erkennt farbiges Objekt im Frame
    
    Args:
        frame: BGR-Frame von OpenCV
        color_name: Zu erkennende Farbe
        min_area: Minimale Objektfläche in Pixeln
        
    Returns:
        Dict mit Objekt-Informationen oder None
    """
    # In HSV konvertieren (besser für Farberkennung)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Farbmaske erstellen
    mask = create_color_mask(hsv, color_name)
    if mask is None:
        return None
    
    # Konturen finden
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Größte Kontur finden
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    # Zu klein -> Ignorieren
    if area < min_area:
        return None
    
    # Bounding Box berechnen
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Zentrum berechnen
    center_x = x + w // 2
    center_y = y + h // 2
    
    # Momente für präziseren Schwerpunkt (optional)
    M = cv2.moments(largest_contour)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = center_x, center_y
    
    return {
        'color': color_name,
        'x': x,
        'y': y,
        'width': w,
        'height': h,
        'center_x': center_x,
        'center_y': center_y,
        'centroid_x': cx,
        'centroid_y': cy,
        'area': area,
        'contour': largest_contour
    }


def detect_multiple_colors(frame: np.ndarray, colors: List[str]) -> List[Dict]:
    """
    Erkennt mehrere Farben gleichzeitig
    
    Args:
        frame: BGR-Frame
        colors: Liste von Farbnamen
        
    Returns:
        Liste von erkannten Objekten
    """
    detections = []
    
    for color in colors:
        obj = detect_object(frame, color)
        if obj:
            detections.append(obj)
    
    return detections


def draw_detection(frame: np.ndarray, detection: Dict, draw_contour: bool = True):
    """
    Zeichnet Erkennungs-Overlay auf Frame
    
    Args:
        frame: Frame zum Zeichnen (wird modifiziert!)
        detection: Erkennungs-Dictionary
        draw_contour: Ob Kontur gezeichnet werden soll
    """
    color_map = {
        'rot': (0, 0, 255),
        'gelb': (0, 255, 255),
        'gruen': (0, 255, 0),
        'blau': (255, 0, 0),
        'orange': (0, 165, 255)
    }
    
    color = color_map.get(detection['color'], (0, 255, 0))
    
    # Bounding Box
    x, y, w, h = detection['x'], detection['y'], detection['width'], detection['height']
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    
    # Zentrum
    cx, cy = detection['center_x'], detection['center_y']
    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
    
    # Schwerpunkt (wenn unterschiedlich)
    centroid_x, centroid_y = detection['centroid_x'], detection['centroid_y']
    if (cx, cy) != (centroid_x, centroid_y):
        cv2.circle(frame, (centroid_x, centroid_y), 3, (255, 0, 255), -1)
    
    # Kontur (optional)
    if draw_contour and 'contour' in detection:
        cv2.drawContours(frame, [detection['contour']], -1, color, 2)
    
    # Label
    label = f"{detection['color'].upper()}"
    info = f"Pos: ({cx}, {cy}) | Area: {detection['area']:.0f}"
    
    cv2.putText(frame, label, (x, y - 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(frame, info, (x, y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)




def main():
    # Kamera suchen
    cameras = find_available_cameras()
    if not cameras:
        print("FEHLER: Keine Kamera gefunden!")
        print("Stelle sicher, dass Iruni Webcam verbunden ist.")
        return
    
    print(f"\nVerwende Kamera {CAMERA_ID}...")
    
    # Kamera initialisieren
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print(f"FEHLER: Kamera {CAMERA_ID} konnte nicht geöffnet werden!")
        print(f"Verfügbare Kameras: {[c[0] for c in cameras]}")
        return
    
    # Auflösung setzen
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    
    # Tatsächliche Werte
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"Kamera initialisiert: {actual_width}x{actual_height} @ {actual_fps} fps")
    print("\n=== STEUERUNG ===")
    print("'q' - Beenden")
    print("'1' - Nur GELB erkennen")
    print("'2' - Nur GRUEN erkennen")
    print("'3' - Nur BLAU erkennen")
    print("'4' - Nur ROT erkennen")
    print("'5' - Nur ORANGE erkennen")
    print("'a' - ALLE Farben erkennen")
    print("'c' - Konturen an/aus")
    print("=================\n")
    
    # Einstellungen
    current_colors = list(COLOR_RANGES.keys())  
    show_contours = True
    frame_count = 0
    start_time = time.time()
    detection_count = 0
    
    try:
        while True:
            # Frame holen
            ret, frame = cap.read()
            
            if not ret:
                print("Warnung: Kein Frame empfangen")
                continue
            
            frame_count += 1
            
            # Objekte erkennen
            detections = detect_multiple_colors(frame, current_colors)
            
            # Erkennungen zeichnen
            for detection in detections:
                draw_detection(frame, detection, draw_contour=show_contours)
                detection_count += 1
            
            # Statistik-Overlay
            elapsed = time.time() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Info-Text
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Frame: {frame_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Erkannt: {len(detections)}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Farben: {', '.join([c.upper() for c in current_colors])}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Frame anzeigen
            cv2.imshow("Webcam mit Objekterkennung", frame)
            
            # Tastatur-Steuerung
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('1'):
                current_colors = ['gelb']
                print("Modus: Nur GELB")
            elif key == ord('2'):
                current_colors = ['Gruen']
                print("Modus: Nur Gruen")
            elif key == ord('3'):
                current_colors = ['blau']
                print("Modus: Nur BLAU")
            elif key == ord('4'):
                current_colors = ['rot']
                print("Modus: Nur ROT")
            elif key == ord('5'):
                current_colors = ['orange']
                print("Modus: Nur ORANGE")
            elif key == ord('a'):
                current_colors = list(COLOR_RANGES.keys())
                print("Modus: ALLE Farben")
            elif key == ord('c'):
                show_contours = not show_contours
                print(f"Konturen: {'AN' if show_contours else 'AUS'}")
            
            # Console-Output bei Erkennung
            if detections:
                for det in detections:
                    print(f"✓ {det['color'].upper()} bei ({det['center_x']}, {det['center_y']}) | Fläche: {det['area']:.0f}")
    
    except KeyboardInterrupt:
        print("\nUnterbrochen durch Benutzer")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Statistik
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\n=== STATISTIK ===")
        print(f"Frames: {frame_count}")
        print(f"Laufzeit: {elapsed:.1f}s")
        print(f"Durchschnitt: {avg_fps:.1f} fps")
        print(f"Erkennungen: {detection_count}")
        print("Kamera freigegeben")


if __name__ == "__main__":
    main()