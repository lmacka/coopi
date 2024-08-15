import json
import os
from config import statefile

def is_door_open():
    if not os.path.exists(statefile):
        return False

    with open(statefile) as json_file:
        json_data = json.load(json_file)
        return json_data.get('state') == 'open'

def is_door_state_running():
    # This function should be implemented based on how you track the running state
    # For example, you might have a separate state in the state file or a global variable
    return False