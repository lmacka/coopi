from flask import Flask, render_template, request, redirect, url_for, Response
from door_state import is_door_open, is_door_state_running
from door_control import open_door, close_door
from config import SCHEDULEFILE, RTSP_FEED_URL, ENABLE_RTSP_STILL
import builtins
import subprocess
import logging
import cv2
import threading
import json
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def check_schedule():
    while True:
        schedule = load_schedule()
        current_time = time.strftime('%H:%M')
        if schedule['open_enabled'] and schedule['open_time'] == current_time:
            logging.info("Opening door on schedule...")
            open_door()
        if schedule['close_enabled'] and schedule['close_time'] == current_time:
            logging.info("Closing door on schedule...")
            close_door()
        time.sleep(60)  # Check every minute

def load_schedule():
    if os.path.exists(SCHEDULEFILE):
        with builtins.open(SCHEDULEFILE) as f:
            return json.load(f)
    return {'open_time': '', 'close_time': '', 'open_enabled': False, 'close_enabled': False}

def save_schedule(schedule):
    with builtins.open(SCHEDULEFILE, 'w') as f:
        json.dump(schedule, f, ensure_ascii=False)

@app.route('/')
def home():
    door_open = is_door_open()
    door_state_running = is_door_state_running()
    schedule = load_schedule()
    return render_template('index.html', door_open=door_open, door_state_running=door_state_running, schedule=schedule)

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

@app.route('/snapshot')
def snapshot():
    if not ENABLE_RTSP_STILL:
        return "RTSP still image is disabled", 403

    cap = cv2.VideoCapture(RTSP_FEED_URL)
    success, frame = cap.read()
    cap.release()
    if not success:
        return "Failed to capture image", 500
    ret, buffer = cv2.imencode('.jpg', frame)
    return Response(buffer.tobytes(), mimetype='image/jpeg')

@app.route('/schedule', methods=['POST'])
def schedule():
    schedule = {
        'open_time': request.form['open_time'],
        'close_time': request.form['close_time'],
        'open_enabled': 'open_enabled' in request.form,
        'close_enabled': 'close_enabled' in request.form
    }
    save_schedule(schedule)
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Start the schedule checking thread
    schedule_thread = threading.Thread(target=check_schedule)
    schedule_thread.daemon = True
    schedule_thread.start()

    app.run(host='127.0.0.1', port=8086)
