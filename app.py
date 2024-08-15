from flask import Flask, render_template, request, redirect, url_for
from door_control import open_door, close_door
from door_state import is_door_open, is_door_state_running

app = Flask(__name__)

@app.route('/')
def home():
    door_open = is_door_open()
    door_state_running = is_door_state_running()
    return render_template('index.html', door_open=door_open, door_state_running=door_state_running)

@app.route('/open', methods=['POST'])
def open():
    if not is_door_state_running():
        open_door()
    return redirect(url_for('home'))

@app.route('/close', methods=['POST'])
def close():
    if not is_door_state_running():
        close_door()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)