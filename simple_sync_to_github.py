#!/usr/bin/env python3
import os, subprocess, time
from pathlib import Path

REPO_PATH = Path(__file__).parent.absolute()
EXCLUDE = {'.git', '__pycache__', '.gitignore', 'Backups', '.env', '.vscode', '.last_sync', '.drive_sync'}

print("\n" + "="*60)
print("SYNCING TO GITHUB")
print("="*60)

try:
    # Stage all changes
    result = subprocess.run(["git", "add", "-A"], cwd=str(REPO_PATH), capture_output=True, text=True)

    # Commit
    result = subprocess.run(["git", "commit", "-m", "Auto-sync: Files updated\n\n[auto-sync]"], cwd=str(REPO_PATH), capture_output=True, text=True)

    if "nothing to commit" in result.stdout or result.returncode != 0:
        print("✅ No changes to commit")
    else:
        print("✅ Changes committed")

    # Push
    result = subprocess.run(["git", "push", "origin", "main"], cwd=str(REPO_PATH), capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Pushed to GitHub")
        print("🚀 Streamlit Cloud will redeploy in 1-2 minutes\n")
    else:
        print(f"⚠️  Push warning: {result.stderr}\n")

except Exception as e:
    print(f"❌ Error: {e}\n")
