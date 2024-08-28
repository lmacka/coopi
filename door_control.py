import sys
import threading
import time
import json
import os
from RPi import GPIO
from .config import RELAY1_PIN, RELAY2_PIN, STATEFILE, ACTUATETIME
from .door_state import set_door_state_running

# Set up GPIO mode to use Broadcom SOC channel numbers
GPIO.setmode(GPIO.BCM)

# Set up the GPIO pins as outputs
GPIO.setup(RELAY1_PIN, GPIO.OUT)
GPIO.setup(RELAY2_PIN, GPIO.OUT)

# Define a threading lock to prevent concurrent operations
lock = threading.Lock()

# Ensure the state file exists with a default state
if not os.path.exists(STATEFILE):
    with open(STATEFILE, "w", encoding='utf-8') as initial_state_file:
        json.dump({"state": "closed"}, initial_state_file, ensure_ascii=False)


def open_door():
    """
    Function to open the door.
    Checks the current state of the door and initiates the opening process if the door is closed.
    """
    # Check if another operation is in progress
    if lock.locked():
        return "Another operation is in progress"

    # Read the current state of the door from the state file
    with open(STATEFILE, encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        doorstate = json_data["state"]

    # If the door is closed, initiate the opening process
    if doorstate == "closed":
        # Update the state file to reflect the door is opening
        with open(STATEFILE, "w", encoding='utf-8') as state_file:
            json.dump({"state": "open"}, state_file, ensure_ascii=False)

        # Acquire the lock and start a new thread to handle the door opening
        lock.acquire()
        threading.Thread(target=delayed_open).start()
        return "Opening door. This will take " + str(ACTUATETIME) + " seconds"
    return "Door already open"


def close_door():
    """
    Function to close the door.
    Checks the current state of the door and initiates the closing process if the door is open.
    """
    # Check if another operation is in progress
    if lock.locked():
        return "Another operation is in progress"

    # Read the current state of the door from the state file
    with open(STATEFILE, encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        doorstate = json_data["state"]

    # If the door is open, initiate the closing process
    if doorstate == "open":
        # Update the state file to reflect the door is closing
        with open(STATEFILE, "w", encoding='utf-8') as state_file:
            json.dump({"state": "closed"}, state_file, ensure_ascii=False)

        # Acquire the lock and start a new thread to handle the door closing
        lock.acquire()
        threading.Thread(target=delayed_close).start()
        return "Closing door. This will take " + str(ACTUATETIME) + " seconds"
    return "Door already closed"


def delayed_open():
    """
    Function to handle the delayed opening of the door.
    Sets the GPIO pins to open the door for the specified actuation time.
    """
    set_door_state_running(True)
    start_time = time.time()
    while time.time() - start_time < ACTUATETIME:
        GPIO.output(RELAY1_PIN, GPIO.LOW)
        GPIO.output(RELAY2_PIN, GPIO.HIGH)
        time.sleep(0.1)  # Adjust the sleep time as needed
    # Release the lock after the operation is complete
    lock.release()
    set_door_state_running(False)


def delayed_close():
    """
    Function to handle the delayed closing of the door.
    Sets the GPIO pins to close the door for the specified actuation time.
    """
    set_door_state_running(True)
    start_time = time.time()
    while time.time() - start_time < ACTUATETIME:
        GPIO.output(RELAY1_PIN, GPIO.HIGH)
        GPIO.output(RELAY2_PIN, GPIO.LOW)
        time.sleep(0.1)  # Adjust the sleep time as needed
    # Release the lock after the operation is complete
    lock.release()
    set_door_state_running(False)


if __name__ == "__main__":
    # Ensure the script is called with the correct number of arguments
    if len(sys.argv) != 2:
        print("Script to open and close the door, for use with cron")
        print("Usage: python door_control.py <command>")
        print("<command> can be 'open' or 'close'")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command in ["open", "close"]:
            # Setup GPIO only when a valid command is received
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(RELAY1_PIN, GPIO.OUT)
            GPIO.setup(RELAY2_PIN, GPIO.OUT)

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
        # Wait for all threads to complete before cleaning up GPIO
        for thread in threading.enumerate():
            if thread is not threading.main_thread():
                thread.join()
        # Clean up GPIO settings before exiting
        GPIO.cleanup()
