#!/usr/bin/env python3
import subprocess
from datetime import datetime, timedelta
from Foundation import NSDistributedNotificationCenter, NSObject
from AppKit import NSApplication, NSTimer
from PyObjCTools import AppHelper
import objc
import os
import logging

MENU_CALENDAR_PATH = "/Users/haonguyen/Projects/menu/menu_calendar/menu_calendar.py"
last_update_date = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "wrap_menu_calendar.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clear_logs():
    """Xóa các file log stdout và stderr."""
    log_files = ["/tmp/menucalendar.out", "/tmp/menucalendar.err"]
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                os.remove(log_file)
                logging.info(f"Cleared log file: {log_file}")
        except Exception as e:
            logging.error(f"Error clearing log file {log_file}: {str(e)}")   

def notify_update():
    """Gửi thông báo để menu_calendar.py cập nhật lịch."""
    try:
        center = NSDistributedNotificationCenter.defaultCenter()
        center.postNotificationName_object_userInfo_(
            "com.haonguyen.menucalendar.update",
            None,
            None
        )
        logging.info("Sent update notification to menu_calendar")
    except Exception as e:
        logging.error(f"Error sending update notification: {str(e)}")

def check_and_update_date():
    """Kiểm tra và cập nhật ngày nếu cần."""
    try:
        global last_update_date
        current_date = datetime.now().date()
        logging.info(f"check_and_update_date called, current_date: {current_date}, last_update_date: {last_update_date}")
        
        if current_date != last_update_date:
            notify_update()
            last_update_date = current_date
            schedule_midnight_update()
            logging.info(f"Date updated to {current_date}")
        else:
            logging.info("No date update needed (same as last update)")
    except Exception as e:
        logging.error(f"Error in check_and_update_date: {str(e)}")

def start_calendar(process):
    """Khởi động menu_calendar.py nếu chưa chạy và gửi thông báo cập nhật."""
    try:
        if not process or process.poll() is not None:
            process = subprocess.Popen(["/usr/bin/python3", MENU_CALENDAR_PATH])
            logging.info("Started menu_calendar.py process")
        notify_update()
        return process
    except Exception as e:
        logging.error(f"Error starting calendar: {str(e)}")
        return None

class WakeupObserver(NSObject):
    """Observer để lắng nghe sự kiện wakeup từ NSWorkspace."""
    def initWithCallback_(self, callback):
        self = objc.super(WakeupObserver, self).init()
        if self:
            self.callback = callback
        return self

    def onWakeup_(self, notification):
        """Xử lý khi hệ thống wakeup."""
        try:
            logging.info("System wakeup event detected, triggering calendar update check")
            self.callback()
        except Exception as e:
            logging.error(f"Error handling wakeup event: {str(e)}")

def setup_wakeup_listener(callback):
    """Thiết lập observer để lắng nghe sự kiện wakeup."""
    try:
        observer = WakeupObserver.alloc().initWithCallback_(callback)
        center = NSDistributedNotificationCenter.defaultCenter()
        
        center.addObserver_selector_name_object_(
            observer,
            objc.selector(observer.onWakeup_, signature=b"v@:@"),
            "com.apple.screenIsUnlocked",
            None
        )
        logging.info("Wakeup listener setup successfully")
        return observer
    except Exception as e:
        logging.error(f"Error setting up wakeup listener: {str(e)}")
        return None

def schedule_midnight_update():
    """Lên lịch cập nhật vào 0h ngày hôm sau."""
    try:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        interval = (next_midnight - now).total_seconds()
        
        timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval,
            check_and_update_date,
            "check_and_update_date",
            None,
            False
        )
        logging.info(f"Scheduled midnight update in {interval} seconds")
        return timer
    except Exception as e:
        logging.error(f"Error scheduling midnight update: {str(e)}")
        return None

def main():
    try:
        # Xóa log trước khi khởi động
        clear_logs()
        
        global last_update_date
        process = None
        
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(1)
        
        logging.info("Application started")
        process = start_calendar(process)
        last_update_date = datetime.now().date()

        observer = setup_wakeup_listener(check_and_update_date)
        if not observer:
            logging.error("Failed to setup wakeup observer")
            return

        timer = schedule_midnight_update()
        if not timer:
            logging.error("Failed to schedule midnight update")
            return

        AppHelper.runConsoleEventLoop()
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()