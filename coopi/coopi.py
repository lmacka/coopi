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
import paho.mqtt.client as mqtt

# Configuration
ACTUATETIME = 90
RELAY1_PIN = 14
RELAY2_PIN = 15
DATA_DIR = "/data"
STATEFILE = os.path.join(DATA_DIR, "state.json")
SCHEDULEFILE = os.path.join(DATA_DIR, "schedule.json")
LOCAL_TIMEZONE = "Australia/Brisbane"
MQTTCONFIGFILE = os.path.join(DATA_DIR, "mqtt.json")
MQTT_UNIQUE_ID = "coopi_coop_door"

# MQTT runtime state. Populated by start_mqtt() only when a broker is configured; while the
# "client" key is absent every publish helper is a no-op, so the app behaves exactly as
# before when the Home Assistant integration is not set up.
mqtt_state = {}

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
        
        # Format with timestamp using UTC (we'll convert to local time after timezone is verified)
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return f"{color}{timestamp} [{record.service}] {record.levelname}: {record.getMessage()}{reset_color}"

def get_logger():
    """Setup logging configuration for Balena dashboard"""
    app_logger = logging.getLogger()
    app_logger.setLevel(logging.INFO)
    
    # Console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(BalenaFormatter())
    
    # Remove any existing handlers and add our custom handler
    app_logger.handlers = []
    app_logger.addHandler(console_handler)
    
    # Log startup message
    app_logger.info("Coopi service starting up")
    app_logger.info("Python version: %s", sys.version)
    app_logger.info("GPIO version: %s", RPi.GPIO.VERSION)
    return app_logger

# Initialize logging first
logger = get_logger()

# Initialize GPIO pins with better logging


def init_gpio():
    try:
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        RPi.GPIO.setup(RELAY1_PIN, RPi.GPIO.OUT)
        RPi.GPIO.setup(RELAY2_PIN, RPi.GPIO.OUT)
        logging.info(
            "GPIO pins initialized successfully: RELAY1=%d, RELAY2=%d",
            RELAY1_PIN,
            RELAY2_PIN)
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
        logger.info("Verified timezone: %s", tz_name)
        logger.info("Current local time: %s", current_time)
        logger.info("UTC offset: %s", offset)
        return timezone
    except (pytz.exceptions.UnknownTimeZoneError, pytz.exceptions.InvalidTimeError) as e:
        logger.error("Invalid timezone: %s - %s", tz_name, str(e))
        # Fall back to UTC rather than exiting
        logger.warning("Falling back to UTC timezone")
        return pytz.UTC

# Initialize timezone after logging is set up
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
                publish_door_state("open")
                return

            logging.info("Opening door")
            publish_door_state("opening")
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.LOW)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
            time.sleep(ACTUATETIME)
            save_state({"state": "open"})

            # Reset both relays to NC state
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
            publish_door_state("open")
        except Exception as e:
            logging.error("Failed to open door: %s", e)
            raise


def close_door():
    with lock:
        try:
            current_state = load_state()
            if current_state["state"] == "closed":
                logging.info("Door is already closed, skipping operation")
                publish_door_state("closed")
                return

            logging.info("Closing door")
            publish_door_state("closing")
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.LOW)
            time.sleep(ACTUATETIME)
            save_state({"state": "closed"})

            # Reset both relays to NC state
            RPi.GPIO.output(RELAY1_PIN, RPi.GPIO.HIGH)
            RPi.GPIO.output(RELAY2_PIN, RPi.GPIO.HIGH)
            publish_door_state("closed")
        except Exception as e:
            logging.error("Failed to close door: %s", e)
            raise


def check_schedule():
    """Check and execute scheduled door operations"""
    logger.info("Automatic schedule checker started")
    while True:
        try:
            schedule_data = load_schedule()
            current_time = datetime.now(local_tz).strftime("%H:%M")

            if schedule_data.get("open_enabled") and schedule_data.get("open_time") == current_time:
                logger.info("Automatically opening door (scheduled for %s)", current_time)
                open_door()

            if schedule_data.get("close_enabled") and schedule_data.get("close_time") == current_time:
                logger.info("Automatically closing door (scheduled for %s)", current_time)
                close_door()

            time.sleep(60)

        except (IOError, json.JSONDecodeError, RPi.GPIO.error) as e:
            logger.error("Schedule check error: %s", e)
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


