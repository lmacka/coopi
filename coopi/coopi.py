import signal
import logging
import threading
import json
import os
import sys
import time
from datetime import datetime
import RPi.GPIO
import requests
import pytz
from flask import Flask, render_template, request, redirect, url_for

# Configuration
ACTUATETIME = 90
RELAY1_PIN = 14
RELAY2_PIN = 15
STATEFILE = "var/state.json"
SCHEDULEFILE = "var/schedule.json"

# Initialize GPIO pins
def init_gpio():
    RPi.GPIO.setmode(RPi.GPIO.BCM)
    RPi.GPIO.setup(RELAY1_PIN, RPi.GPIO.OUT)
    RPi.GPIO.setup(RELAY2_PIN, RPi.GPIO.OUT)

# Call the initialization functions when the module is loaded
init_gpio()

# Define a threading lock to prevent concurrent operations
lock = threading.Lock()

# Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Fetch the local timezone using ipinfo.io
def fetch_timezone():
    try:
        response = requests.get("http://ipinfo.io/timezone", timeout=10)
        if response.status_code == 200:
            return response.text.strip()
        logging.error("Failed to fetch timezone: %s", response.status_code)
        return "UTC"
    except requests.RequestException as e:
        logging.error("Exception occurred while fetching timezone: %s", e)
        return "UTC"

# Set the local timezone
LOCAL_TIMEZONE = fetch_timezone()
logging.info("Detected local timezone: %s", LOCAL_TIMEZONE)
local_tz = pytz.timezone(LOCAL_TIMEZONE)

# Ensure the state file exists with a default state
if not os.path.exists(STATEFILE):
    with open(STATEFILE, "w", encoding='utf-8') as initial_state_file:
        json.dump({"state": "closed"}, initial_state_file, ensure_ascii=False)

# Ensure the schedule file exists with a default schedule
if not os.path.exists(SCHEDULEFILE):
    with open(SCHEDULEFILE, "w", encoding='utf-8') as initial_schedule_file:
        json.dump(
            {
                "open_enabled": False,
                "open_time": "06:00",
                "close_enabled": False,
                "close_time": "18:00"
            },
            initial_schedule_file,
            ensure_ascii=False
        )

def open_door():
    with lock:
        RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.LOW)
        RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
        time.sleep(ACTUATETIME)
        with open(STATEFILE, "w", encoding='utf-8') as state_file:
            json.dump({"state": "open"}, state_file, ensure_ascii=False)
        # Reset both relays to NC state
        RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
        RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)

def close_door():
    with lock:
        RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
        RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.LOW)
        time.sleep(ACTUATETIME)
        with open(STATEFILE, "w", encoding='utf-8') as state_file:
            json.dump({"state": "closed"}, state_file, ensure_ascii=False)
        # Reset both relays to NC state
        RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
        RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
        return "Door closed"

def check_schedule():
    logging.info("Starting schedule check thread...")
    while True:
        schedule_data = load_schedule()
        current_time = datetime.now(local_tz).strftime("%H:%M")
        logging.debug("Current time: %s", current_time)
        logging.debug("Schedule data: %s", schedule_data)
        if schedule_data.get("open_enabled") and schedule_data.get("open_time") == current_time:
            logging.info("Opening door on schedule...")
            open_door()
        if schedule_data.get("close_enabled") and schedule_data.get("close_time") == current_time:
            logging.info("Closing door on schedule...")
            close_door()
        logging.debug("Sleeping for 60 seconds...")
        time.sleep(60)  # Check every minute

def load_schedule():
    if os.path.exists(SCHEDULEFILE):
        with open(SCHEDULEFILE, "r", encoding='utf-8') as schedule_file:
            schedule_data = json.load(schedule_file)
            return schedule_data
    return {}

def save_schedule(schedule_data):
    with open(SCHEDULEFILE, "w", encoding='utf-8') as schedule_file:
        json.dump(schedule_data, schedule_file, ensure_ascii=False)

def cleanup():
    if not getattr(cleanup, "done", False):
        print("Cleaning up GPIO...")
        RPi.GPIO.cleanup()
        cleanup.done = True

def signal_handler(_sig, _frame):
    cleanup()
    sys.exit(0)

@app.route("/")
def home():
    with open(STATEFILE, encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        doorstate = json_data["state"]
    schedule_data = load_schedule()
    return render_template(
        "index.html",
        schedule=schedule_data,
        actuate_time=ACTUATETIME,
        doorstate=doorstate
    )

@app.route("/open", methods=["POST"])
def open_door_route():
    open_door()
    return redirect(url_for("home"))

@app.route("/close", methods=["POST"])
def close_door_route():
    close_door()
    return redirect(url_for("home"))

@app.route("/schedule", methods=["POST"])
def schedule():
    schedule_data = {
        "open_time": request.form["open_time"],
        "close_time": request.form["close_time"],
        "open_enabled": "open_enabled" in request.form,
        "close_enabled": "close_enabled" in request.form,
    }
    save_schedule(schedule_data)
    return redirect(url_for("home"))

# Initialize the function attribute
cleanup.done = False

# Listen for signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    if len(sys.argv) > 2:
        print("Error: Only one argument is allowed.")
        sys.exit(1)
    elif len(sys.argv) == 2:
        command = sys.argv[1]
        try:
            if command == "open":
                print(open_door())
            elif command == "close":
                print(close_door())
            else:
                print(f"Invalid command: {command}")
                sys.exit(1)
        except KeyboardInterrupt:
            pass
    else:
        # Start the schedule checking thread
        schedule_thread = threading.Thread(target=check_schedule)
        schedule_thread.daemon = True
        schedule_thread.start()

        app.run(host="0.0.0.0", port=8086)

if __name__ == "__main__":
    main()
elif __name__ == "coopi.coopi":
    # Start the schedule checking thread
    module_schedule_thread = threading.Thread(target=check_schedule)
    module_schedule_thread.daemon = True
    module_schedule_thread.start()
