import socket
import time

class SpeechRecognizerClient:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port

    def get_one_command(self):
        """
        Connects, records for 5 seconds, gets result, and closes connection.
        Returns: String (lowercase)
        """
        sock = None
        try:
            # 1. Connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0) # Safety timeout
            sock.connect((self.host, self.port))
            
            # 2. Send Start
            sock.sendall("START".encode('utf-8'))
            
            # 3. Wait for ACK (Ready to record)
            ack = sock.recv(1024)
            if not ack:
                return "error_no_ack"
            
            # 4. Wait for Result (Server records for ~5 sec)
            # We wait a bit longer than the recording time
            sock.settimeout(15.0) 
            response = sock.recv(4096)
            
            if response:
                return response.decode('utf-8').lower()
            else:
                return "empty"
                
        except Exception as e:
            print ("Speech Client Error: " + str(e))
            return "error"
        finally:
            if sock:
                sock.close()