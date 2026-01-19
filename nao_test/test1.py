from naoqi import ALProxy
from nao_config import *

nao = InitNao()
tts = nao.get_proxy("ALTextToSpeech")
#tts = ALProxy("ALTextToSpeech", "192.168.1.118", 9559)
tts.say("Hello")
  