import signal
import logging
import threading
import json
import os
import sys
import time
import RPi.GPIO
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
    while True:
        schedule_data = load_schedule()
        current_time = time.strftime("%H:%M")
        if schedule_data["open_enabled"] and schedule_data["open_time"] == current_time:
            logging.info("Opening door on schedule...")
            open_door()
        if schedule_data["close_enabled"] and schedule_data["close_time"] == current_time:
            logging.info("Closing door on schedule...")
            close_door()
        time.sleep(60)  # Check every minute


def load_schedule():
    if os.path.exists(SCHEDULEFILE):
        with open(SCHEDULEFILE, "r", encoding='utf-8') as schedule_file:
            return json.load(schedule_file)
    return []

def save_schedule(schedule_data):
    with open(SCHEDULEFILE, "w", encoding='utf-8') as schedule_file:
        json.dump(schedule_data, schedule_file, ensure_ascii=False)


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

def cleanup():
    if not getattr(cleanup, "done", False):
        print("Cleaning up GPIO and other resources...")
        RPi.GPIO.cleanup()
        # Perform any other necessary cleanup here
        cleanup.done = True

# Initialize the function attribute
cleanup.done = False

def signal_handler(_sig, _frame):
    cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if len(sys.argv) == 2:
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
            finally:
                for thread in threading.enumerate():
                    if thread is not threading.main_thread():
                        thread.join()
                cleanup()
        else:
            # Start the schedule checking thread
            schedule_thread = threading.Thread(target=check_schedule)
            schedule_thread.daemon = True
            schedule_thread.start()

            app.run(host="127.0.0.1", port=8086)
    finally:
        cleanup()
