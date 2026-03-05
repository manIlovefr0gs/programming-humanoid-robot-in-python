#runs on python3

import socket
import sys
import os
import json
import threading
import pyaudio
from vosk import Model, KaldiRecognizer

# Configuration
HOST = '127.0.0.1'
PORT = 65432
MODEL_PATH = "model" 
SAMPLE_RATE = 16000
CHUNK_SIZE = 4000

# 1. Load Model
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Please download a model from https://alphacephei.com/vosk/models and unpack as '{MODEL_PATH}'")
    sys.exit(1)

print("[Server] Loading Vosk Model... (Please wait)")
model = Model(MODEL_PATH)
# We initialize the recognizer here to keep it ready in memory
rec = KaldiRecognizer(model, SAMPLE_RATE)

class VoskServer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.rec_thread = None

    def _init_stream(self):
        """Opens the stream if not already open."""
        if self.stream is None:
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=SAMPLE_RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK_SIZE)

    def _record_loop(self):
        """Background loop: reads audio and feeds the recognizer."""
        print("[Server] >> Audio Loop Started")
        self.stream.start_stream()
        
        while self.is_recording:
            try:
                # Blocks here for ~0.25s (4000 frames @ 16k)
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                if len(data) == 0: 
                    break
                
                if self.rec.AcceptWaveform(data):
                    # Optional: You could log partial results here if needed
                    pass
            except Exception as e:
                print(f"[Server] Error in record loop: {e}")
                break

        self.stream.stop_stream()
        print("[Server] >> Audio Loop Ended")

    def start(self):
        """Sets flag and starts the background thread."""
        self._init_stream()
        self.rec = rec # Reset or use existing instance
        self.is_recording = True
        
        # Start the recording in a separate thread so the main socket loop isn't blocked
        self.rec_thread = threading.Thread(target=self._record_loop)
        self.rec_thread.start()

    def stop(self):
        """Signals thread to stop, WAITS for it, then returns text."""
        if not self.is_recording:
            return ""

        print("[Server] Stopping recording...")
        self.is_recording = False
        
        # CRITICAL FIX: Wait for the audio thread to actually finish
        # This prevents the 'race condition' from the previous code.
        if self.rec_thread is not None:
            self.rec_thread.join() 

        # Get the final result from Vosk
        res = json.loads(rec.FinalResult())
        final_text = res.get('text', '')
        
        # Clear the recognizer for the next interaction
        rec.Reset()
        
        return final_text

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    
    print(f"[Server] Vosk Service Running on {HOST}:{PORT}")

    engine = VoskServer()

    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"[Server] Connected: {addr}")
            
            while True:
                data = conn.recv(1024)
                if not data: break
                
                command = data.decode('utf-8').strip()

                if command == "START":
                    engine.start()
                    conn.sendall(b"ACK_START")
                
                elif command == "STOP":
                    text = engine.stop()
                    print(f"[Server] Result: {text}")
                    conn.sendall(text.encode('utf-8'))

            conn.close()
            print("[Server] Client disconnected")
            
        except KeyboardInterrupt:
            print("\n[Server] Shutting down...")
            break
        except Exception as e:
            print(f"[Server] Connection Error: {e}")

if __name__ == "__main__":
    run_server()