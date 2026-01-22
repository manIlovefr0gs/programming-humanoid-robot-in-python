from naoqi import ALProxy


class InitNao:
    
    IP = "192.168.1.102"
    PORT = 9559
    
    COLORS = {
        "red":   (255, 0, 0, 60),
        "green": (0, 255, 0, 60),
        "blue":  (0, 0, 255, 60)
    }

    def __init__(self):
        self.ip = self.IP
        self.port = self.PORT
        self._proxies = {}


    def get_proxy(self, proxy):
        if proxy not in self._proxies:
            self._proxies[proxy] = ALProxy(proxy, self.ip, self.port)
        return self._proxies[proxy]


def main():
    # nur zum testen
    nao = InitNao()
    motion = nao.get_motion_proxy()
    posture = nao.get_posture_proxy()


