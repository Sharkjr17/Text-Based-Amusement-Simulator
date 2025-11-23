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

main_menu_exit = False

# Stores all active game data
saveFile = {}


# =========================
# ====== LOAD DATA ========
# =========================

# Reads data json. Data in this json is set by the game developers, read-only.
try:
    with open('data.json', 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: data.json not found. Please ensure the game data file exists.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: data.json is not valid JSON ({e}).")
    sys.exit(1)

# Uses data json to define several dictionaries containing game data, read-only.
required_keys = ['model', 'manufacture', 'staff', 'guest', 'monthData']
for k in required_keys:
    if k not in data:
        print(f"Error: data.json missing required key '{k}'.")
        sys.exit(1)

model = data['model']
manufacture = data['manufacture']
staff = data['staff']
guest = data['guest']
monthData = data['monthData']

# Ensure monthData contains entries for all expected months; warn if any are missing.
for mname in monthData.keys():
    if 'guestBonus' not in monthData[mname]:
        print(f"Warning: monthData entry for '{mname}' missing 'guestBonus'. Using fallback of 1.0.")
        monthData[mname]['guestBonus'] = 1.0

# =========================
# ======= HELPERS =========
# =========================

# Completely clears the terminal
def clear_screen():
    cmd = 'cls' if sys.platform.startswith('win') else 'clear'
    subprocess.run(cmd, shell=True)

# Limits any number to be between a minimum value and maximum value
def clamp_number(num, min_val, max_val):
    return max(min_val, min(num, max_val))


# Check if player already has a save
def save_check():
    global saveFile

    # Prompt player (yes or no)
    choice = input("Do you have a save file? Y/N --> ").strip().lower()

    match choice:
        # Yes, they have a file. Try to open file.
        case "y" | "yes":
            try:
                with open('save.json', 'r') as file:
                    saveFile = json.load(file)
            except FileNotFoundError:
                print("No save.json found. Creating a new save instead.")
                _create_new_save()

        # No, they don't have a file. Create new file, ask player for their name and park name.
        case "n" | "no":
            _create_new_save()

        # Invalid input, retry
        case _:
            print("Please enter Y or N.")
            save_check()


# Helper to create a new save file
def _create_new_save():
    global saveFile, month
    saveFile['name'] = input("What is your name? --> ").strip()
    saveFile['pname'] = input("Name your theme park --> ").strip()
    saveFile['money'] = 1_000_000
    saveFile['reputation'] = 0.0      # range: -100.0 to +100.0
    saveFile['advertising'] = 1.0     # min of 1, max of 100.0
    saveFile['rides'] = {}
    # Initialize current date properly
    get_date()


# Write saveFile dictionary to save json file
def export_save():
    try:
        with open("save.json", "w") as f:
            json.dump(saveFile, f, indent=2)
        print("Game saved.")
    except Exception as e:
        print(f"Error saving game: {e}")



# =========================
# ===== GAME HANDLER ======
# =========================

def get_date():
    """
    Increment the month counter and update saveFile['currentDate'].
    Uses monthData keys to determine month names instead of a fixed mList.
    """
    # If no currentDate yet, start at month 0 (before Jan 1980)
    if "currentDate" not in saveFile:
        saveFile["currentDate"] = {"month": 0}

    saveFile["currentDate"]["month"] += 1
    m = saveFile["currentDate"]["month"]

    # Use monthData keys as the authoritative month list
    month_names = list(monthData.keys())
    mReal = ((m - 1) % len(month_names)) + 1
    mName = month_names[mReal - 1]
    y = (m - 1) // len(month_names) + 1980
    guestBonus = monthData.get(mName, {}).get('guestBonus', 1.0)

    saveFile['currentDate'].update({
        "real": mReal,
        "name": mName,
        "year": y,
        "guestBonus": guestBonus
    })






def simulate():
    """
    Run one month of guest simulation.
    """
    # Calculate guest count based on reputation, advertising, and seasonal bonus
    currentMonth = saveFile['currentDate']['name']
    guestsCount = math.floor(
        (saveFile['reputation'] + 100) *
        saveFile['advertising'] *
        monthData.get(currentMonth, {}).get('guestBonus', 1.0)
    )

    # Weighted random selection of guest types
    guest_types = list(guest.keys())
    guest_weights = [guest[g]['weight'] for g in guest_types]
    guestList = random.choices(guest_types, guest_weights, k=guestsCount)

    # Loop for all guests in simulation this month
    for gType in guestList:
        gData = guest[gType]

        # Random time in park (minutes) and hunger stats
        timeInPark = random.randint(120, 480)
        hunger = 0
        hungerClock = 0

        while timeInPark > 0:
            # Hunger clock increments
            if hungerClock >= 30:
                hunger += random.randint(0, 1)
                hungerClock = 0

            # If guest is hungry, eat and reset hunger
            if hunger >= 5:
                hunger = 0
                # eating consumes some time
                timeInPark -= 30
                continue

            # Guest chooses a RANDOM ride from built rides
            if not saveFile['rides']:
                # no rides built, guest leaves after wasting time
                timeInPark -= 30
                continue

            ride_name = random.choice(list(saveFile['rides'].keys()))
            rideData = saveFile['rides'][ride_name]

            # Base chance from excitement points
            chanceToRide = rideData.get("excitementPoints", 0)

            # Intensity preference check
            intensity = rideData.get("intensityPoints", 0)
            pref_low, pref_high = gData.get('intensityPreference', (0, 100))
            if intensity < pref_low or intensity > pref_high:
                chanceToRide *= (2/3)

            # Age preference check
            agePref = gData.get('ageTolerance', 0)
            if rideData.get('age', 0) > agePref:
                divisor = clamp_number(
                    0.1 * (rideData['age'] - agePref) + 1,
                    1, 5
                )
                chanceToRide /= divisor

            # Price tolerance check
            priceTol = gData.get('priceTolerance', 999999)
            if rideData.get('price', 0) > priceTol:
                divisor = 0.5 * (
                    rideData['price'] - priceTol - rideData.get('themePoints', 0)
                ) + 1
                chanceToRide /= max(divisor, 1)

            # Manufacturer multiplier
            manuf = rideData.get('manufacturer')
            if manuf and manuf in manufacture:
                chanceToRide *= manufacture[manuf]['qMult']

            # Capacity check
            if rideData.get('ridersThisMonth', 0) > rideData.get('monthlyCapacity', 999999):
                chanceToRide *= 0.25

            # Roll random to determine if this guest rides
            if chanceToRide > random.randint(0, 100):
                # Ride, spend 15–45 mins, add to ride stats
                timeSpent = random.randint(15, 45)
                timeInPark -= timeSpent
                hungerClock += timeSpent
                rideData['ridersThisMonth'] = rideData.get('ridersThisMonth', 0) + 1
            else:
                # Do nothing, waste 5 minutes
                timeInPark -= 5
                hungerClock += 5



# =========================
# ===== BUILD COASTER =====
# =========================

def build_coaster():
    global saveFile

    # Step 1: Select coaster type
    model_menu = TerminalMenu(
        menu_entries=list(model.keys()),
        title="Select what model you'd like to build.",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True
    )
    model_sel = model_menu.show()
    selected_model = list(model.keys())[model_sel]
    model_data = model[selected_model]

    # Step 2: Select manufacturer
    manuf_entries = [f"{m} (Qmult: {manufacture[m]['qMult']})" for m in manufacture]
    manuf_menu = TerminalMenu(
        menu_entries=manuf_entries,
        title="Select a manufacturer.",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True
    )
    manuf_sel = manuf_menu.show()
    selected_manuf = list(manufacture.keys())[manuf_sel]
    manuf_qmult = manufacture[selected_manuf]['qMult']

    # Step 3: Allocate size points
    try:
        size_money = int(input("Enter money to spend on SIZE --> ").strip())
    except ValueError:
        print("Invalid input. Defaulting to 0.")
        size_money = 0
    size_points = size_money // 1000  # placeholder conversion
    print(f"Size points: {size_points}")

    # Step 4: Allocate intensity, theming, excitement (capped by size)
    def allocate_points(prompt_text):
        try:
            money = int(input(prompt_text).strip())
        except ValueError:
            print("Invalid input. Defaulting to 0.")
            money = 0
        return min(money // 1000, size_points)

    intensity_points = allocate_points("Enter money to spend on INTENSITY --> ")
    print(f"Intensity points: {intensity_points} (capped at {size_points})")

    theme_points = allocate_points("Enter money to spend on THEMEING --> ")
    print(f"Theming points: {theme_points} (capped at {size_points})")

    excite_points = allocate_points("Enter money to spend on EXCITEMENT --> ")
    print(f"Excitement points: {excite_points} (capped at {size_points})")

    # Step 5: Name the ride
    ride_name = input("What would you like to call your new ride? --> ").strip()

    # Store ride stats in saveFile
    saveFile['rides'][ride_name] = {
        "model": selected_model,
        "manufacturer": selected_manuf,
        "qMult": manuf_qmult,
        "yearDeveloped": model_data['yearDeveloped'],
        "lifeSpan": model_data['lifeSpan'],
        "payroll": model_data['payroll'],
        "sizePoints": size_points,
        "intensityPoints": intensity_points,
        "themePoints": theme_points,
        "excitementPoints": excite_points,
        "age": 0,
        "price": 0,
        "ridersThisMonth": 0,
        "monthlyCapacity": size_points * 100  # placeholder throughput scaling
    }

    print(f"Ride '{ride_name}' built successfully!")


def build_flat_ride():
    # Placeholder for flat ride builder
    pass





# =========================
# ======= UI SYSTEM =======
# =========================

def playerTab():
    print("------------------------------------------------------")
    print(f"Player Name: {saveFile.get('name', 'Unknown')}")
    print(f"Park Name: {saveFile.get('pname', 'Unnamed Park')}")
    print(f"Money: {saveFile.get('money', 0)}")
    print(f"Reputation: {saveFile.get('reputation', 0.0)}")
    print(f"Advertising Budget: {saveFile.get('advertising', 1.0)}")
    print("------------------------------------------------------")
    _ = input("Press Enter to continue...")


def parkTab():
    tab_menu = TerminalMenu(
        menu_entries=["Overview", "Back"],
        title=f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} |",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True
    )
    tab_sel = tab_menu.show()
    if tab_sel == 0:
        print("------------------------------------------------------")
        print(f"Park: {saveFile.get('pname', 'Unnamed Park')}")
        print(f"Money: {saveFile.get('money', 0)}")
        print(f"Reputation: {saveFile.get('reputation', 0.0)}")
        print(f"Advertising Budget: {saveFile.get('advertising', 1.0)}")
        print(f"Rides Built: {len(saveFile.get('rides', {}))}")
        print("------------------------------------------------------")
        _ = input("Press Enter to continue...")


def rideTab():
    ride_names = sorted(saveFile['rides'].keys())
    menu_entries = ['Build Coaster', 'Build Flat Ride'] + ride_names

    tab_menu = TerminalMenu(
        menu_entries=menu_entries,
        title=f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} |",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True,
        quit_keys=("escape", "backspace"),
    )

    tab_sel = tab_menu.show()

    if tab_sel == 0:
        build_coaster()
    elif tab_sel == 1:
        build_flat_ride()
    else:
        ride_name = ride_names[tab_sel - 2]
        ride_data = saveFile['rides'][ride_name]

        sub_entries = ["View Stats", "Adjust Price", "Close Ride", "Demolish Ride"]
        sub_menu = TerminalMenu(
            menu_entries=sub_entries,
            title=f"Manage Ride: {ride_name}",
            menu_cursor="> ",
            menu_cursor_style=("fg_red", "bold"),
            menu_highlight_style=("bg_gray", "bold"),
            cycle_cursor=True,
            clear_screen=True,
            quit_keys=("escape", "backspace"),
        )

        sub_sel = sub_menu.show()

        if sub_sel == 0:  # View Stats
            print("------------------------------------------------------")
            print(f"Ride Name: {ride_name}")
            for key, value in ride_data.items():
                print(f"{key}: {value}")
            print("------------------------------------------------------")
            _ = input("Press Enter to continue...")
        elif sub_sel == 1:  # Adjust Price
            pass
        elif sub_sel == 2:  # Close Ride
            pass
        elif sub_sel == 3:  # Demolish Ride
            pass


