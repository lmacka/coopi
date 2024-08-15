import os
import json
import psutil
from config import statefile

def is_door_open():
    try:
        with open(statefile, 'r') as file:
            state = json.load(file)
            return state.get('door_open', False)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def is_door_state_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'door_control.py' in proc.info['cmdline']:
            return True
    return False