# =========================
# ======= IMPORTS =========
# =========================

import sys, subprocess, json, math, random, time, threading, collections, html, copy, statistics
from prompt_toolkit import print_formatted_text as print, HTML, prompt as input
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.application import run_in_terminal, get_app, Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, is_done
from simple_term_menu import TerminalMenu

# =========================
# ======= GLOBALS =========
# =========================

exit = False
manage = False
month = 1
page = "1"
main_menu_exit = False

#Stores all active game data
saveFile = {}

date = {}
mList = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")

# =========================
# ====== LOAD DATA ========
# =========================

#Reads data json. Data in this json is set by the game developers, read-only.
with open('data.json', 'r') as file:
    data = json.load(file)

#Uses data json to define several dictionaries containing game data, read-only.
model = data['model']
manufacture = data['manufacture']
staff = data['staff']
guest = data['guest']
monthData = data['monthData']

# =========================
# ======= HELPERS =========
# =========================

#Completely clears the terminal
def clear_screen():
    cmd = 'cls' if sys.platform.startswith('win') else 'clear'
    subprocess.run(cmd, shell=True)

#Limits any number to be between a minimum value and maximum value
def clamp_number(num, min_val, max_val):
    return max(min_val, min(num, max_val))



#Check if player already has a save
def save_check():
    
    #Create new save file dictionary
    global saveFile

    #Prompt player (yes or no)
    choice = input("Do you have a save line? Y/N --> ").lower()

    #Use player choice to determine next action
    match choice:

        #Yes, they have a file. Open file.
        case "y" | "yes":
            with open('save.json', 'r') as file:
                saveFile = json.load(file)
        
        #No, they don't have a file. Create new file, ask player for their name and park name.
        #Save files store name, park name, money, reputation, advertising budget, and rides.
        case "n" | "no":
            saveFile['name'] = input("What is your name? --> ")
            saveFile['pname'] = input("Name your themepark --> ")
            saveFile["currentDate"] = date
            saveFile['money'] = 1_000_000
            saveFile['reputation'] = 0.0      # +- 100.0
            saveFile['advertising'] = 1.0     # + 100.0, min of 1
            saveFile['rides'] = {}



#Write saveFile dictionary to save json file
def export_save():

    
    with open("save.json", "w") as f:
        json.dump(saveFile, f, indent=2)
        
    print("Game saved.")



# =========================
# ===== GAME HANDLER ======
# =========================

