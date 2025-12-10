# =========================
# ======= IMPORTS =========
# =========================

import sys, subprocess, json, math, random, time, threading, collections, html, copy, statistics

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button


# =========================
# ======= GLOBALS =========
# =========================

# Stores all active game data
saveFile = {}


# =========================
# ====== LOAD DATA ========
# =========================

try:
    with open('data.json', 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: data.json not found. Please ensure the game data file exists.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: data.json is not valid JSON ({e}).")
    sys.exit(1)

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


# =========================
# ======= HELPERS =========
# =========================

def clamp_number(num, min_val, max_val):
    return max(min_val, min(num, max_val))

def save_check():
    global saveFile
    choice = input("Do you have a save file? Y/N --> ").strip().lower()
    match choice:
        case "y" | "yes":
            try:
                with open('save.json', 'r') as file:
                    saveFile = json.load(file)
            except FileNotFoundError:
                print("No save.json found. Creating a new save instead.")
                _create_new_save()
        case "n" | "no":
            _create_new_save()
        case _:
            print("Please enter Y or N.")
            save_check()

def _create_new_save():
    global saveFile
    saveFile['name'] = input("What is your name? --> ").strip()
    saveFile['pname'] = input("Name your theme park --> ").strip()
    saveFile['money'] = 1_000_000
    saveFile['reputation'] = 0.0
    saveFile['advertising'] = 1.0
    saveFile['rides'] = {}
    get_date()





def export_save():
    """Non-blocking save function for Textual UI.
       Writes saveFile to disk and returns a status message."""
    try:
        with open("save.json", "w") as f:
            json.dump(saveFile, f, indent=2)
        return "Saving successful."
    except Exception as e:
        return f"Error saving game: {e}"



# =========================
# ===== GAME HANDLER ======
# =========================

def get_date():
    if "currentDate" not in saveFile:
        saveFile["currentDate"] = {"month": 0}
    saveFile["currentDate"]["month"] += 1
    m = saveFile["currentDate"]["month"]

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
    currentMonth = saveFile['currentDate']['name']
    guestsCount = math.floor(
        (saveFile['reputation'] + 100) *
        saveFile['advertising'] *
        monthData.get(currentMonth, {}).get('guestBonus', 1.0)
    )
    guest_types = list(guest.keys())
    guest_weights = [guest[g]['weight'] for g in guest_types]
    guestList = random.choices(guest_types, guest_weights, k=guestsCount)
    for gType in guestList:
        gData = guest[gType]
        timeInPark = random.randint(120, 480)
        hunger = 0
        hungerClock = 0
        while timeInPark > 0:
            if hungerClock >= 30:
                hunger += random.randint(0, 1)
                hungerClock = 0
            if hunger >= 5:
                hunger = 0
                timeInPark -= 30
                continue
            if not saveFile['rides']:
                timeInPark -= 30
                continue
            ride_name = random.choice(list(saveFile['rides'].keys()))
            rideData = saveFile['rides'][ride_name]
            chanceToRide = rideData.get("excitementPoints", 0)
            intensity = rideData.get("intensityPoints", 0)
            pref_low, pref_high = gData.get('intensityPreference', (0, 100))
            if intensity < pref_low or intensity > pref_high:
                chanceToRide *= (2/3)
            agePref = gData.get('ageTolerance', 0)
            if rideData.get('age', 0) > agePref:
                divisor = clamp_number(0.1 * (rideData['age'] - agePref) + 1, 1, 5)
                chanceToRide /= divisor
            priceTol = gData.get('priceTolerance', 999999)
            if rideData.get('price', 0) > priceTol:
                divisor = 0.5 * (rideData['price'] - priceTol - rideData.get('themePoints', 0)) + 1
                chanceToRide /= max(divisor, 1)
            manuf = rideData.get('manufacturer')
            if manuf and manuf in manufacture:
                chanceToRide *= manufacture[manuf]['qMult']
            if rideData.get('ridersThisMonth', 0) > rideData.get('monthlyCapacity', 999999):
                chanceToRide *= 0.25
            if chanceToRide > random.randint(0, 100):
                timeSpent = random.randint(15, 45)
                timeInPark -= timeSpent
                hungerClock += timeSpent
                rideData['ridersThisMonth'] = rideData.get('ridersThisMonth', 0) + 1
            else:
                timeInPark -= 5
                hungerClock += 5



# =========================
# ===== BUILD COASTER =====
# =========================

def build_coaster():
    """Non-blocking coaster builder for Textual UI.
       Creates a placeholder ride with default stats."""
    global saveFile

    ride_name = f"Coaster_{len(saveFile.get('rides', {})) + 1}"

    saveFile['rides'][ride_name] = {
        "model": "Default",
        "manufacturer": "Default",
        "qMult": 1.0,
        "yearDeveloped": 1980,
        "lifeSpan": 20,
        "payroll": 1000,
        "sizePoints": 10,
        "intensityPoints": 5,
        "themePoints": 5,
        "excitementPoints": 5,
        "age": 0,
        "price": 0,
        "ridersThisMonth": 0,
        "monthlyCapacity": 1000
    }

    return f"Ride '{ride_name}' built successfully!"


def build_flat_ride():
    """Placeholder for flat ride builder."""
    return "Flat ride builder not yet implemented."





# =========================
# ======= TEXTUAL UI ======
# =========================

class ThemeParkApp(App):
    CSS_PATH = "main.css"

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left pane: scrollable main content
            with ScrollableContainer(id="left-pane"):
                yield Vertical(id="main-content")

            # Right side split vertically
            with Vertical(id="right-pane"):
                # Top right: scrollable tab buttons (fixed height via CSS fr)
                with ScrollableContainer(id="tab-pane"):
                    yield Vertical(id="tab-buttons")
                # Bottom right: scrollable info panel
                with ScrollableContainer(id="info-pane"):
                    yield Static("Park Info:\nMoney: 0\nReputation: 0", id="info-content")

    def on_mount(self) -> None:
        self.show_main_tabs()
        self.update_info_panel()

    def show_main_tabs(self) -> None:
        buttons = self.query_one("#tab-buttons", Vertical)
        buttons.remove_children()
        for tab in ["Player Information", "Park Information", "Rides", "Settings"]:
            safe_id = "tab_" + tab.replace(" ", "_").lower()
            buttons.mount(Button(tab, id=safe_id))
        buttons.mount(Button("End Month", id="end_month"))
        # If you want to verify scrolling, uncomment the next line to add many buttons:
        # buttons.mount_all(*(Button(f"Extra {i}", id=f"tab_extra_{i}") for i in range(1, 31)))

    def show_sub_tabs(self, tab_name: str) -> None:
        buttons = self.query_one("#tab-buttons", Vertical)
        buttons.remove_children()
        if tab_name == "Rides":
            for sub in ["Build Coaster", "Build Flat Ride", "Manage Rides"]:
                buttons.mount(Button(sub, id="sub_" + sub.replace(" ", "_").lower()))
        elif tab_name == "Settings":
            for sub in ["Save Game", "Save & Exit"]:
                buttons.mount(Button(sub, id="sub_" + sub.replace(" ", "_").replace("&", "and").lower()))
        buttons.mount(Button("Back", id="back"))

    def update_info_panel(self) -> None:
        money = saveFile.get("money", 0)
        rep = saveFile.get("reputation", 0)
        month = saveFile.get("currentDate", {}).get("month", 0)
        year = saveFile.get("currentDate", {}).get("year", 1980)
        info_text = (
            f"Park Info:\n"
            f"Money: {money}\n"
            f"Reputation: {rep}\n"
            f"Month: {month}\n"
            f"Year: {year}"
        )
        self.query_one("#info-content", Static).update(info_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("tab_"):
            tab_name = btn_id.replace("tab_", "").replace("_", " ").title()
            self.show_sub_tabs(tab_name)
        elif btn_id == "back":
            self.show_main_tabs()
        elif btn_id == "end_month":
            get_date()
            simulate()
            self.query_one("#main-content", Vertical).mount(
                Static(
                    f"Month {saveFile['currentDate']['month']} ended. Current date: "
                    f"{saveFile['currentDate']['name']} {saveFile['currentDate']['year']}"
                )
            )
            self.update_info_panel()
        elif btn_id == "sub_build_coaster":
            msg = build_coaster()
            self.query_one("#main-content", Vertical).mount(Static(msg))
            self.update_info_panel()
        elif btn_id == "sub_build_flat_ride":
            msg = build_flat_ride()
            self.query_one("#main-content", Vertical).mount(Static(msg))
        elif btn_id == "sub_manage_rides":
            rides = saveFile.get("rides", {})
            text = "Rides:\n" + "\n".join(rides.keys()) if rides else "No rides built yet."
            self.query_one("#main-content", Vertical).mount(Static(text))
        elif btn_id == "sub_save_game":
            msg = export_save()
            self.query_one("#main-content", Vertical).mount(Static(msg))
        elif btn_id == "sub_save_and_exit":
            msg = export_save()
            self.query_one("#main-content", Vertical).mount(Static(msg + " Exiting game..."))
            self.exit()
           

# =========================
# ======= ENTRY POINT =====
# =========================

if __name__ == "__main__":
    # Ensure save file exists or create a new one
    save_check()

    # Launch the Textual UI
    app = ThemeParkApp()
    app.run()

    # (Program ends only via Save & Exit in Settings or closing the UI)