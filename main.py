# =========================
# ======= IMPORTS =========
# =========================

import time, random, sys, subprocess, json, math, collections, html, copy, time
from prompt_toolkit import print_formatted_text as print, HTML, prompt as input
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.application import run_in_terminal, get_app, Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, is_done

import threading

# =========================
# ====== LOAD DATA ========
# =========================

with open('data.json', 'r') as file:
    data = json.load(file)

ride = data['ride']
staff = data['staff']
guest = data['guest']

exit = False
player = {}

def save_check():
    global player
    _ = ("Do you have a save line? Y/N --> ")
    match _:
        case "Y" | "y" | "yes":
            print("AAAA")
        case "N" | "n" | "no":
            player['name'] = input("What is your name? --> ")
            player['pname'] = input("name your themepark --> ")
            player['money'] = 1000000
            player['reputation'] = 0.0      # +- 100.0
            
def export_save():
    save = (player["name"])
    print(save)

# =========================
# ======= HELPERS =========
# =========================

def clear_screen():
    cmd = 'cls' if sys.platform.startswith('win') else 'clear'
    subprocess.run(cmd, shell=True)









# =========================
# ===== GAME HANDLER ======
# =========================




def game():
    global player, exit

    


# =========================
# ======= ENTRY POINT =====
# =========================

if __name__ == "__main__":
    save_check()
    while exit != True:
        game()
    export_save()