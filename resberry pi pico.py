import network
import time
import urequests
from machine import Pin

# Wi-Fi credentials
# config_example.py

SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

FIREBASE_AMBULANCE_URL = "YOUR_FIREBASE_AMBLUNCE_URL"
FIREBASE_CONTROL_URL = "YOUR_FIREBASE_CONTROL_URL

# Traffic signal location
traffic_signal_lat = "YOUR_LAT"
traffic_signal_lon = "YOUR_LON"

# LED pin setup (common anode RGB)
led_pins = {
    1: (Pin(0, Pin.OUT), Pin(1, Pin.OUT), Pin(2, Pin.OUT)),
    2: (Pin(3, Pin.OUT), Pin(4, Pin.OUT), Pin(5, Pin.OUT)),
    3: (Pin(9, Pin.OUT), Pin(10, Pin.OUT), Pin(11, Pin.OUT)),  # Line 4
    4: (Pin(6, Pin.OUT), Pin(7, Pin.OUT), Pin(8, Pin.OUT))     # Line 3
}

# Set all LEDs red
def set_all_red():
    for red, green, blue in led_pins.values():
        red.value(0)
        green.value(1)
        blue.value(1)

# Turn selected LED green, rest red
def set_led_green(led_number):
    set_all_red()
    red, green, blue = led_pins[led_number]
    red.value(1)
    green.value(0)
    blue.value(1)

# LED cycling (used for idle/fallback)
def cycle_leds():
    for i in range(1, 5):
        set_led_green(i)
        time.sleep(1)

# Connect Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        cycle_leds()
    print("Connected to WiFi:", wlan.ifconfig()[0])

# Fetch control mode and command from Firebase
def get_control_data():
    try:
        response = urequests.get(FIREBASE_CONTROL_URL)
        control = response.json()
        response.close()
        return control.get("mode"), control.get("command")
    except Exception as e:
        print("Error fetching control:", e)
        return None, None

# Fetch ambulance GPS location from Firebase
def get_gps_data():
    try:
        response = urequests.get(FIREBASE_AMBULANCE_URL)
        data = response.json()
        response.close()
        return float(data["lat"]), float(data["lon"])
    except Exception as e:
        print("Error fetching GPS:", e)
        return None, None

# Determine LED based on location
def decide_led(lat, lon):
    if lat > traffic_signal_lat and abs(lon - traffic_signal_lon) <= 0.0001:
        return 1
    elif lon > traffic_signal_lon and abs(lat - traffic_signal_lat) <= 0.0001:
        return 2
    elif lon < traffic_signal_lon and abs(lat - traffic_signal_lat) <= 0.0001:
        return 4
    else:
        return 3

# --- MAIN PROGRAM ---
connect_wifi()

last_command = None
last_mode = None
last_auto_led = None
last_manual_command = None
gps_last_change_time = time.time()
gps_last_coords = (None, None)

while True:
    mode, command = get_control_data()

    if mode == "manual":
        if command != last_manual_command:
            print("Manual command changed:", command)
            if command == "line1":
                set_led_green(1)
            elif command == "line2":
                set_led_green(2)
            elif command == "line3":
                set_led_green(4)
            elif command == "line4":
                set_led_green(3)
            elif command == "cycling":
                print("Cycling LEDs (manual)")
                cycle_leds()
            last_manual_command = command

        # Hold the current manual state unless command changes
        time.sleep(1)

    elif mode == "automatic":
        lat, lon = get_gps_data()
        if lat is None or lon is None:
            print("GPS data unavailable. Cycling.")
            cycle_leds()
            continue

        # If location changed, update LED
        if (lat, lon) != gps_last_coords:
            matched_led = decide_led(lat, lon)
            set_led_green(matched_led)
            gps_last_coords = (lat, lon)
            gps_last_change_time = time.time()
            last_auto_led = matched_led
            print("Auto mode - LED", matched_led)
            time.sleep(10)  # Hold green for 10s

        elif time.time() - gps_last_change_time >= 10:
            print("No GPS change for 10s, cycling.")
            cycle_leds()

    else:
        print("Unknown mode or command. Cycling.")
        cycle_leds()

