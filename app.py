from flask import Flask, render_template, request, redirect, url_for, Response
from door_state import is_door_open, is_door_state_running
import subprocess
import cv2

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8086)