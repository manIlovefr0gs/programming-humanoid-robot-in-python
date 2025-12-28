# test_voice.py (Run with Python 2.7)
from speech_client import SpeechRecognizerClient

def test():
    client = SpeechRecognizerClient()
    if not client.connect():
        print("Error: Could not connect to the server!")
        return

    print("\n--- TEST STARTED ---")
    print("1. Press Enter to START recording...")
    raw_input() 
    
    client.start_listening()
    print(">> LISTENING... (Speak clearly into your mic now)")
    
    print("2. Press Enter to STOP and see result...")
    raw_input()
    
    result = client.stop_listening()
    print("\n[VOSK RESULT]: " + result)
    print("--------------------")
    
    client.close()

if __name__ == "__main__":
    test()