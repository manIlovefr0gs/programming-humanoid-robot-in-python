from naoqi import ALProxy


class InitNao:
    
    IP = "127.0.0.1"
    PORT = 9559
    
    COLORS = {
        "rot":   (255, 0, 0, 60),
        "gruen": (0, 255, 0, 60),
        "blau":  (0, 0, 255, 60)
    }

    def __init__(self):
        self.ip = self.IP
        self.port = self.PORT
        self._proxies = {}


    def get_proxy(self, proxy):
        if proxy not in self._proxies:
            self._proxies[proxy] = ALProxy(proxy, self.ip, self.port)
        return self._proxies[proxy]

    def get_motion_proxy(self):
        return self.get_proxy("ALMotion")

    def get_posture_proxy(self):
        return self.get_proxy("ALRobotPosture")

    def get_tracker_proxy(self):
        return self.get_proxy("ALTracker")

    def get_memory_proxy(self):
        return self.get_proxy("ALMemory")




def main():
    nao = InitNao()
    motion = nao.get_motion_proxy()
    posture = nao.get_posture_proxy()


