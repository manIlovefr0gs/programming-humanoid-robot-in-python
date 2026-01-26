import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
form test_cycle import *
from nao_config import *
from 

def main_menu():

    print("Please select:")
    print()
    print("[1]Start sense-think-act-cycle")
    print("[2]Testmode")
    print("[0]Exit")
    print()

    return choice


def main():
    while True:
        choice = main_menu()
        
        if choice == "1":
            print("Hier noch den sense-think-act-cycle hinpacken")
        elif choice == "2":
            test_menu()
        elif choice == "0":
            clear_console()
            print("Shuting down...")
            print("bye bye!")
            sys.exit(0)
        else:
            print("Choose 0,1 or 2")


def get_voice_command():



def sense_think_act_cycle():
    pass