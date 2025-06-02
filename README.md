# Raspberry Pi Camera 2 Web Streaming Client

A web-based client for streaming video from a Raspberry Pi camera, 
with real-time status monitoring and media management. The backend is built 
with Python (Flask + Flask-SocketIO), and the frontend uses JavaScript with 
Socket.IO for live updates.

## Features

- Live video streaming from Raspberry Pi Camera 2
- Real-time device status (CPU temp, disk space, uptime, battery, etc.)
- Configurable settings via web UI
- Power-saving mode for camera
- Responsive web interface

## Requirements

- Python 3.7+
- Raspberry Pi OS (for camera streaming)
- Raspberry Pi Camera 2 (hardware)

## Python Dependencies

Install with pip:

```bash
pip install flask flask-socketio picamera2 opencv-python numpy turbojpeg
```

## Setup

1. Clone the repository to your Raspberry Pi.
2. Install the required Python packages (see above).
3. Ensure the camera is enabled (`sudo raspi-config`).
4. Run the server:

```bash
python main.py
```

Or use the provided launcher script:

```bash
sh launcher.sh
```

5. Open a browser and navigate to `http://<raspberry-pi-ip>:8080`.

## Project Structure

- `main.py` - Flask web server and Socket.IO backend
- `camera_lib.py` - Camera streaming and frame processing logic
- `pi_sys_data.py` - System data collection (CPU temp, disk, etc.)
- `config.py` - Configuration settings
- `static/` - Frontend JavaScript and CSS
- `templates/` - HTML templates

## External Libraries Used

- [Flask](https://palletsprojects.com/p/flask/) - Web framework
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - Real-time communication
- [picamera2](https://github.com/raspberrypi/picamera2) - Raspberry Pi Camera library
- [OpenCV (cv2)](https://opencv.org/) - Image processing
- [NumPy](https://numpy.org/) - Numerical operations
- [PyTurboJPEG](https://github.com/lilohuang/PyTurboJPEG) - Fast JPEG encoding/decoding
- [Socket.IO](https://socket.io/) (frontend) - Real-time web communication

## Notes

- On Windows, the app runs in local mode (no camera streaming) for debugging purposes.

## License

See individual library licenses for third-party dependencies.
```
This covers project usage, structure, and references all major external libraries used.