import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def __init__(self, script_to_run, files_to_watch):
        self.script_to_run = script_to_run
        self.files_to_watch = files_to_watch
        self.process = None
        self.run_script()

    def run_script(self):
        # Kill tất cả process liên quan đến wrap_menu_calendar.py và menu_calendar.py
        try:
            subprocess.run(["pkill", "-f", "wrap_menu_calendar.py"], check=False)
            subprocess.run(["pkill", "-f", "menu_calendar.py"], check=False)
            time.sleep(0.5)  # Đợi một chút để đảm bảo process được kill
        except Exception as e:
            print(f"Error killing processes: {e}")

        print(f"Running {self.script_to_run}...")
        self.process = subprocess.Popen([sys.executable, self.script_to_run])

    def on_modified(self, event):
        if not event.is_directory and os.path.basename(event.src_path) in self.files_to_watch:
            print(f"Detected change in {event.src_path}, restarting...")
            self.run_script()

if __name__ == "__main__":
    script_to_run = "wrap_menu_calendar.py"
    files_to_watch = ["wrap_menu_calendar.py", "menu_calendar.py"]
    event_handler = MyHandler(script_to_run, files_to_watch)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
        observer.join()