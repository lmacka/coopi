import json
import os
from .config import STATEFILE

# Global variable to track the running state
DOOR_STATE_RUNNING = False


def is_door_open():
    if not os.path.exists(STATEFILE):
        return False

    with open(STATEFILE, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        return json_data.get("state") == "open"


def is_door_state_running():
    return DOOR_STATE_RUNNING


def set_door_state_running(state):
    global DOOR_STATE_RUNNING
    DOOR_STATE_RUNNING = state
