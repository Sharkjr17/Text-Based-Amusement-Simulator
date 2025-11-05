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

# =========================
# ======= HELPERS =========
# =========================

def clear_screen():
    cmd = 'cls' if sys.platform.startswith('win') else 'clear'
    subprocess.run(cmd, shell=True)









# =========================
# ===== GAME HANDLER ======
# =========================







# =========================
# ======= ENTRY POINT =====
# =========================

if __name__ == "__main__":
    start()