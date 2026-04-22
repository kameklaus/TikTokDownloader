"""
TikTok Downloader Configuration
"""
import os

# Path to the yt-dlp executable file
# Make sure this file exists!
YT_DLP_PATH = r"C:\Tools\VidDownload\yt-dlp.exe"

# Path to the folder for saving videos
MATERIALS_PATH = r"D:\materials"

# Path to the SQLite database
DB_PATH = "tiktok_downloader.db"

# State file
STATE_FILE = "download_state.json"

# Download settings
DOWNLOAD_SETTINGS = {
    "sleep_interval": 2,
    "max_sleep_interval": 5,
    "autonumber_size": 4,
    "save_state_every": 5,
}

# Flask server settings
FLASK_SETTINGS = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True,
}

# Configuration validation
def validate_config():
    errors = []
    if not os.path.exists(YT_DLP_PATH):
        errors.append(f"yt-dlp not found at path: {YT_DLP_PATH}")
    
    drive = os.path.splitdrive(MATERIALS_PATH)[0]
    if drive and not os.path.exists(drive + "\\"):
        errors.append(f"Drive {drive} not found")
    
    return errors

def ensure_folders():
    os.makedirs(MATERIALS_PATH, exist_ok=True)