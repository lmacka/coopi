import json
import os
from config import STATEFILE

# Global variable to track the running state
door_state_running = False

def is_door_open():
    if not os.path.exists(STATEFILE):
        return False

    with open(STATEFILE) as json_file:
        json_data = json.load(json_file)
        return json_data.get('state') == 'open'

def is_door_state_running():
    global door_state_running
    return door_state_running

def set_door_state_running(state):
    global door_state_running
    door_state_running = state
