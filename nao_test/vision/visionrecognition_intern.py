# -*- coding: utf-8 -*-
from naoqi import ALProxy
from nao_config import InitNao

# oder VisionRecognitionProxy was ist der richtige Modulname?
class VisionRecognition(object):
    def __init__(self, cfg=None):
        self.cfg = cfg or InitNao()
        self.vr = ALProxy("ALVisionRecognition", self.cfg.ip, self.cfg.port)
        self.mem = ALProxy("ALMemory", self.cfg.ip, self.cfg.port)
        self.sub = None

    def start(self, name="py_vr"):
        self.vr.subscribe(name) 
        self.sub = name

    def stop(self):
        if self.sub:
            self.vr.unsubscribe(self.sub)
            self.sub = None

    def get_result(self):
        try:
            return self.mem.getData("PictureRecognized")
        except:
            return None
    def get_database(self, visionRecProxy):
        db_list = visionRecProxy.getDatabaseList()
        return db_list

def main():
    vr = VisionRecognition()
    db_list = vr.get_database(vr.vr)
    print("Datenbankeinträge:", db_list)
    vr.start()

    try:
        while True:
            data = vr.get_result()
            if data:
                pass  
            time.sleep(0.1)
    finally:
        vr.stop()


if __name__ == "__main__":
    main()  