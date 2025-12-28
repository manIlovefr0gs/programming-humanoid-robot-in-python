# OFFLINE SPEECH RECOGNITION MODULE

This module enables offline speech recognition in a Python 2.7 
application by offloading the heavy processing to a Python 3 
background service using a local socket connection.

--- SETUP ---

0. (Linux only)
Install required packages:
```
sudo apt update 
sudo apt install portaudio19-dev python3-pyaudio
```

1. PYTHON 3 (Server Side):
   Install dependencies in your Python 3 environment: ```pip install vosk pyaudio```

2. RUNNING:
   - Open a terminal: 
   ```python3 vosk_server.py```
   - Run your main app

--- MODULES ---
- vosk_server.py: The Python 3 background service.
- speech_client.py: The Python 2.7 module for the main app.

--- TESTING ---

To verify microphone and the connection are working:

1. Keep the 'vosk_server.py' running in its terminal.
2. Open a new terminal and run:
   ```python test_voice.py```
3. Follow the on-screen prompts:
   - Press [Enter] once to start listening.
   - Speak clearly into your microphone.
   - Press [Enter] again to stop and see the transcribed text.