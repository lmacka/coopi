import signal
import logging
import threading
import json
import os
import sys
import time
from datetime import datetime
import RPi.GPIO
import pytz
from flask import Flask, render_template, request, redirect, url_for, jsonify

# Configure logging for Balena
class BalenaFormatter(logging.Formatter):
    """Custom formatter that includes service name, timestamp and adds color for Balena dashboard"""
    
    def format(self, record):
        # Add service name and format for better visibility in Balena dashboard
        record.service = "coopi"
        
        # Color codes for different log levels
        colors = {
            'ERROR': '\033[91m',  # Red
            'WARNING': '\033[93m',  # Yellow
            'INFO': '\033[92m',  # Green
            'DEBUG': '\033[94m',  # Blue
            'CRITICAL': '\033[95m'  # Purple
        }
        
        reset_color = '\033[0m'
        color = colors.get(record.levelname, '')
        
        # Format with timestamp
        timestamp = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        return f"{color}{timestamp} [{record.service}] {record.levelname}: {record.getMessage()}{reset_color}"

# Configure logging
def setup_logging():
    """Setup logging configuration for Balena dashboard"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(BalenaFormatter())
    
    # Remove any existing handlers and add our custom handler
    logger.handlers = []
    logger.addHandler(console_handler)
    
    # Log startup message
    logging.info("Coopi service starting up")
    logging.info("Python version: %s", sys.version)
    logging.info("GPIO version: %s", RPi.GPIO.VERSION)
    return logger

# Initialize logging
logger = setup_logging()

# Configuration
ACTUATETIME = 90
RELAY1_PIN = 14
RELAY2_PIN = 15
# Use absolute paths in the data directory
DATA_DIR = "/data"
STATEFILE = os.path.join(DATA_DIR, "state.json")
SCHEDULEFILE = os.path.join(DATA_DIR, "schedule.json")
LOCAL_TIMEZONE = "Australia/Brisbane"

# Initialize GPIO pins with better logging
def init_gpio():
    try:
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        RPi.GPIO.setup(RELAY1_PIN, RPi.GPIO.OUT)
        RPi.GPIO.setup(RELAY2_PIN, RPi.GPIO.OUT)
        logging.info("GPIO pins initialized successfully: RELAY1=%d, RELAY2=%d", 
                    RELAY1_PIN, RELAY2_PIN)
    except Exception as e:
        logging.error("Failed to initialize GPIO: %s", e)
        raise

# Call the initialization functions when the module is loaded
init_gpio()

# Define a threading lock to prevent concurrent operations
lock = threading.Lock()

# Flask application
app = Flask(__name__)

# Verify and set the local timezone
def verify_timezone():
    try:
        # First try to get timezone from environment variable
        tz_name = os.getenv('TZ', LOCAL_TIMEZONE)
        timezone = pytz.timezone(tz_name)
        # Verify we can get the current time in this timezone
        current_time = datetime.now(timezone)
        # Verify by checking offset calculation
        offset = current_time.utcoffset()
        if offset is None:
            raise pytz.exceptions.UnknownTimeZoneError("Invalid timezone offset")
        logging.info("Verified timezone: %s", tz_name)
        logging.info("Current local time: %s", current_time)
        logging.info("UTC offset: %s", offset)
        return timezone
    except (pytz.exceptions.UnknownTimeZoneError, pytz.exceptions.InvalidTimeError) as e:
        logging.error("Invalid timezone: %s - %s", tz_name, str(e))
        # Fall back to UTC rather than exiting
        logging.warning("Falling back to UTC timezone")
        return pytz.UTC

# Verify and set the local timezone
local_tz = verify_timezone()

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

# Add directory creation
def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info("Created data directory at %s", DATA_DIR)

# Call it during initialization
ensure_data_directory()

def load_state():
    """Load the current state with error handling"""
    try:
        if os.path.exists(STATEFILE):
            with open(STATEFILE, "r", encoding='utf-8') as state_file:
                return json.load(state_file)
    except (IOError, json.JSONDecodeError) as e:
        logging.error("Error loading state file: %s", e)
    return {"state": "closed"}  # Default state

def save_state(state):
    """Save the state with error handling"""
    try:
        with open(STATEFILE, "w", encoding='utf-8') as state_file:
            json.dump(state, state_file, ensure_ascii=False)
    except IOError as e:
        logging.error("Error saving state file: %s", e)

# Update the door operations with better logging
def open_door():
    with lock:
        try:
            current_state = load_state()
            if current_state["state"] == "open":
                logging.info("Door is already open, skipping operation")
                return
                
            logging.info("Opening door")
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.LOW)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
            time.sleep(ACTUATETIME)
            save_state({"state": "open"})
            
            # Reset both relays to NC state
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
        except Exception as e:
            logging.error("Failed to open door: %s", e)
            raise

def close_door():
    with lock:
        try:
            current_state = load_state()
            if current_state["state"] == "closed":
                logging.info("Door is already closed, skipping operation")
                return
                
            logging.info("Closing door")
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.LOW)
            time.sleep(ACTUATETIME)
            save_state({"state": "closed"})
            
            # Reset both relays to NC state
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
        except Exception as e:
            logging.error("Failed to close door: %s", e)
            raise

def check_schedule():
    logging.info("Automatic schedule checker started")
    while True:
        try:
            schedule_data = load_schedule()
            current_time = datetime.now(local_tz).strftime("%H:%M")
            
            if schedule_data.get("open_enabled") and schedule_data.get("open_time") == current_time:
                logging.info("Automatically opening door (scheduled for %s)", current_time)
                open_door()
            
            if schedule_data.get("close_enabled") and schedule_data.get("close_time") == current_time:
                logging.info("Automatically closing door (scheduled for %s)", current_time)
                close_door()
            
            time.sleep(60)
            
        except Exception as e:
            logging.error("Schedule check error: %s", e)
            time.sleep(60)

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

@app.route('/')
def index():
    # Skip logging for healthcheck requests
    user_agent = request.headers.get('User-Agent', '')
    if 'curl' not in user_agent.lower():  # Only log non-healthcheck requests
        # Get client IP or hostname
        client = request.headers.get('X-Forwarded-For', request.remote_addr)
        logging.info("Web interface accessed from %s", client)
    
    # Get current door state
    with open(STATEFILE, "r", encoding='utf-8') as state_file:
        doorstate = json.load(state_file)["state"]

    # Get current schedule
    with open(SCHEDULEFILE, "r", encoding='utf-8') as schedule_file:
        schedule_data = json.load(schedule_file)

    # Get current time in configured timezone
    current_time = datetime.now(local_tz).strftime("%d/%m %I:%M %p %Z")

    return render_template('index.html',
                         doorstate=doorstate,
                         schedule=schedule_data,
                         current_time=current_time,
                         actuate_time=ACTUATETIME)

@app.route("/open", methods=["POST"])
def open_door_route():
    logging.info("Opening door from web interface")
    open_door()
    return jsonify({"status": "success"})

@app.route("/close", methods=["POST"])
def close_door_route():
    logging.info("Closing door from web interface")
    close_door()
    return jsonify({"status": "success"})

@app.route("/schedule", methods=["POST"])
def update_schedule():
    old_schedule = load_schedule()
    schedule_data = {
        "open_time": request.form["open_time"],
        "close_time": request.form["close_time"],
        "open_enabled": "open_enabled" in request.form,
        "close_enabled": "close_enabled" in request.form,
    }
    
    # Log only actual changes with clearer messages
    if old_schedule.get("open_enabled") != schedule_data["open_enabled"]:
        status = "enabled" if schedule_data["open_enabled"] else "disabled"
        logging.info("Automatic door opening %s for %s", 
                    status, schedule_data["open_time"])
    
    if old_schedule.get("close_enabled") != schedule_data["close_enabled"]:
        status = "enabled" if schedule_data["close_enabled"] else "disabled"
        logging.info("Automatic door closing %s for %s", 
                    status, schedule_data["close_time"])
    
    if old_schedule.get("open_time") != schedule_data["open_time"]:
        logging.info("Automatic opening time set to %s", schedule_data["open_time"])
    
    if old_schedule.get("close_time") != schedule_data["close_time"]:
        logging.info("Automatic closing time set to %s", schedule_data["close_time"])
    
    save_schedule(schedule_data)
    return redirect(url_for("index"))

# Initialize the function attribute
cleanup.done = False

# Listen for signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def print_help():
    help_message = """
Usage: python coopi.py [OPTION]
Control the coop door or run the web UI with scheduling functionality.

Options:
  open         Open the coop door
  close        Close the coop door
  server       Run the web server with scheduling (default if no option is provided)
  -h, --help   Display this help message

Examples:
  python coopi.py open
  python coopi.py close
  python coopi.py server
"""
    print(help_message)

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0)
    elif len(sys.argv) == 2:
        command = sys.argv[1]
        try:
            if command == "open":
                print(open_door())
            elif command == "close":
                print(close_door())
            elif command == "server":
                # Start the schedule checking thread
                schedule_thread = threading.Thread(target=check_schedule)
                schedule_thread.daemon = True
                schedule_thread.start()
                app.run(host="0.0.0.0", port=8086)
            else:
                print(f"Invalid command: {command}")
                print_help()
                sys.exit(1)
        except KeyboardInterrupt:
            pass
    else:
        print("Error: Too many arguments.")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
elif __name__ == "coopi.coopi":
    # Start the schedule checking thread
    module_schedule_thread = threading.Thread(target=check_schedule)
    module_schedule_thread.daemon = True
    module_schedule_thread.start()