def load_mqtt_config():
    """Build MQTT config from environment variables, falling back to /data/mqtt.json.

    Environment variables win; the file fills any gaps. Returns the config dict when a
    broker host is configured, otherwise None (Home Assistant integration disabled).
    """
    cfg = {
        "host": os.getenv("MQTT_HOST"),
        "port": os.getenv("MQTT_PORT"),
        "user": os.getenv("MQTT_USER"),
        "password": os.getenv("MQTT_PASS"),
        "base_topic": os.getenv("MQTT_BASE_TOPIC"),
        "discovery_prefix": os.getenv("MQTT_DISCOVERY_PREFIX"),
    }
    if os.path.exists(MQTTCONFIGFILE):
        try:
            with open(MQTTCONFIGFILE, "r", encoding="utf-8") as cfg_file:
                file_cfg = json.load(cfg_file)
            for key, value in file_cfg.items():
                if cfg.get(key) is None:
                    cfg[key] = value
        except (IOError, json.JSONDecodeError) as exc:
            logging.error("Error reading MQTT config file: %s", exc)
    if not cfg.get("host"):
        return None
    cfg["port"] = int(cfg.get("port") or 1883)
    cfg["base_topic"] = cfg.get("base_topic") or "coopi/coop_door"
    cfg["discovery_prefix"] = cfg.get("discovery_prefix") or "homeassistant"
    return cfg


def mqtt_topic(suffix):
    """Return the full topic for the given suffix under the configured base topic."""
    return f"{mqtt_state['cfg']['base_topic']}/{suffix}"


def publish_door_state(state):
    """Publish the cover state (open/opening/closed/closing) to HA, retained.

    No-op when MQTT is disabled, so the door functions are safe to call either way.
    """
    client = mqtt_state.get("client")
    if client is not None:
        client.publish(mqtt_topic("state"), state, qos=1, retain=True)


def publish_discovery():
    """Publish the Home Assistant MQTT discovery config for the coop door cover, retained."""
    cfg = mqtt_state["cfg"]
    topic = f"{cfg['discovery_prefix']}/cover/{MQTT_UNIQUE_ID}/config"
    payload = {
        "name": "Coop Door",
        "unique_id": MQTT_UNIQUE_ID,
        "device_class": "garage",
        "command_topic": mqtt_topic("set"),
        "state_topic": mqtt_topic("state"),
        "availability_topic": mqtt_topic("availability"),
        "payload_open": "OPEN",
        "payload_close": "CLOSE",
        "state_open": "open",
        "state_opening": "opening",
        "state_closed": "closed",
        "state_closing": "closing",
        "optimistic": False,
        "device": {
            "identifiers": [MQTT_UNIQUE_ID],
            "name": "Coop Door",
            "manufacturer": "lmacka",
            "model": "coopi",
        },
    }
    mqtt_state["client"].publish(topic, json.dumps(payload), qos=1, retain=True)


def on_mqtt_connect(client, _userdata, _flags, reason_code, _properties):
    """Publish availability, discovery and current state, then subscribe to commands."""
    if reason_code != 0:
        logging.error("MQTT connection failed: %s", reason_code)
        return
    client.publish(mqtt_topic("availability"), "online", qos=1, retain=True)
    publish_discovery()
    publish_door_state(load_state().get("state", "closed"))
    client.subscribe(mqtt_topic("set"), qos=1)
    logging.info("MQTT connected; published discovery and current state")


def on_mqtt_message(_client, _userdata, msg):
    """Handle an HA cover command by running the door operation on a worker thread.

    A worker thread is used so the blocking actuation never stalls the MQTT network loop.
    """
    command = msg.payload.decode("utf-8", "ignore").strip().upper()
    logging.info("MQTT command received: %s", command)
    if command == "OPEN":
        threading.Thread(target=open_door, daemon=True).start()
    elif command == "CLOSE":
        threading.Thread(target=close_door, daemon=True).start()
    else:
        logging.warning("Ignoring unknown MQTT command: %s", command)


def start_mqtt():
    """Start the MQTT client loop when a broker is configured; otherwise do nothing."""
    cfg = load_mqtt_config()
    if cfg is None:
        logging.info("MQTT not configured (no MQTT_HOST); Home Assistant integration disabled")
        return
    mqtt_state["cfg"] = cfg
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="coopi")
    if cfg.get("user"):
        client.username_pw_set(cfg["user"], cfg.get("password"))
    client.will_set(mqtt_topic("availability"), "offline", qos=1, retain=True)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    mqtt_state["client"] = client
    client.connect_async(cfg["host"], cfg["port"], keepalive=60)
    client.loop_start()
    logging.info("MQTT client started for broker %s:%s", cfg["host"], cfg["port"])


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
        logging.info(
            "Automatic opening time set to %s",
            schedule_data["open_time"])

    if old_schedule.get("close_time") != schedule_data["close_time"]:
        logging.info(
            "Automatic closing time set to %s",
            schedule_data["close_time"])

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
                start_mqtt()
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
    start_mqtt()
