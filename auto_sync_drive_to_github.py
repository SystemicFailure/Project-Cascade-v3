#!/usr/bin/env python3
"""
Auto-sync files from Google Drive to GitHub
Watches Google Drive folder: 1W7cYOTue3T3TiLtucPGPBDJtapyLGQNC
and commits changes to GitHub
"""

import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Configuration
DRIVE_FOLDER_ID = "1W7cYOTue3T3TiLtucPGPBDJtapyLGQNC"
REPO_PATH = r"C:\Users\Dr. Strangelove\cascade_app_package"
LAST_SYNC_FILE = Path(REPO_PATH) / ".drive_sync_timestamp"

# Files to sync
FILES_TO_SYNC = [
    "cascade_db.py",
    "cascade_app.py",
    "cascade_data.db",
    "cascade_config.json",
]

def get_drive_service():
    """Authenticate with Google Drive"""
    try:
        from google.auth import default
        credentials, _ = default()
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"❌ Error: Could not authenticate with Google Drive: {e}")
        return None

def list_drive_files(service, folder_id):
    """List all files in Google Drive folder"""
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            pageSize=100
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def download_file(service, file_id, file_name, local_path):
    """Download a file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_obj = io.BytesIO()
        downloader = MediaIoBaseDownload(file_obj, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(file_obj.getvalue())
        print(f"✅ Downloaded: {file_name}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {file_name}: {e}")
        return False

def get_last_sync_time():
    """Get timestamp of last sync"""
    if LAST_SYNC_FILE.exists():
        return float(LAST_SYNC_FILE.read_text())
    return 0

def set_last_sync_time():
    """Update last sync timestamp"""
    LAST_SYNC_FILE.write_text(str(time.time()))

def check_for_changes():
    """Check if there are uncommitted changes in git"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except Exception as e:
        print(f"⚠️  Error checking git status: {e}")
        return False

def commit_and_push(commit_msg):
    """Commit changes and push to GitHub"""
    try:
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=REPO_PATH,
            check=True
        )

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=REPO_PATH,
            check=True
        )

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Changes committed and pushed to GitHub")
            print("🚀 Streamlit Cloud will auto-redeploy in 1-2 minutes\n")
            return True
        else:
            print(f"❌ Push failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during commit/push: {e}")
        return False

def sync_from_drive():
    """Sync changed files from Google Drive to local repo"""
    service = get_drive_service()
    if not service:
        return False

    last_sync = get_last_sync_time()
    synced_count = 0

    print(f"🔄 Syncing from Google Drive to GitHub...")
    print(f"   Folder: {DRIVE_FOLDER_ID}\n")

    drive_files = list_drive_files(service, DRIVE_FOLDER_ID)

    if not drive_files:
        print("⚠️  No files found in Google Drive folder")
        return False

    for drive_file in drive_files:
        file_id = drive_file['id']
        file_name = drive_file['name']

        # Only sync if in our target list or if modified recently
        if file_name not in FILES_TO_SYNC:
            continue

        # Check modification time
        try:
            mod_time = datetime.fromisoformat(drive_file['modifiedTime'].replace('Z', '+00:00')).timestamp()
            if mod_time <= last_sync:
                continue
        except:
            pass

        local_path = os.path.join(REPO_PATH, file_name)

        if download_file(service, file_id, file_name, local_path):
            synced_count += 1

    if synced_count == 0:
        print("✅ No changes to sync from Google Drive")
        return True

    print(f"\n📁 Downloaded {synced_count} files from Google Drive")

    # Check for changes and commit
    if check_for_changes():
        commit_msg = f"Auto-sync: Update files from Google Drive\n\n[auto-sync] {synced_count} files synced"
        if commit_and_push(commit_msg):
            set_last_sync_time()
            return True
    else:
        print("✅ No changes detected in git")
        set_last_sync_time()
        return True

    return False

if __name__ == "__main__":
    print("=" * 60)
    print("GOOGLE DRIVE → GITHUB AUTO-SYNC")
    print("=" * 60)

    success = sync_from_drive()
    exit(0 if success else 1)
