import SpeechRecognition as sr

# pip install SpeechRecognition pyaudio

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something ")
        audio = r.listen(source)
    
    try:
        text = r.recognize_google(audio, language='de-DE')
        return text
    except:
        return ""


def main():
    while True:
        command = listen()
        print("You said: " + command)


if __name__ == "__main__":
    main()