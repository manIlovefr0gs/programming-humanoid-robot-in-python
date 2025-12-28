"""
=============================================================================
 MODULE: Speech Recognition Client Bridge
 COMPATIBILITY: Python 2.7 (Main App) <--> Python 3 (Speech Server)
=============================================================================
 INSTRUCTIONS:
 1. Place this file in your Python 2.7 project directory.
 2. This file is a 'Remote Control' for vosk_server.py.
 3. Ensure vosk_server.py is running in Python 3 before use.
=============================================================================
"""
import socket

class SpeechRecognizerClient:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            print("Connection failed: " + str(e))
            return False

    def start_listening(self):
        """Sends START command."""
        if self.sock:
            try:
                self.sock.sendall("START".encode('utf-8'))
                # Wait for ACK to ensure server is recording
                self.sock.recv(1024)
            except Exception as e:
                print("Error starting: " + str(e))

    def stop_listening(self):
        """Sends STOP command and waits for text."""
        if self.sock:
            try:
                self.sock.sendall("STOP".encode('utf-8'))
                # Block until we get the full text back
                response = self.sock.recv(4096)
                return response.decode('utf-8')
            except Exception as e:
                return "Error: " + str(e)
        return ""

    def close(self):
        if self.sock:
            self.sock.close()