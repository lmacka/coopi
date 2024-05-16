import sys
import RPi.GPIO as GPIO
import automationhat
import threading
import json
import time

############ CONFIG ###############
statefile = 'static/state.json'
actuateTime = 90
###################################

# Create a lock
lock = threading.Lock()

def get_lock_status():
    return lock.locked()

def open_door():
    # Check if the lock is acquired
    if lock.locked():
        return "Another operation is in progress"

    with open(statefile) as json_file:
        json_data = json.load(json_file)
        doorstate = json_data['state']
    if ( doorstate == 'closed' ):
        with open(statefile, 'w') as f:
            json.dump({'state': 'open'}, f, ensure_ascii=False)
        # Acquire the lock and start a new thread
        lock.acquire()
        threading.Thread(target=delayed_open).start()
        return 'Opening door. This will take ' + str(actuateTime) + ' seconds'
    else:
        return "Door already open"

def close_door():
    # Check if the lock is acquired
    if lock.locked():
        return "Another operation is in progress"

    with open(statefile) as json_file:
        json_data = json.load(json_file)
        doorstate = json_data['state']
    if ( doorstate == 'open' ):
        with open(statefile, 'w') as f:
            json.dump({'state': 'closed'}, f, ensure_ascii=False)
        # Acquire the lock and start a new thread
        lock.acquire()
        threading.Thread(target=delayed_close).start()
        return 'Closing door. This will take ' + str(actuateTime) + ' seconds'
    else:
        return "Door already closed"

def delayed_open():
    if automationhat.is_automation_hat():
        automationhat.light.comms.on()
        automationhat.relay.one.off()
        automationhat.relay.two.on()
        time.sleep(actuateTime)
        automationhat.light.comms.off()
    # Release the lock
    lock.release()

def delayed_close():
    if automationhat.is_automation_hat():
        automationhat.light.comms.on()
        automationhat.relay.one.on()
        automationhat.relay.two.off()
        time.sleep(actuateTime)
        automationhat.light.comms.off()
    # Release the lock
    lock.release()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Script to open and close the door, for use with cron")
        print("Usage: python door_control.py <command>")
        print("<command> can be 'open' or 'close'")
        sys.exit(1)

    command = sys.argv[1]
    if command == 'open':
        print(open_door())
    elif command == 'close':
        print(close_door())
    else:
        print(f"Invalid command: {command}")
        sys.exit(1)

    command = sys.argv[1]
    if command == 'open':
        open_door()
    elif command == 'close':
        close_door()
    else:
        print(f"Invalid command: {command}")
        sys.exit(1)