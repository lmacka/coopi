import builtins
import subprocess
import logging
import threading
import json
import os
import time
from flask import Flask, render_template, request, redirect, url_for
from .door_state import is_door_open, is_door_state_running
from .door_control import open_door, close_door
from .config import SCHEDULEFILE, ACTUATETIME

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)


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
        with builtins.open(SCHEDULEFILE, encoding='utf-8') as f:
            return json.load(f)
    return {
        "open_time": "",
        "close_time": "",
        "open_enabled": False,
        "close_enabled": False,
    }


def save_schedule(schedule_data):
    with builtins.open(SCHEDULEFILE, "w", encoding='utf-8') as f:
        json.dump(schedule_data, f, ensure_ascii=False)


@app.route("/")
def home():
    door_open = is_door_open()
    door_state_running = is_door_state_running()
    schedule_data = load_schedule()
    return render_template(
        "index.html",
        door_open=door_open,
        door_state_running=door_state_running,
        schedule=schedule_data,
        actuate_time=ACTUATETIME
    )

@app.route("/open", methods=["POST"])
def open_door_route():
    if not is_door_state_running():
        subprocess.run(["python3", "door_control.py", "open"], check=True)
    return redirect(url_for("home"))


@app.route("/close", methods=["POST"])
def close_door_route():
    if not is_door_state_running():
        subprocess.run(["python3", "door_control.py", "close"], check=True)
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


if __name__ == "__main__":
    # Start the schedule checking thread
    schedule_thread = threading.Thread(target=check_schedule)
    schedule_thread.daemon = True
    schedule_thread.start()

    app.run(host="127.0.0.1", port=8086)
