import socket
import sys
import os
import json
import pyaudio

# Check imports
try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    print("Error: Vosk not installed. Run 'pip install vosk pyaudio'")
    sys.exit(1)

# Check Model
MODEL_PATH = "model"
if not os.path.exists(MODEL_PATH):
    print(f"Error: Model folder '{MODEL_PATH}' not found.")
    sys.exit(1)

# Audio Config
HOST = '0.0.0.0'
PORT = 65432
SAMPLE_RATE = 16000
CHUNK_SIZE = 4000

def list_microphones(p):
    print("\n--- Available Microphones ---")
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            print(f"Device ID {i}: {name}")
    print("-----------------------------\n")

def run_server():
    print("[Server] Loading Model... (Please wait)")
    model = Model(MODEL_PATH)
    
    # TRICK: Wir erlauben NUR diese Woerter!
    # [unk] steht fuer "unknown" (unbekanntes Geraeusch)
    grammar = '["red", "green", "blue", "read", "start", "stop", "[unk]"]'
    rec = KaldiRecognizer(model, SAMPLE_RATE, grammar)
    
    p = pyaudio.PyAudio()
    list_microphones(p)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[Server] Ready on {HOST}:{PORT}")
        print("[INFO] Vocabulary restricted to: red, green, blue")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[Connection] Client connected: {addr}")
                
                # Timeout verhindern, falls Client mal haengt
                conn.settimeout(10.0)
                
                try:
                    data = conn.recv(1024)
                    
                    if data and "START" in data.decode('utf-8', errors='ignore'):
                        print(">> Recording (4 seconds)...")
                        conn.sendall(b"ACK") 
                        
                        stream = p.open(format=pyaudio.paInt16, channels=1, 
                                      rate=SAMPLE_RATE, input=True, 
                                      frames_per_buffer=CHUNK_SIZE)
                        stream.start_stream()
                        
                        final_text = ""
                        
                        # Record for approx 4 seconds
                        for i in range(0, int(SAMPLE_RATE / CHUNK_SIZE * 4)):
                            data_audio = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                            if rec.AcceptWaveform(data_audio):
                                res = json.loads(rec.Result())
                                if res['text']:
                                    final_text = res['text']
                                    print(f"   Detected live: {final_text}")

                        if not final_text:
                            res = json.loads(rec.FinalResult())
                            final_text = res.get('text', "")
                        
                        print(f">> Final Result: '{final_text}'")
                        
                        stream.stop_stream()
                        stream.close()
                        
                        response = final_text if final_text else "empty"
                        conn.sendall(response.encode('utf-8'))
                        
                except Exception as e:
                    print(f"Error handling request: {e}")
                
            print("[Connection] Closed.")

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServer stopped.")