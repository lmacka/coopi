from flask import Flask, render_template, request, redirect, url_for
from door_state import is_door_open, is_door_state_running
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    door_open = is_door_open()
    door_state_running = is_door_state_running()
    return render_template('index.html', door_open=door_open, door_state_running=door_state_running)

@app.route('/open', methods=['POST'])
def open():
    if not is_door_state_running():
        subprocess.run(['python3', 'door_control.py', 'open'])
    return redirect(url_for('home'))

@app.route('/close', methods=['POST'])
def close():
    if not is_door_state_running():
        subprocess.run(['python3', 'door_control.py', 'close'])
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8086)