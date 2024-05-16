from flask import Flask, render_template, request, jsonify, Response
import subprocess
import logging
import io
import door_control

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/open_door', methods=['POST'])
def open_door_route():
    result = door_control.open_door()
    return jsonify({'message': result})

@app.route('/close_door', methods=['POST'])
def close_door_route():
    result = door_control.close_door()
    return jsonify({'message': result})

@app.route('/lock_status', methods=['GET'])
def lock_status_route():
    result = door_control.get_lock_status()
    return jsonify({'lock_engaged': result})

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen():
    command = ['libcamera-vid', '-t', '0', '-o', '-']
    ffmpeg_command = ['ffmpeg', '-i', '-', '-f', 'mjpeg', '-']
    camera_process = subprocess.Popen(command, stdout=subprocess.PIPE)
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=camera_process.stdout, stdout=subprocess.PIPE)
    while True:
        frame = ffmpeg_process.stdout.read(1024)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)