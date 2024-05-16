from flask import Flask, render_template, jsonify
import automationhat
import door_control
import atexit

app = Flask(__name__)

if automationhat.is_automation_hat():
    atexit.register(automationhat.light.power.off)

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

if __name__ == "__main__":
    if automationhat.is_automation_hat():
        automationhat.light.power.on()
    app.run(host='0.0.0.0', debug=True)