import sys
import os



def execute_script(script_path, script_name):
    print("=" * 50)
    print("Running: " + script_name)
    print()
    

    if os.path.exists(script_path):
        result = subprocess.run([sys.executable, script_path], 
                                capture_output=False)
        
        print( "=" * 50)
        if result.returncode == 0:
            print(script_name + "erfolgreich beendet")
        else:
            print("Error")
        print("=" * 50)
    else:
        print("File not found: " + script_path)

    
def test_menu():

    test_scripts = {
        "1": ("audio/hello.py", "hello.py"),
        "2": ("motion/change_posture.py", "change_posture.py"),
        "3": ("motion/standup.py", "standup.py"),
        "4": ("motion/walk_straight.py", "walk_straight.py"),
        "5": ("vision/blobdetection.py", "blobdetection.py"),
        "6": ("vision/test_picture.py", "test_picture.py"),
        "7": ("vision/video_device.py", "video_device.py"),
    }
    
    while True:
        clear_console()
        print_test_header()
        
        print("Verfügbare Tests:")
        print()
        
        print("  AUDIO:")
        print("    [1] hello.py ")
        print()
        
        print("  MOTION:")
        print("    [2] change_posture.py")
        print("    [3] standup.py (Falldetection <- funktioniert noch nicht richtig)")
        print("    [4] walk_straight.py")
        print()
        
        print("  VISION:")
        print("    [5] blobdetection.py")
        print("    [6] test_picture.py ")
        print("    [7] video_device.py t")
        print()
        
        
        print("  [0] Zurück zum Hauptmenü")
        print()
        
        choice = input("Ihre Auswahl: ").strip()
        
        if choice == "0":
            break
        elif choice in test_scripts:
            script_path, script_name = test_scripts[choice]
            execute_script(script_path, script_name)
        else:
            print("\n")


if __name__ == "__main__":
    try:
        test_menu()
    except KeyboardInterrupt:
        print("\n\nTestmodus durch Benutzer abgebrochen.")
        sys.exit(0)