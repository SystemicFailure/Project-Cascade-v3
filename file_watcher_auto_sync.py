import os, sys, time, subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATH = Path(__file__).parent.absolute()
REPO_PATH = str(WATCH_PATH)
EXCLUDE = {'.git', '__pycache__', '.gitignore', 'Backups', '.env', '.vscode', 'node_modules'}

class Handler(FileSystemEventHandler):
    def __init__(self):
        self.syncing = False
        self.last_sync = 0
    def should_sync(self, path):
        return not any(x.lower() in path.lower() for x in EXCLUDE) and os.path.isfile(path)
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
        print('\n🔄 SYNC TRIGGERED\n')
        try:
            subprocess.run(['python', 'auto_sync_windows_to_drive.py'], cwd=REPO_PATH, timeout=60)
            time.sleep(1)
            subprocess.run(['python', 'auto_sync_drive_to_github.py'], cwd=REPO_PATH, timeout=60)
            print('✅ SYNC COMPLETE\n')
        except: print('❌ Sync error\n')
        finally: self.syncing = False

print('File watcher started - monitoring for changes')
observer = Observer()
observer.schedule(Handler(), str(WATCH_PATH), recursive=True)
observer.start()
try:
    while True: time.sleep(1)
except KeyboardInterrupt: observer.stop()
observer.join()
