#!/usr/bin/env python3
import os, sys, time, subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATH = Path(__file__).parent.absolute()
REPO_PATH = str(WATCH_PATH)
EXCLUDE = {'.git', '__pycache__', '.gitignore', 'Backups', '.env', '.vscode', 'node_modules', '.last_sync'}

class Handler(FileSystemEventHandler):
    def __init__(self):
        self.syncing = False
        self.last_sync = 0
    def should_sync(self, path):
        if not os.path.isfile(path): return False
        for x in EXCLUDE:
            if x.lower() in path.lower(): return False
        return True
    def on_created(self, event):
        if self.should_sync(event.src_path):
            print(f'📝 {Path(event.src_path).name}')
            self.trigger()
    def on_modified(self, event):
        if self.should_sync(event.src_path):
            print(f'✏️  {Path(event.src_path).name}')
            self.trigger()
    def trigger(self):
        now = time.time()
        if now - self.last_sync < 2 or self.syncing: return
        self.syncing = True
        self.last_sync = now
        print('\n🔄 SYNCING TO GITHUB\n')
        try:
            subprocess.run(['python', 'simple_sync_to_github.py'], cwd=REPO_PATH, timeout=60)
        except Exception as e:
            print(f'❌ Error: {e}\n')
        finally:
            self.syncing = False

print('Cascade File Watcher - Monitoring for changes (Ctrl+C to stop)\n')
observer = Observer()
observer.schedule(Handler(), str(WATCH_PATH), recursive=True)
observer.start()
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
