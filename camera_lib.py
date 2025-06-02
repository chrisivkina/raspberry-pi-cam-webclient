from picamera2 import Picamera2
import cv2
import threading
from time import time
import time as time_module
import logging
import numpy as np
from turbojpeg import TurboJPEG
import base64

from config import *

jpeg = TurboJPEG()


def get_streaming_status():
    return Camera.is_streaming


class Camera:
    # Class variable to track streaming status
    is_streaming = False

    def __init__(self, socketio):
        self.socketio = socketio
        self.camera = None
        self.camera_occupied_flag = False
        self.generator_stop_flag = threading.Event()

        self.last_jpeg = None
        self.frame_base64 = None
        self.capture_thread = None

        # Lock for thread synchronization
        self.camera_lock = threading.Lock()

        # FPS tracking
        self.current_second = 0
        self.frames_this_second = 0
        self.fps = 0

        # Client tracking
        self.clients = set()  # Connected clients
        self.streaming_clients = set()  # Clients actively viewing stream

        # Start frame emission thread
        self.emit_thread = threading.Thread(target=self._emit_frames_thread, daemon=True)
        self.emit_thread.start()

    def add_client(self, client_id):
        """Add a new connected client."""
        self.clients.add(client_id)
        logging.info(f"Client {client_id} connected. Total clients: {len(self.clients)}")

        # Start camera if this is the first client
        if len(self.clients) == 1 and self.camera is None:
            self._start_camera()

    def remove_client(self, client_id):
        """Remove a disconnected client."""
        if client_id in self.clients:
            self.clients.remove(client_id)
        if client_id in self.streaming_clients:
            self.streaming_clients.remove(client_id)

        logging.info(f"Client {client_id} disconnected. Remaining clients: {len(self.clients)}")

        # Stop camera if no clients are connected (power saving)
        if len(self.clients) == 0 and config['CONFIG_POWER_SAVE_MODE']:
            self.stop_cam()

    def start_streaming_to_client(self, client_id):
        """Start streaming to a specific client."""
        if client_id not in self.streaming_clients:
            self.streaming_clients.add(client_id)
            logging.info(f"Client {client_id} started viewing. Active viewers: {len(self.streaming_clients)}")

    def stop_streaming_to_client(self, client_id):
        """Stop streaming to a specific client."""
        if client_id in self.streaming_clients:
            self.streaming_clients.remove(client_id)
            logging.info(f"Client {client_id} stopped viewing. Remaining viewers: {len(self.streaming_clients)}")

    def _start_camera(self):
        """Initialize camera and start capture thread."""
        with self.camera_lock:
            self.create_camera_instance()
            self.camera.start()
            self._start_capture_thread()

    def _start_capture_thread(self):
        """Start the continuous frame capture thread."""
        self.generator_stop_flag.clear()
        self.capture_thread = threading.Thread(
            target=self._capture_frames_continuously, daemon=True
        )
        self.capture_thread.start()

    def stop_cam(self):
        """Stop the camera and all associated resources."""
        with self.camera_lock:
            self.generator_stop_flag.set()

            # Give the capture thread time to exit gracefully
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=1.0)

            if self.camera is not None:
                try:
                    self.camera.stop()
                    self.camera.close()
                except Exception as e:
                    logging.error(f"Error closing camera: {e}")
                finally:
                    self.camera = None
                    self.camera_occupied_flag = False

    def create_camera_instance(self):
        """Create and configure the camera with high-quality settings."""
        try:
            self.camera_occupied_flag = True
            self.camera = Picamera2()

            # Use high-quality stream for clients
            stream_res = config.get('CONFIG_STREAMING_RESOLUTION', (1920, 1080))

            # Create a video configuration for high-quality streaming
            self.camera.configure(self.camera.create_video_configuration(
                main={"size": stream_res, "format": "RGB888"},  # RGB for easier processing
                buffer_count=4,  # Increase buffer to prevent frame drops
                controls={"FrameDurationLimits": (33333, 33333)}  # ~30fps
            ))
        except Exception as e:
            logging.error(f"Error creating camera instance: {e}")
            self.camera_occupied_flag = False
            self.camera = None

    def _capture_frames_continuously(self):
        """Continuously capture frames for streaming to clients."""
        Camera.is_streaming = True

        try:
            while not self.generator_stop_flag.is_set():
                try:
                    # Capture frames as long as any clients are connected
                    if len(self.clients) > 0:
                        frame = self.camera.capture_array("main")
                        self._process_stream_frame(frame)

                    # Control frame rate
                    time_module.sleep(0.033)  # ~30fps
                except Exception as e:
                    logging.error(f"Error capturing frames: {e}")
                    time_module.sleep(0.1)  # Wait a bit before trying again

        finally:
            Camera.is_streaming = False

    def _process_stream_frame(self, frame: np.ndarray):
        """Process frame for streaming to clients."""
        try:
            # Convert frame to RGB format
            if len(frame.shape) == 3:
                if frame.shape[2] == 4:  # BGRA
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                elif frame.shape[2] == 3:
                    # Check if already RGB or if BGR
                    if self.camera and "format" in self.camera.camera_configuration()["main"] and \
                            self.camera.camera_configuration()["main"]["format"] == "RGB888":
                        frame_rgb = frame.copy()  # Already RGB
                    else:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                logging.error(f"Unsupported frame shape: {frame.shape}")
                return

            # Add FPS indicator
            cv2.putText(frame_rgb, f"FPS: {self.fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                        cv2.LINE_AA)

            # Encode frame to JPEG
            self.last_jpeg = jpeg.encode(frame_rgb, quality=90)
            self.frame_base64 = base64.b64encode(self.last_jpeg).decode('utf-8')

            # FPS tracking
            if self.current_second != int(time()):
                self.current_second = int(time())
                self.fps = self.frames_this_second
                self.frames_this_second = 0
                logging.info(f"FPS: {self.fps}")

            self.frames_this_second += 1
        except Exception as e:
            logging.error(f"Error processing stream frame: {e}")

    def _emit_frames_thread(self):
        """Thread to emit frames to connected clients via Socket.IO."""
        last_log_time = 0

        while True:  # This thread runs for the life of the object
            current_time = time()

            # Skip processing if stopping or no streaming clients
            if self.generator_stop_flag.is_set() or len(self.streaming_clients) == 0:
                time_module.sleep(0.033)
                continue

            try:
                if self.frame_base64:
                    frame_data = {'frame': self.frame_base64}
                    for client_id in self.streaming_clients:
                        self.socketio.emit('frame', frame_data, to=client_id)

                    # Log frame emission occasionally
                    if current_time - last_log_time > 5:  # Every 5 seconds
                        logging.info(
                            f"Emitting frames to {len(self.streaming_clients)} clients, frame size: {len(self.frame_base64)} bytes")
                        last_log_time = current_time
                elif len(self.streaming_clients) > 0:
                    if current_time - last_log_time > 5:
                        logging.warning("No frames available to emit")
                        last_log_time = current_time
            except Exception as e:
                logging.error(f"Error emitting frames: {e}")

            time_module.sleep(0.033)  # ~30fps

    def stop_stream(self):
        """Stop the streaming generator."""
        self.generator_stop_flag.set()
