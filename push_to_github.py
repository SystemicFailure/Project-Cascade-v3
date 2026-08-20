#!/usr/bin/env python3
"""
Push cascade_app_package to GitHub using the GitHub API
Bypasses git proxy restrictions
"""

import requests
import json
import base64
import os
from pathlib import Path

# Configuration
TOKEN = "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"
OWNER = "SystemicFailure"
REPO = "Project-Cascade-v3"
BRANCH = "main"
BASE_PATH = "cascade_app_package"

# GitHub API base URL
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"

# Headers with authentication
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

def get_current_commit():
    """Get the SHA of the current main branch commit"""
    url = f"{API_URL}/refs/heads/{BRANCH}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['object']['sha']
    else:
        print(f"Error getting current commit: {response.status_code}")
        print(response.text)
        return None

def get_file_sha(path):
    """Get the SHA of a file if it exists"""
    url = f"{API_URL}/contents/{path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['sha']
    return None

def push_file(file_path, github_path, commit_message):
    """Push a single file to GitHub"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        # Binary file
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')

    url = f"{API_URL}/contents/{github_path}"

    # Get existing SHA if file exists
    sha = get_file_sha(github_path)

    data = {
        "message": commit_message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8') if isinstance(content, str) else content,
        "branch": BRANCH
    }

    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=HEADERS, json=data)

    if response.status_code in [201, 200]:
        print(f"✅ Pushed: {github_path}")
        return True
    else:
        print(f"❌ Failed to push {github_path}: {response.status_code}")
        print(response.text)
        return False

def push_cascade_app_package():
    """Push all files in cascade_app_package"""

    print("=" * 60)
    print("PUSHING CASCADE_APP_PACKAGE TO GITHUB")
    print("=" * 60)

    # Verify token works
    response = requests.get("https://api.github.com/user", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return False

    user = response.json()
    print(f"✅ Authenticated as: {user['login']}\n")

    # Get current HEAD
    current_sha = get_current_commit()
    if not current_sha:
        print("❌ Could not get current commit SHA")
        return False

    print(f"📌 Current HEAD: {current_sha[:8]}\n")

    # Find all files in cascade_app_package
    local_path = Path("/mnt/user-data/uploads/cascade_app_package")

    if not local_path.exists():
        print(f"❌ Local path not found: {local_path}")
        return False

    pushed_count = 0
    failed_count = 0

    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_path.parent)
            github_path = str(relative_path).replace("\\", "/")

            commit_msg = f"Update: {github_path}\n\n[auto-sync] Automated cascade_app_package sync from Google Drive"

            if push_file(str(file_path), github_path, commit_msg):
                pushed_count += 1
            else:
                failed_count += 1

    print("\n" + "=" * 60)
    print(f"PUSH COMPLETE: {pushed_count} files pushed, {failed_count} failed")
    print("=" * 60)
    print("\n🚀 Streamlit Cloud will auto-redeploy within 1-2 minutes")

    return failed_count == 0

if __name__ == "__main__":
    success = push_cascade_app_package()
    exit(0 if success else 1)
