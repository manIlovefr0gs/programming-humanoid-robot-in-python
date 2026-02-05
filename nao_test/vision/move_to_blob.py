# -*- coding: utf-8 -*-
"""
NAO Move to Blob - Vollständige Version
Sucht farbiges Objekt, läuft hin und kippt es um
"""
import sys
import os
import time
import random
import numpy as np

# --- Setup Paths ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from naoqi import ALProxy, ALBroker, ALModule
from nao_config import InitNao

# Falls SpeechRecognizerClient verfügbar ist, importieren
# Ansonsten Fallback auf manuelle Eingabe
try:
    sys.path.append(os.path.join(current_dir, "..", "..", "voice_recog"))
    from speech_client import SpeechRecognizerClient
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("SpeechRecognizerClient nicht verfügbar - verwende Tastatur-Eingabe")

# Global var for the module
BlobTrackerModule = None


class BlobTracker(ALModule):
    """
    Monitors the blob detection event.
    """
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.memory = ALProxy("ALMemory")
        self.last_detection = 0
        self.is_visible = False
        self.module_name = name
        
        try:
            # Subscribe to the ColorBlobDetected event using OUR unique name
            self.memory.subscribeToEvent(
                "ALTracker/ColorBlobDetected", 
                self.module_name, 
                "on_detect"
            )
            print("Event subscribed: ALTracker/ColorBlobDetected")
        except Exception as e:
            print("Warning subscribing to event: " + str(e))
    
    def on_detect(self, event, value, id):
        """Callback when a blob is seen"""
        if value and len(value) > 0:
            self.last_detection = time.time()
            self.is_visible = True
            # print("Blob detected at " + str(time.time()))
        else:
            self.is_visible = False

    def seen_recently(self, seconds=1.0):
        """Returns True if object was seen within 'seconds'"""
        return (time.time() - self.last_detection) < seconds
    
    def shutdown(self):
        """Clean unsubscribe"""
        try:
            self.memory.unsubscribeToEvent(
                "ALTracker/ColorBlobDetected", 
                self.module_name
            )
            print("Event unsubscribed successfully")
        except Exception as e:
            print("Error unsubscribing: " + str(e))


def configure_vision(blob_proxy, color_name):
    """Sets up the camera for the specific color - using proven settings"""
    config = InitNao()
    
    # German/English mapping
    color_map = {
        "red": "red", "rot": "red",
        "green": "green", "grün": "green", "grun": "green", 
        "blue": "blue", "blau": "blue"
    }
    
    key = color_map.get(color_name.lower(), "red")
    print("Configuring camera for color: " + key)
    
    if key in config.COLORS:
        c = config.COLORS[key]
        # Set color parameters (RGB + Threshold)
        blob_proxy.setColor(c["r"], c["g"], c["b"], c["threshold"])
        print("Color set: RGB({}, {}, {}) Threshold: {}".format(
            c["r"], c["g"], c["b"], c["threshold"]))
        
        # Set object size - WICHTIG: Genau wie in blobdetection.py
        # min_size in Pixeln, span in Metern
        min_size = 20      # Minimale Größe in Pixeln (für 5-10cm Objekte)
        span = 0.05        # Geschätzte Objektgröße in Metern (5cm)
        blob_proxy.setObjectProperties(min_size, span)
        print("Object properties set: min_size={}px, span={}m".format(min_size, span))
        
        # Optional: Auto-Exposure für stabilere Farberkennung
        # Auskommentiert lassen, da es manchmal Probleme macht
        # blob_proxy.setAutoExposure(False)
    else:
        print("ERROR: Color not found in config!")
    
    return key


def perform_wipe_move(motion):
    """The attacking move - pushes object with right arm"""
    print("\n=== Starte Wisch-Bewegung! ===")
    
    # Set stiffness for arm and body
    motion.setStiffnesses("RArm", 1.0)
    motion.setStiffnesses("Body", 1.0)
    
    # 1. Raise Arm (Prepare)
    print("Phase 1: Arm vorbereiten...")
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"]
    times = [1.0, 1.0, 1.0, 1.0, 1.0]
    keys  = [-0.2, -1.2, 1.5, 1.5, 1.0]  # Hand open
    motion.angleInterpolation(names, keys, times, True)
    
    time.sleep(0.5)
    
    # 2. Strike (Swipe Inwards)
    print("Phase 2: Schlag ausführen!")
    names = ["RShoulderRoll", "RElbowYaw"]
    times = [0.4, 0.4]  # Fast speed
    keys  = [0.2, -1.0] 
    motion.angleInterpolation(names, keys, times, True)
    
    time.sleep(1.0)
    
    # 3. Relax arm
    print("Phase 3: Arm entspannen...")
    motion.setStiffnesses("RArm", 0.0)
    
    print("Wisch-Bewegung abgeschlossen!")


