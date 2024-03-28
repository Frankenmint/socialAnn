import os
import subprocess
import obspy as obs

def on_stream_start(event):
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED:
        print("Stream started, launching broadcast announcer script.")
        # Ensure the path to your Python executable and script are correct
        subprocess.Popen(["path/to/python", "path/to/your/broadcast_announcer.py"])

def script_load(settings):
    obs.obs_frontend_add_event_callback(on_stream_start)
