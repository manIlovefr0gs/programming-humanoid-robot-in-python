# -*- coding: utf-8 -*-

from naoqi import ALProxy
from nao_config import *



def get_posture_List(posture_proxy):
    print("Posture List: ")
    try:
        posture_list = posture_proxy.getPostureList()
        print("Posture: " )
        print(posture_list)
    except Exception as e:
        print("Can not get posture list: ")
        print(e)

def get_current_posture(posture_proxy):
    print("\nCurrent Posture")
    try:
        current_posture = posture_proxy.getPosture()
        print("Aktuelle Haltung: " + current_posture)
    except Exception as e:
        print("Can not get current posture: ")
        print(e)

def change_posture(posture_proxy, posture):
    new_posture = posture.strip()
    print("Change posture to: " + new_posture)

    try:
        current_posture = get_current_posture(posture_proxy)
        if current_posture != new_posture:
            posture_proxy.goToPosture(new_posture, 1.0)
        else:
            print("Already in that posture")
    except Exception as e:
        print("Can not change posture: ")
        print(e)
    
    print("Posture changed to: " + new_posture)
    

def main():

    nao = InitNao()
    posture_proxy = nao.get_proxy("ALRobotPosture")
    get_posture_List(posture_proxy)

    #get_current_posture(posture_proxy)
    change_posture(posture_proxy, "Sit")




if __name__ == "__main__":
    main()
