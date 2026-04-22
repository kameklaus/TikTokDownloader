from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import subprocess
import os
import json
import re
from datetime import datetime
from pathlib import Path
import threading
import time

# Importing settings from the adjacent config.py file
from config import (
    YT_DLP_PATH, MATERIALS_PATH, DB_PATH, 
    DOWNLOAD_SETTINGS, FLASK_SETTINGS, validate_config, ensure_folders
)

app = Flask(__name__)
CORS(app)

# Global variables
download_status = {
    "is_running": False,
    "current_account": "",
    "progress": {"current": 0, "total": 0},
    "message": "Ready to work",
    "type": "idle"
}

download_lock = threading.Lock()

class Database:
    def __init__(self):
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                start_video_url TEXT,
                start_video_id TEXT,
                videos_downloaded INTEGER DEFAULT 0,
                last_check TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                video_id TEXT UNIQUE NOT NULL,
                video_url TEXT,
                filename TEXT,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_or_update_account(self, username, url, start_video_url=None, start_video_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM accounts WHERE username = ?', (username,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute('''
                    UPDATE accounts 
                    SET url = ?, start_video_url = ?, start_video_id = ?, status = 'pending'
                    WHERE username = ?
                ''', (url, start_video_url, start_video_id, username))
                account_id = existing[0]
            else:
                cursor.execute('''
                    INSERT INTO accounts (username, url, start_video_url, start_video_id)
                    VALUES (?, ?, ?, ?)
                ''', (username, url, start_video_url, start_video_id))
                account_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "id": account_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_all_accounts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
        res = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return res

    def get_account_by_username(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def delete_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        cursor.execute('DELETE FROM videos WHERE account_id = ?', (account_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    
    def update_account_status(self, account_id, videos_count=None, status=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if videos_count is not None:
            cursor.execute('UPDATE accounts SET videos_downloaded = ?, last_check = CURRENT_TIMESTAMP WHERE id = ?', (videos_count, account_id))
        if status:
            cursor.execute('UPDATE accounts SET status = ?, last_check = CURRENT_TIMESTAMP WHERE id = ?', (status, account_id))
        conn.commit()
        conn.close()
    
    def get_videos_by_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE account_id = ? ORDER BY download_date DESC', (account_id,))
        res = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return res
    
    def video_exists(self, video_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM videos WHERE video_id = ?', (video_id,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists
    
    def save_state(self, state):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO download_state (id, state, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)', (json.dumps(state),))
        conn.commit()
        conn.close()
    
    def clear_state(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM download_state WHERE id = 1')
        conn.commit()
        conn.close()

db = Database()

class TikTokDownloader:
    def __init__(self):
        ensure_folders()
    
    def create_account_folders(self, username):
        account_path = Path(MATERIALS_PATH) / username
        input_path = account_path / "input"
        output_path = account_path / "output"
        
        input_path.mkdir(parents=True, exist_ok=True)
        output_path.mkdir(parents=True, exist_ok=True)
        
        return str(input_path)
    
    def parse_url(self, url):
        username_match = re.search(r'@([a-zA-Z0-9._]+)', url)
        video_id_match = re.search(r'/video/(\d+)', url)
        
        if not username_match:
            return None
        
        username = username_match.group(1)
        video_id = video_id_match.group(1) if video_id_match else None
        
        return {
            "username": username,
            "account_url": f"https://www.tiktok.com/@{username}",
            "start_video_url": url if video_id else None,
            "start_video_id": video_id
        }
    
    def download_account_videos(self, account):
        global download_status
        account_id = account['id']
        username = account['username']
        url = account['url']
        start_video_id = account.get('start_video_id')
        
        download_status['current_account'] = username
        download_status['message'] = f"Preparing to download @{username}..."
        
        input_path = self.create_account_folders(username)
        current_count = len(db.get_videos_by_account(account_id))
        
        # Base command
        output_template = os.path.join(input_path, f"{username}_%(autonumber)s.%(ext)s")
        cmd = [
            YT_DLP_PATH,
            url,
            "-o", output_template,
            "--no-check-certificate",
            "--autonumber-start", str(current_count + 1),
            "--autonumber-size", "4",
            "--sleep-interval", str(DOWNLOAD_SETTINGS["sleep_interval"]),
            "--max-sleep-interval", str(DOWNLOAD_SETTINGS["max_sleep_interval"]),
            "--no-warnings",
            "--no-playlist",
            "--playlist-reverse"
        ]
        
        # LOGIC TO START FROM A SPECIFIC VIDEO
        if start_video_id:
            print(f"Searching for video position {start_video_id}...")
            list_cmd = [YT_DLP_PATH, url, "--flat-playlist", "--print", "id", "--no-warnings"]
            try:
                result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    all_ids = [v for v in result.stdout.strip().split('\n') if v]
                    if start_video_id in all_ids:
                        index = all_ids.index(start_video_id)
                        videos_to_take = index + 1
                        cmd.extend(["--playlist-end", str(videos_to_take)])
                        print(f"Will download {videos_to_take} videos (from newest to the specified one)")
                    else:
                        print("Video not found in list, downloading all")
            except Exception as e:
                print(f"Error fetching list: {e}")

        try:
            download_status['type'] = 'running'
            print(f"Launching: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace'
            )
            
            videos_downloaded = 0
            for line in process.stdout:
                print(line.strip())
                if "[download]" in line and "Destination:" in line:
                    videos_downloaded += 1
                    download_status['message'] = f"@{username}: downloaded {videos_downloaded}"
            
            process.wait()
            
            # Cleaning up junk
            for info_file in Path(input_path).glob("*.info.json"):
                info_file.unlink(missing_ok=True)
                
            total = current_count + videos_downloaded
            db.update_account_status(account_id, total, 'completed')
            db.clear_state()
            
            return {"success": True, "videos_downloaded": videos_downloaded}
            
        except Exception as e:
            print(f"Error: {e}")
            db.update_account_status(account_id, status='error')
            return {"success": False, "error": str(e)}

    def check_for_new_videos(self, account):
        try:
            cmd = [YT_DLP_PATH, account['url'], "--flat-playlist", "--print", "id", "--playlist-end", "5"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                ids = [v for v in result.stdout.strip().split('\n') if v]
                has_new = any(not db.video_exists(vid) for vid in ids)
                db.update_account_status(account['id'], status='checked')
                return {"success": True, "has_new": has_new}
            return {"success": True, "has_new": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

downloader = TikTokDownloader()

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    return jsonify(db.get_all_accounts())

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    return jsonify(db.delete_account(account_id))

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(download_status)

@app.route('/api/download/start', methods=['POST'])
def start_download():
    global download_status
    if not download_lock.acquire(blocking=False):
        return jsonify({"error": "Busy"}), 400
    
    try:
        url = request.json.get('url')
        parsed = downloader.parse_url(url)
        if not parsed:
            download_lock.release()
            return jsonify({"error": "Bad URL"}), 400
            
        res = db.add_or_update_account(parsed['username'], parsed['account_url'], parsed['start_video_url'], parsed['start_video_id'])
        account = db.get_account_by_username(parsed['username'])
        
        def task():
            global download_status
            try:
                download_status['is_running'] = True
                res = downloader.download_account_videos(account)
                download_status['type'] = 'success' if res['success'] else 'error'
                download_status['message'] = "Done" if res['success'] else res['error']
            finally:
                download_status['is_running'] = False
                download_lock.release()
        
        threading.Thread(target=task, daemon=True).start()
        return jsonify({"success": True})
    except Exception as e:
        download_lock.release()
        return jsonify({"error": str(e)}), 500

@app.route('/api/check-updates', methods=['POST'])
def check_updates():
    if not download_lock.acquire(blocking=False): return jsonify({"error": "Busy"}), 400
    def task():
        download_status['is_running'] = True
        download_status['type'] = 'running'
        for acc in db.get_all_accounts():
            download_status['message'] = f"Checking @{acc['username']}"
            if downloader.check_for_new_videos(acc).get('has_new'):
                downloader.download_account_videos(acc)
        download_status['is_running'] = False
        download_status['type'] = 'success'
        download_status['message'] = "All checked"
        download_lock.release()
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"success": True})

@app.route('/api/videos/<int:account_id>', methods=['GET'])
def get_videos(account_id):
    return jsonify(db.get_videos_by_account(account_id))

@app.route('/api/config', methods=['GET'])
def get_conf():
    return jsonify({"yt_dlp_path": YT_DLP_PATH, "materials_path": MATERIALS_PATH, "settings": DOWNLOAD_SETTINGS})

if __name__ == '__main__':
    errs = validate_config()
    if errs:
        print("CONFIGURATION ERRORS:", errs)
        input("Press Enter...")
        exit(1)
    print(f"Server on http://localhost:{FLASK_SETTINGS['port']}")
    app.run(**FLASK_SETTINGS)