def get_date(m):
    mReal = (m - 1) % 12 + 1
    mName = mList[mReal - 1]
    y = (m // 12) + 1980
    guestBonus = monthData.get(mName, {}).get('guestBonus', 1.0)
    saveFile['currentDate']  = {"month": m, "real": mReal, "name": mName, "year": y}

def simulate():
    guestsCount = math.floor((saveFile['reputation'] + 100) * saveFile['advertising'] * data['monthData'][saveFile['currentDate']['name']]['guestBonus'])
    guestList = random.choices(list(guest.keys()), [guest[g]['weight'] for g in guest], k=guestsCount)

    #Loop for all guests in simulation this month
    for guest in guestList:

        #Give each guest a random amount of time in the park from 2-8 hours, and set their initial hunger stat to 0
        timeInPark = random.randint(120, 480)
        hunger = 0

        #Hunger clock counts up with time is spent in the park (minutes), resets every time it surpasses 30 minutes
        hungerClock = 0
        
        #Keep this loop going while the guest still has time to be in the park (time deducted at end of loop)
        while timeInPark > 0:
            
            #If hunger clock is ready, increase hunger randomly, 50/50 chance to increase hunger stat by 1, and reset clock
            if hungerClock >= 30:                            
                hunger += random.randint(0, 1)
                hungerClock = 0
            
            #Check if guest is hungry, eat if so, and return to start of loop
            if hunger >= 5:
                #Eat
                hunger = 0
                return

            #Guest chooses a RANDOM ride, excitement of ride is chance
            currentRide = random.choice(list(model.keys()))
            chanceToRide = currentRide["excitement"]

            #Do checks to degrade chance of ridership

            #If intensity is outside of preference range, multiply chance by 2/3
            if currentRide["intensity"] < guest[guest]['intensityPreference'[0]] or currentRide['intensity'] > guest[guest]['intensityPreference'[1]]:
                chanceToRide = chanceToRide * (2/3)
            
            #If ride is older than the guest prefers, divide by an increasing amount proportionate to the age of the ride
            if currentRide['age'] > guest[guest]['agePreference']:
                chanceToRide = chanceToRide / clamp_number((0.1 * (currentRide['age'] - guest[guest]['agePreference']) + 1), 1, 5)
            
            #If price is higher than guest's tolerance, divide by an increasing amount proportionate to the ride price
            if currentRide['price'] > guest[guest]['priceTolerence']:
                chanceToRide = chanceToRide / (0.5 * (currentRide['price'] - guest[guest]['priceTolerence'] - currentRide['Theming']) + 1)
            
            #Multiply by manufacturer multiplier (Bow = 0.8, multiply by 0.8)
            chanceToRide = chanceToRide * currentRide['manufacturer'['qMult']]

            #Multiply chance by 1/4 if ride is too full
            if currentRide['ridersThisMonth'] > currentRide['monthlyCapacity']:
                chanceToRide * 0.25

            #Roll random to determine if this guest rides this ride
            if chanceToRide > random.randint(0, 100):
                #Ride, spend a fat minute (15-45 mins), add to ride stats
                timeSpent = random.randint(15, 45)
                timeInPark -= timeSpent
                hungerClock += timeSpent         
                currentRide['ridersThisMonth'] += 1   
            else:
                #Do nothing, waste 5 minutes
                timeInPark -= 5
                hungerClock += 5



#Prompts player several times to define a new ride entry, if they can afford it
def build_coaster():

    model_menu = TerminalMenu(
        menu_entries = ,
        title = "Select what model you'd like to build.",
        menu_cursor_style = ("fg_red", "bold"),
        menu_highlight_style = ("bg_gray", "bold"),
        cycle_cursor = True,
        clear_screen = True
    )

    newRideModel

    #Get new ride name
    newRideName = input("What would you like to call your new ride? -->")


# =========================
# ======= UI SYSTEM =======
# =========================
def playerTab(m): 
    print("------------------------------------------------------")
    




def parkTab(m): 

    tab_menu = TerminalMenu(
        menu_entries = ["a", "b"],
        title = f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} |",
        menu_cursor = "> ",
        menu_cursor_style = ("fg_red", "bold"),
        menu_highlight_style = ("bg_gray", "bold"),
        cycle_cursor = True,
        clear_screen = True
    )

    tab_sel = tab_menu.show()

def rideTab(m): 


    tab_menu = TerminalMenu(
        menu_entries = ['Build Coaster', 'Build Flat Ride'] + saveFile['rides'].keys(),
        title = f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} |",
        menu_cursor = "> ",
        menu_cursor_style = ("fg_red", "bold"),
        menu_highlight_style = ("bg_gray", "bold"),
        cycle_cursor = True,
        clear_screen = True,
        quit_keys = ("escape", "backspace"),
    )

    tab_sel = tab_menu.show()

    if tab_sel == 0:
        build_coaster()
    elif tab_sel == 1:
        build_flat_ride()
    else:
        print(saveFile['rides'][tab_sel-2])
    



def foodTab(m): pass
def carnivalTab(m): pass
def commoditiesTab(m): pass
def staffTab(m): pass
def maintanenceTab(m): pass
def advertisingTab(m): pass
def realEstateTab(m): pass
def stockTab(m): pass
def settingTab(m): 
    export_save()






tabs = {
    "Player Information": playerTab,
    "Park Information": parkTab,
    "Rides": rideTab,
    "Food Stalls": foodTab,
    "Carnival Games": carnivalTab,
    "Commodities": commoditiesTab,
    "Staff": staffTab,
    "Maintanence": maintanenceTab,
    "Advertising": advertisingTab,
    "Real Estate": realEstateTab,
    "Stock Market": stockTab,
    "Settings": settingTab
}

def UI():
    global page, manage

    main_menu = TerminalMenu(
        menu_entries = list(tabs.keys()),
        title = f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} | \n------------------------------------------------------\nSelect a tab, use arrow keys to navigate.",
        menu_cursor = "> ",
        menu_cursor_style = ("fg_red", "bold"),
        menu_highlight_style = ("bg_gray", "bold"),
        cycle_cursor = True,
        clear_screen = True,
    )


    while not main_menu_exit:
        main_sel = main_menu.show()

        func = tabs[list(tabs.keys())[main_sel]]
        if func:
            func(manage)












# =========================
# ======= ENTRY POINT =====
# =========================

def gameTurn():
    global date, month
    get_date(month)
    UI()

if __name__ == "__main__":

    # Check if the player has a save line, if not, create a new profile
    save_check()

    # Keep running until exit is true
    while not exit:
        gameTurn()
        # progress to next turn/month
        month += 1
    
    export_save()