def scan_head(motion):
    """
    Manually moves head to find the object - SLOW for better image quality.
    Returns immediately (non-blocking) so we can check for blobs while moving.
    """
    # VIEL LANGSAMERE Scan-Bewegung für stabile Bilder
    # Scan path: Center -> Left (langsam) -> Right (langsam) -> Center
    names = ["HeadYaw", "HeadPitch"]
    # Yaw: 0° -> 45° links -> 45° rechts -> 0°
    # Pitch: leicht nach unten für besseren Blickwinkel
    keys  = [[0.0, 0.8, -0.8, 0.0], [0.0, -0.3, -0.3, -0.3, 0.0]] 
    # LANGSAME Zeiten: 15 Sekunden für kompletten Scan (statt 9 Sekunden)
    times = [[2.0, 7.0, 12.0, 15.0], [2.0, 7.0, 12.0, 15.0]]
    
    # 'post' makes it non-blocking
    motion.post.angleInterpolation(names, keys, times, True)
    print("Head scan started (SLOW mode for stable images)")


def take_search_picture(video_proxy, picture_number):
    """
    Macht ein Bild während der Suche
    """
    try:
        from PIL import Image
        
        # Subscribe to camera
        name = video_proxy.subscribeCamera(
            "search_capture_" + str(picture_number),
            0,      # Top camera
            2,      # VGA 640x480 (bessere Qualität)
            11,     # RGB
            10      # 10 FPS
        )
        
        # Kurz warten damit Kamera stabilisiert
        time.sleep(0.3)
        
        # Bild holen
        img = video_proxy.getImageRemote(name)
        
        if img:
            width = img[0]
            height = img[1]
            data = img[6]
            
            image = np.frombuffer(data, dtype=np.uint8)
            image = image.reshape((height, width, 3))
            
            # Bild speichern
            filename = "search_scan_{}.png".format(picture_number)
            Image.fromarray(image).save(filename)
            print("  -> Picture saved: " + filename)
            
            video_proxy.unsubscribe(name)
            return True
        else:
            video_proxy.unsubscribe(name)
            return False
    except Exception as e:
        print("  -> Could not take picture: " + str(e))
        try:
            video_proxy.unsubscribe(name)
        except:
            pass
        return False


def get_color_from_voice(nao, tts):
    """Gets color via voice recognition"""
    if not SPEECH_AVAILABLE:
        print("Voice recognition not available!")
        return None
    
    try:
        client = SpeechRecognizerClient(host="127.0.0.1")
        target_color = None
        
        print("\n=== Waiting for voice command ===")
        tts.say("Which color?")
        
        for attempt in range(5):
            print("Attempt " + str(attempt+1) + "/5 - Listening...")
            text = client.get_one_command()
            print("Heard: '" + text + "'")
            
            if "red" in text or "read" in text or "rat" in text or "rot" in text:
                target_color = "red"
                break
            elif "green" in text or "grain" in text or "seen" in text or "grün" in text or "grun" in text:
                target_color = "green"
                break
            elif "blue" in text or "glue" in text or "low" in text or "blau" in text:
                target_color = "blue"
                break
            elif "empty" in text or text.strip() == "":
                print("Nothing heard - trying again...")
            else:
                tts.say("Please say Red, Green or Blue.")
        
        return target_color
        
    except Exception as e:
        print("Error in voice recognition: " + str(e))
        return None


def get_color_from_keyboard():
    """Gets color via keyboard input"""
    print("\n=== Keyboard Input ===")
    print("Enter target color (red/green/blue):")
    
    valid_colors = ["red", "green", "blue", "rot", "grün", "gruen", "blau"]
    
    for attempt in range(3):
        try:
            color = raw_input("> ").strip().lower()
            
            if color in valid_colors:
                # Normalize to English
                if color == "rot":
                    return "red"
                elif color in ["grün", "gruen"]:
                    return "green"
                elif color == "blau":
                    return "blue"
                else:
                    return color
            else:
                print("Invalid color. Please enter: red, green, or blue")
        except KeyboardInterrupt:
            print("\nAborted by user")
            return None
    
    return None


