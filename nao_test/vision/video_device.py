
import numpy as np
import cv2
from naoqi import ALProxy
from nao_config import *

# ALImage Struktur:
# [0] width
# [1] height
# [2] number of layers
# [3] ColorSpace
# [4] timestamp (seconds)
# [5] timestamp (microseconds)
# [6] binary image data
            

def stream_camera(vision_proxy):

    resolution = 0 # 0=QQVGA(160x120), 1=QVGA(320x240), 2=VGA(640x480)
    color_space = 11 # RGB
    camera_index = 0 # 0=top camera, 1=bottom camera

    fps = 30
    nameId = vision_proxy.subscribeCamera("camera", camera_index, resolution, color_space, fps)

    try:
        while True:
            nao_image = vision_proxy.getImageRemote(nameId)
            
            if nao_image is None:
                continue
            
            width = nao_image[0]
            height = nao_image[1]
            image_data = nao_image[6]
            
            image = np.frombuffer(image_data, dtype=np.uint8)
            image = image.reshape((height, width, 3))
            
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imshow("NAO Camera Stream", image_bgr)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            vision_proxy.releaseImage(nameId)
            
    except KeyboardInterrupt:
        print("\nAbgebrochen")
    
    finally:
        vision_proxy.unsubscribe(nameId)
        cv2.destroyAllWindows()

def main():
    
    nao = InitNao()

    vision_proxy = nao.get_proxy("AlVideoDevice")
    stream_camera(vision_proxy)

if __name__ == "__main__":
    main()  