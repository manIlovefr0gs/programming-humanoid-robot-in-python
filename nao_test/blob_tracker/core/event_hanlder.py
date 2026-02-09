import time


class EventHandler:
    
    def __init__(self, nao_config):
        self.nao = nao_config
        self.memory_proxy = None
        self._callbacks = {}
    
    
    def initialize(self):
        self.memory_proxy = self.nao.get_proxy("ALMemory")
        print("[EventHandler] Initialized")
    
    
    def subscribe_event(self, event_name, callback):
        if event_name in self._callbacks:
            print(f"[EventHandler] Already subscribed to: {event_name}")
            return
        
        self._callbacks[event_name] = callback
        self.memory_proxy.subscribeToEvent(event_name, "ColorBlobTracker", callback.__name__)
        print(f"[EventHandler] Subscribed to event: {event_name}")
    
    
    def unsubscribe_event(self, event_name):
        if event_name not in self._callbacks:
            return
        
        self.memory_proxy.unsubscribeToEvent(event_name, "ColorBlobTracker")
        del self._callbacks[event_name]
        print(f"[EventHandler] Unsubscribed from event: {event_name}")
    
    
    def unsubscribe_all(self):
        for event_name in list(self._callbacks.keys()):
            self.unsubscribe_event(event_name)