def main():
    print("\n" + "="*60)
    print(" NAO COLOR BLOB TRACKER - MOVE TO BLOB")
    print("="*60 + "\n")
    
    nao = InitNao()
    my_broker = None
    tracker = None
    
    # --- Initialize Proxies ---
    try:
        motion = nao.get_proxy("ALMotion")
        tracker = nao.get_proxy("ALTracker")
        blob_proxy = nao.get_proxy("ALColorBlobDetection")
        tts = nao.get_proxy("ALTextToSpeech")
        posture = nao.get_proxy("ALRobotPosture")
        video_proxy = nao.get_proxy("ALVideoDevice")
    except Exception as e:
        print("ERROR: Could not connect to robot!")
        print(str(e))
        print("\nPlease check:")
        print("1. Robot IP address in nao_config.py")
        print("2. Robot is turned on and connected")
        print("3. NAOqi is running on robot")
        return

    # --- 1. Init - Stand Up ---
    print("\n[STEP 1/5] Standing up...")
    tts.say("I am standing up")
    motion.wakeUp()
    posture.goToPosture("StandInit", 0.8)
    print("Standing up complete!")
    time.sleep(2)  # 2 Sekunden warten für stabile Kamera

    # --- 2. Get Target Color ---
    print("\n[STEP 2/5] Getting target color...")
    target_color = None
    
    # Try voice first if available, otherwise keyboard
    if SPEECH_AVAILABLE:
        print("Trying voice recognition...")
        target_color = get_color_from_voice(nao, tts)
        
        if not target_color:
            print("Voice recognition failed, switching to keyboard...")
            target_color = get_color_from_keyboard()
    else:
        target_color = get_color_from_keyboard()
    
    if not target_color:
        tts.say("I did not understand. Goodbye.")
        print("ERROR: No valid color received!")
        posture.goToPosture("Sit", 0.8)
        motion.rest()
        return

    print("Target color: " + target_color.upper())
    tts.say("Looking for " + target_color)

    # --- 3. Vision Setup ---
    print("\n[STEP 3/5] Setting up vision...")
    configure_vision(blob_proxy, target_color)
    
    # Generate UNIQUE module name to prevent "Already Registered" error
    unique_module_name = "BlobTracker_" + str(random.randint(10000, 99999))
    print("Registering module as: " + unique_module_name)
    
    # --- 4. Start Tracking ---
    try:
        # Start broker for event callbacks
        my_broker = ALBroker("myBroker", "0.0.0.0", 0, nao.IP, nao.PORT)
        
        global BlobTrackerModule
        BlobTrackerModule = BlobTracker(unique_module_name)
        
        # Ensure head is stiff so it can move
        motion.setStiffnesses("Head", 1.0)
        
        # Setup Tracker Mode
        tracker.setMode("Move")  # Robot will walk towards target
        tracker.setRelativePosition([0.20, 0.0, 0.0, 0.1, 0.1, 0.3])  # Stop at 20cm
        print("Tracker configured: Stop distance = 20cm")
        
        # --- Main Loop (State Machine) ---
        print("\n[STEP 4/5] Starting search and track...")
        print("States: SEARCH -> TRACK -> DONE")
        print("Max time: 90 seconds\n")
        
        state = "SEARCH"
        start_time = time.time()
        last_status_print = 0
        picture_counter = 0  # Zähler für Bilder
        last_picture_time = 0  # Zeitpunkt des letzten Bildes
        
        while (time.time() - start_time) < 90:  # 90 seconds max
            
            # Print status every 5 seconds
            if time.time() - last_status_print > 5:
                elapsed = int(time.time() - start_time)
                print("Status: {} | Time: {}s/90s".format(state, elapsed))
                last_status_print = time.time()
            
            # Check if we see the blob RIGHT NOW
            seen = BlobTrackerModule.seen_recently(0.5)
            
            if state == "SEARCH":
                if seen:
                    print("\n>>> BLOB FOUND! Switching to TRACK mode <<<")
                    tts.say("Object found")
                    motion.stopMove()  # Stop head scan
                    
                    # Start Tracker
                    tracker.trackEvent("ALTracker/ColorBlobDetected")
                    state = "TRACK"
                    time.sleep(0.5)
                else:
                    # Still searching...
                    # Check if head is moving, if not, trigger new scan
                    if not motion.moveIsActive():
                        print("Scanning head...")
                        scan_head(motion)
                    
                    # Mache alle 3 Sekunden ein Bild während der Suche
                    if (time.time() - last_picture_time) > 3.0 and picture_counter < 5:
                        print("Taking search picture {}...".format(picture_counter + 1))
                        if take_search_picture(video_proxy, picture_counter):
                            picture_counter += 1
                        last_picture_time = time.time()
                    
                    time.sleep(0.5)
                    
            elif state == "TRACK":
                if not seen:
                    # We lost it!
                    print("\n>>> LOST TARGET! Back to SEARCH <<<")
                    tts.say("Lost it")
                    tracker.stopTracker()
                    state = "SEARCH"
                    time.sleep(0.5)
                else:
                    # Tracking is active, robot is walking automatically
                    # We just check the distance to stop
                    try:
                        pos = tracker.getTargetPosition(2)  # 2 = Robot Frame
                        if pos:
                            x_dist = pos[0]
                            y_dist = pos[1]
                            
                            # Print distance occasionally
                            if int(time.time() * 2) % 3 == 0:  # Every ~1.5 sec
                                print("Distance: x={:.2f}m, y={:.2f}m".format(x_dist, y_dist))
                            
                            # Check if we reached the target (20cm +/- 5cm)
                            if abs(x_dist - 0.20) < 0.05:
                                print("\n>>> TARGET REACHED! <<<")
                                tts.say("Target reached")
                                tracker.stopTracker()
                                motion.moveTo(0, 0, 0)  # Ensure full stop
                                state = "DONE"
                                break
                    except Exception as e:
                        print("Warning: Could not get target position - " + str(e))
                        
                time.sleep(0.2)

        # --- 5. Finish ---
        print("\n[STEP 5/5] Finishing mission...")
        
        if state == "DONE":
            print("SUCCESS - Target destroyed!")
            tts.say("Target destroyed.")
            time.sleep(0.5)
            perform_wipe_move(motion)
            time.sleep(1)
            tts.say("Mission complete!")
        else:
            print("TIMEOUT - Could not find or reach target")
            tts.say("Time over. I could not find it.")
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user (Ctrl+C)")
        tts.say("Stopped by user")
        
    except Exception as e:
        print("\nERROR during main loop: " + str(e))
        import traceback
        traceback.print_exc()
        
    finally:
        # This block ALWAYS executes, even on errors
        # Prevents broker staying open
        print("\n" + "="*60)
        print("Cleaning up...")
        print("="*60)
        
        # 1. WICHTIG: Stoppe alle Bewegungen (auch Kopf!)
        try:
            print("Stopping all movements...")
            motion.stopMove()  # Stoppt Körper-Bewegung
            motion.killMove()  # Stoppt ALLE laufenden Bewegungen inkl. Kopf
            time.sleep(0.5)
        except:
            pass
        
        # 2. Kopf in neutrale Position
        try:
            print("Centering head...")
            motion.setStiffnesses("Head", 1.0)
            motion.angleInterpolation(["HeadYaw", "HeadPitch"], [0.0, 0.0], [1.0, 1.0], True)
        except:
            pass
        
        # 3. Tracker cleanup
        if tracker:
            try:
                tracker.stopTracker()
                tracker.unregisterAllTargets()
                print("Tracker stopped")
            except:
                pass
        
        # 4. Blob module cleanup
        if BlobTrackerModule:
            BlobTrackerModule.shutdown()
            print("BlobTracker module unsubscribed")
        
        # 5. Broker cleanup
        if my_broker:
            my_broker.shutdown()
            print("Broker shut down")
        
        # 6. Sit down and rest
        print("Sitting down...")
        try:
            posture.goToPosture("Sit", 0.8)
            time.sleep(0.5)
            motion.rest()
            print("Robot resting")
        except:
            print("Could not sit down properly")
        
        print("\n" + "="*60)
        print(" MISSION COMPLETE")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()