def foodTab(): pass
def carnivalTab(): pass
def commoditiesTab(): pass
def staffTab(): pass
def maintanenceTab(): pass
def advertisingTab(): pass
def realEstateTab(): pass
def stockTab(): pass

def settingTab():
    settings_menu = TerminalMenu(
        menu_entries=["Save Game", "Save & Exit", "Back"],
        title="Settings",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True
    )
    sel = settings_menu.show()
    if sel == 0:  # Save Game
        export_save()
        print("Saving successful.")
        _ = input("Press Enter to continue...")
    elif sel == 1:  # Save & Exit
        export_save()
        print("Saving successful. Exiting game...")
        sys.exit(0)
    # Back just returns


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
    global main_menu_exit

    main_menu = TerminalMenu(
        menu_entries=list(tabs.keys()) + ["End Month"],
        title=f"month {saveFile['currentDate']['month']} | {saveFile['currentDate']['name']} {saveFile['currentDate']['year']} | \n------------------------------------------------------\nSelect a tab, use arrow keys to navigate.",
        menu_cursor="> ",
        menu_cursor_style=("fg_red", "bold"),
        menu_highlight_style=("bg_gray", "bold"),
        cycle_cursor=True,
        clear_screen=True,
    )

    while True:
        main_sel = main_menu.show()
        if main_sel == len(tabs):  # End Month option
            break
        func = tabs[list(tabs.keys())[main_sel]]
        if func:
            func()

# =========================
# ======= ENTRY POINT =====
# =========================

if __name__ == "__main__":
    save_check()

    while True:
        # Update date (month increments inside get_date)
        get_date()

        # Run monthly simulation
        simulate()

        # Allow player to make changes until they end the month
        UI()

    # (Program ends only via Save & Exit in Settings)