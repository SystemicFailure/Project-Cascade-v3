#!/usr/bin/env python3
"""
Auto-sync files from Windows to Google Drive
Monitors C:\Users\Dr. Strangelove\cascade_app_package for changes
and syncs to Google Drive folder: 1W7cYOTue3T3TiLtucPGPBDJtapyLGQNC
"""

import os
import time
from pathlib import Path
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

# Configuration
LOCAL_PATH = Path(r"C:\Users\Dr. Strangelove\cascade_app_package")
DRIVE_FOLDER_ID = "1W7cYOTue3T3TiLtucPGPBDJtapyLGQNC"
LAST_SYNC_FILE = LOCAL_PATH / ".last_sync_timestamp"

# Files to sync (exclude unnecessary files)
EXCLUDE_PATTERNS = {'.git', '__pycache__', '.gitignore', 'Backups', '.env', '.last_sync_timestamp'}

def get_drive_service():
    """Authenticate with Google Drive"""
    try:
        from google.auth import default
        credentials, _ = default()
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"❌ Error: Could not authenticate with Google Drive: {e}")
        print("   Make sure Google Drive API credentials are configured.")
        return None

def get_drive_file_id(service, file_name, folder_id):
    """Find a file in Google Drive folder by name"""
    try:
        query = f"'{folder_id}' in parents and name='{file_name}' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None
    except Exception as e:
        print(f"⚠️  Error finding file: {e}")
        return None

def upload_file_to_drive(service, local_path, folder_id, file_name):
    """Upload or update a file in Google Drive"""
    try:
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(str(local_path), resumable=True)

        # Check if file already exists
        existing_id = get_drive_file_id(service, file_name, folder_id)

        if existing_id:
            # Update existing file
            service.files().update(fileId=existing_id, media_body=media).execute()
            print(f"✅ Updated on Drive: {file_name}")
        else:
            # Create new file
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"✅ Uploaded to Drive: {file_name}")
        return True
    except Exception as e:
        print(f"❌ Error uploading {file_name}: {e}")
        return False

def get_last_sync_time():
    """Get the timestamp of last sync"""
    if LAST_SYNC_FILE.exists():
        return float(LAST_SYNC_FILE.read_text())
    return 0

def set_last_sync_time():
    """Update last sync timestamp"""
    LAST_SYNC_FILE.write_text(str(time.time()))

def sync_files():
    """Sync changed files from Windows to Google Drive"""
    service = get_drive_service()
    if not service:
        return False

    last_sync = get_last_sync_time()
    synced_count = 0

    print(f"\n🔄 Syncing from Windows to Google Drive...")
    print(f"   Local: {LOCAL_PATH}")
    print(f"   Drive: {DRIVE_FOLDER_ID}\n")

    try:
        for file_path in LOCAL_PATH.rglob("*"):
            # Skip excluded patterns
            if any(excl in file_path.parts for excl in EXCLUDE_PATTERNS):
                continue

            if not file_path.is_file():
                continue

            # Check if file was modified since last sync
            file_mtime = file_path.stat().st_mtime
            if file_mtime <= last_sync:
                continue

            file_name = file_path.name
            relative_path = file_path.relative_to(LOCAL_PATH)

            if upload_file_to_drive(service, file_path, DRIVE_FOLDER_ID, file_name):
                synced_count += 1

        if synced_count > 0:
            set_last_sync_time()
            print(f"\n✅ Synced {synced_count} files to Google Drive")
            return True
        else:
            print(f"✅ No changes to sync")
            return True

    except Exception as e:
        print(f"❌ Sync error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WINDOWS → GOOGLE DRIVE AUTO-SYNC")
    print("=" * 60)

    success = sync_files()
    exit(0 if success else 1)
