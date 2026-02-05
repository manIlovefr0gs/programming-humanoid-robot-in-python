# -*- coding: utf-8 -*-
"""
NAO Roboter Konfiguration
Zentrale Konfigurationsdatei für alle NAO-Programme
"""

from naoqi import ALProxy

class InitNao:
    """NAO Roboter Konfiguration und Proxy-Manager"""
    
    # IP-Adresse und Port des Roboters
    IP = "192.168.1.118"
    PORT = 9559
    
    # Farbdefinitionen für Blob Detection
    # Format: {"r": Red, "g": Green, "b": Blue, "threshold": Toleranz}
    COLORS = {
        "rot":   {"r": 255, "g": 0,   "b": 0,   "threshold": 40},
        "red":   {"r": 255, "g": 0,   "b": 0,   "threshold": 40},
        "grün":  {"r": 0,   "g": 255, "b": 0,   "threshold": 40},
        "gruen": {"r": 0,   "g": 255, "b": 0,   "threshold": 40},
        "green": {"r": 0,   "g": 255, "b": 0,   "threshold": 40},
        "blau":  {"r": 0,   "g": 0,   "b": 255, "threshold": 40},
        "blue":  {"r": 0,   "g": 0,   "b": 255, "threshold": 40}
    }
    
    def __init__(self, ip=None, port=None):
        """
        Initialisiert NAO-Konfiguration
        
        Args:
            ip (str): Optional - überschreibt Standard-IP
            port (int): Optional - überschreibt Standard-Port
        """
        self.ip = ip or self.IP
        self.port = port or self.PORT
        self._proxies = {}
    
    def get_proxy(self, proxy_name):
        """
        Erstellt oder gibt existierenden Proxy zurück
        
        Args:
            proxy_name (str): Name des NAOqi-Moduls (z.B. "ALMotion")
        
        Returns:
            ALProxy: Proxy-Objekt oder None bei Fehler
        """
        if proxy_name not in self._proxies:
            try:
                self._proxies[proxy_name] = ALProxy(
                    proxy_name, 
                    self.ip, 
                    self.port
                )
                print("Proxy erstellt: " + proxy_name)
            except Exception as e:
                print("FEHLER beim Erstellen von {}: {}".format(
                    proxy_name, str(e)))
                return None
        
        return self._proxies[proxy_name]
    
    def get_color_config(self, color_name):
        """
        Gibt Farbkonfiguration zurück
        
        Args:
            color_name (str): Name der Farbe (deutsch oder englisch)
        
        Returns:
            dict: Farbkonfiguration oder None
        """
        color_key = color_name.lower()
        if color_key in self.COLORS:
            return self.COLORS[color_key]
        else:
            print("Unbekannte Farbe: " + color_name)
            return None