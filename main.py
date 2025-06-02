from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, redirect, abort, send_from_directory
import json
import time
import logging

from config import *
import pi_sys_data


app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_timeout=config['CONFIG_SOCKETIO_PING_TIMEOUT'],
    ping_interval=config['CONFIG_SOCKETIO_PING_INTERVAL']
)
rasp = pi_sys_data.Pi()


# Configure logging
logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# prevent crash when working in local mode
if not config['CONFIG_LOCAL_MODE']:

    import camera_lib
    cam = camera_lib.Camera(socketio=socketio)


@app.route('/')
def index():
    return render_template('index.html', config=config)


@app.route("/api/get_config")
def get_config():
    return json.dumps(config)


@app.route("/api/toggle_config", methods=['POST'])
def toggle_config():
    data = request.get_json()
    config[data['key']] = not config[data['key']]

    return redirect('/')


@app.route('/video_stream')
def video_stream():
    return render_template('video_stream.html')


@app.route('/api/get_pi_data')
def get_pi_data():
    return json.dumps({
        'cpu_temp': rasp.cpu_temp,
        'battery_low': rasp.battery_low,
        'uptime': rasp.uptime,
        'disk_space': rasp.disk_space[0],
        'disk_space_used': rasp.disk_space[1],
        'record_status': cam.camera_occupied_flag if not config['CONFIG_LOCAL_MODE'] else False,
    })


@app.route('/api/stop_stream', methods=['POST', 'GET'])
def stop_stream():
    cam.stop_cam()
    return redirect('/video_stream')


# Add Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logging.info(f'Client connected: {request.sid}')
    if not config['CONFIG_LOCAL_MODE']:
        cam.add_client(request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f'Client disconnected: {request.sid}')
    if not config['CONFIG_LOCAL_MODE']:
        cam.remove_client(request.sid)


@socketio.on('start_stream')
def handle_start_stream():
    if not config['CONFIG_LOCAL_MODE']:
        cam.start_streaming_to_client(request.sid)


@socketio.on('stop_stream')
def handle_stop_stream():
    if not config['CONFIG_LOCAL_MODE']:
        cam.stop_streaming_to_client(request.sid)


@socketio.on('get_pi_status')
def handle_get_pi_status():
    emit('pi_status_update', {
        'cpu_temp': rasp.cpu_temp,
        'battery_low': rasp.battery_low,
        'uptime': rasp.uptime,
        'disk_space': rasp.disk_space[0],
        'disk_space_used': rasp.disk_space[1],
        'record_status': cam.camera_occupied_flag if not config['CONFIG_LOCAL_MODE'] else False,
    })


@socketio.on('toggle_config')
def handle_toggle_config(data):
    config[data['key']] = not config[data['key']]
    emit('config_updated', {'key': data['key'], 'value': config[data['key']]}, broadcast=True)


if __name__ == '__main__':
    print('Starting up...')
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
