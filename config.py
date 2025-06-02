import os

config = {
    'CONFIG_LOCAL_MODE': os.name == 'nt',  # Determines if camera lib is available. If on Windows, it defaults to local mode.

    'CONFIG_POWER_SAVE_MODE': True,        # Camera power saving mode (recommended, reduces power consumption when no clients are connected)
    'CONFIG_SOCKETIO_PING_TIMEOUT': 5,     # Socket.IO ping timeout in seconds
    'CONFIG_SOCKETIO_PING_INTERVAL': 25,   # Socket.IO ping interval in seconds
    'CONFIG_STREAMING_RESOLUTION': (1920, 1080),

    # Debug settings
    'CONFIG_INDUCE_STREAM_MALFUNCTION': False,  # To test stream placeholder
}
