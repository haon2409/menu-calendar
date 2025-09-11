#!/usr/bin/env python3
import objc
from AppKit import (
    NSApplication, NSStatusBar, NSPopover, NSView, NSTextField, NSMakeRect, 
    NSColor, NSSize, NSButton, NSRoundedBezelStyle, NSCenterTextAlignment, 
    NSFont, NSImage, NSMutableAttributedString, NSMenu, 
    NSMenuItem, NSMakePoint, NSTimer, NSTextAttachment
)
from Foundation import (
    NSObject, NSAttributedString, NSDictionary, NSNotificationCenter, NSDistributedNotificationCenter
)
from datetime import datetime, timedelta
import calendar
from lunarcalendar import Converter, Solar
import os
import logging

# Thiết lập logging
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "menu_calendar.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Biến toàn cục cho ngày cập nhật cuối cùng
last_update_date = None

# Lớp WakeupObserver để lắng nghe sự kiện đánh thức
class WakeupObserver(NSObject):
    def initWithCallback_(self, callback):
        self = objc.super(WakeupObserver, self).init()
        if self:
            self.callback = callback
        return self

    def onWakeup_(self, notification):
        try:
            logging.info("System wakeup event detected, triggering calendar update check")
            self.callback()
        except Exception as e:
            logging.error(f"Error handling wakeup event: {str(e)}")

# Hàm lên lịch cập nhật vào nửa đêm
def schedule_midnight_update(target, selector):
    try:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        interval = (next_midnight - now).total_seconds()
        
        timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval,
            target,
            selector,
            None,
            False
        )
        logging.info(f"Scheduled midnight update in {interval} seconds")
        return timer
    except Exception as e:
        logging.error(f"Error scheduling midnight update: {str(e)}")
        return None

          
class ClickableTextField(NSTextField):
    def init(self):
        self = objc.super(ClickableTextField, self).init()
        if self:
            self.target = None
            self.action = None
        return self

    def mouseDown_(self, event):
        logging.info("Mouse clicked on '...'")
        if self.target and self.action:
            NSApplication.sharedApplication().sendAction_to_from_(self.action, self.target, self)

class ClickableDayLabel(NSTextField):
    def init(self):
        self = objc.super(ClickableDayLabel, self).init()
        if self:
            self.target = None
            self.action = None
        return self

    def mouseDown_(self, event):
        pass  # Bỏ qua click trái

    def rightMouseDown_(self, event):
        pass  # Không có chức năng nào cho right-click

class CalendarView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(CalendarView, self).initWithFrame_(frame)
        if self:
            self.current_date = datetime.now()
            self.current_month = self.current_date.month
            self.current_year = self.current_date.year
            self.padding = 30
            self.day_labels = []
            self.date_labels = []
            self.lunar_label = None
            self.timer = None
            self.setupUI()
        return self

    def setupUI(self):
        month_name = "Tháng " + str(self.current_month)
        title = f"{month_name} {self.current_year}"

        offset = 30
        self.lunar_label = NSTextField.alloc().init()
        self.lunar_label.initWithFrame_(NSMakeRect(30, 490 + offset, 300, 30))
        self.lunar_label.setBezeled_(False)
        self.lunar_label.setDrawsBackground_(False)
        self.lunar_label.setEditable_(False)
        self.lunar_label.setTextColor_(NSColor.systemGrayColor())
        self.addSubview_(self.lunar_label)

        title_label = NSTextField.alloc().init()
        title_label.initWithFrame_(NSMakeRect(30, 450 + offset, 300, 30))
        title_label.setStringValue_(title)
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setSelectable_(False)
        self.addSubview_(title_label)

        title_attributes = NSDictionary.dictionaryWithObjects_forKeys_(
            [NSColor.whiteColor(), NSFont.systemFontOfSize_(12)], 
            ["NSColor", "NSFont"]
        )

        prev_button = NSButton.alloc().init()
        prev_button.initWithFrame_(NSMakeRect(320, 493, 40, 20))
        prev_title = NSAttributedString.alloc().initWithString_attributes_("←", title_attributes)
        prev_button.setAttributedTitle_(prev_title)
        prev_button.setBezelStyle_(NSRoundedBezelStyle)
        prev_button.setTarget_(self)
        prev_button.setAction_("prevMonth:")
        prev_button.setEnabled_(True)
        prev_button.setRefusesFirstResponder_(True)
        self.addSubview_(prev_button)

        self.current_button = NSButton.alloc().init()
        self.current_button.initWithFrame_(NSMakeRect(355, 493, 40, 20))
        current_title = NSAttributedString.alloc().initWithString_attributes_("●", title_attributes)
        self.current_button.setAttributedTitle_(current_title)
        self.current_button.setBezelStyle_(NSRoundedBezelStyle)
        self.current_button.setTarget_(self)
        self.current_button.setAction_("currentMonth:")
        self.current_button.setRefusesFirstResponder_(True)
        self.addSubview_(self.current_button)

        next_button = NSButton.alloc().init()
        next_button.initWithFrame_(NSMakeRect(390, 493, 40, 20))
        next_title = NSAttributedString.alloc().initWithString_attributes_("→", title_attributes)
        next_button.setAttributedTitle_(next_title)
        next_button.setBezelStyle_(NSRoundedBezelStyle)
        next_button.setTarget_(self)
        next_button.setAction_("nextMonth:")
        next_button.setEnabled_(True)
        next_button.setRefusesFirstResponder_(True)
        self.addSubview_(next_button)

        self.updateButtonStates()
        self.createDayLabels()
        self.updateCalendar()
        self.setNeedsDisplay_(True)

    def createDayLabels(self):
        days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        offset = 30
        for i, day in enumerate(days):
            label = NSTextField.alloc().init()
            label.initWithFrame_(NSMakeRect(self.padding + i * (55 + 4), 400 + offset + 10, 55, 30))
            label.setStringValue_(day)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setAlignment_(NSCenterTextAlignment)
            label.setFont_(NSFont.boldSystemFontOfSize_(15))

            if i < 5:
                label.setTextColor_(NSColor.systemTealColor())
            else:
                label.setTextColor_(NSColor.systemOrangeColor())
            self.addSubview_(label)
            self.day_labels.append(label)

    def updateCalendar(self):
        self.updateCalendarUI()

    def updateCalendarUI(self):
        logging.info(f"Updating UI with month: {self.current_month}, year: {self.current_year}")
        for label in self.date_labels:
            label.removeFromSuperview()
        self.date_labels = []

        offset = 30
        first_weekday, days_in_month = calendar.monthrange(self.current_year, self.current_month)
        prev_month = self.current_month - 1 if self.current_month > 1 else 12
        prev_year = self.current_year if self.current_month > 1 else self.current_year - 1
        _, days_in_prev_month = calendar.monthrange(prev_year, prev_month)

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        start_date = datetime(self.current_year, self.current_month, 1) - timedelta(days=first_weekday)
        day_offset = 0

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                day_label = ClickableDayLabel.alloc().init()
                day_label.initWithFrame_(NSMakeRect(self.padding + col * (55 + 4), 340 + offset - row * 68, 55, 68))
                day_label.setBezeled_(False)
                day_label.setDrawsBackground_(False)
                day_label.setEditable_(False)
                day_label.setAlignment_(NSCenterTextAlignment)

                current_date = datetime.now()
                day_offset += 1

                if day == current_date.day and self.current_month == current_date.month and self.current_year == current_date.year:
                    circle_diameter = 19
                    image = NSImage.alloc().initWithSize_(NSSize(circle_diameter, circle_diameter))
                    image.lockFocus()
                    circle_path = objc.lookUpClass("NSBezierPath").bezierPathWithOvalInRect_(
                        NSMakeRect(0, 0, circle_diameter, circle_diameter)
                    )
                    NSColor.systemOrangeColor().setFill()
                    circle_path.fill()
                    day_str = str(day)
                    day_attributes = {
                        "NSFont": NSFont.systemFontOfSize_(12),
                        "NSColor": NSColor.blackColor(),
                    }
                    day_attr_string = NSAttributedString.alloc().initWithString_attributes_(day_str, day_attributes)
                    text_size = day_attr_string.size()
                    day_attr_string.drawAtPoint_(NSMakePoint((circle_diameter - text_size.width) / 2, (circle_diameter - text_size.height) / 2))
                    image.unlockFocus()
                    
                    attachment = NSTextAttachment.alloc().init()
                    attachment.setImage_(image)                    
                    day_label.setFrameOrigin_(NSMakePoint(self.padding + col * (55 + 4) + 14, 340 + offset - row * 68 + 2))
                    day_label.setAttributedStringValue_(NSAttributedString.attributedStringWithAttachment_(attachment))                    
                else:
                    if day == 0:
                        day_label.setTextColor_(NSColor.grayColor())
                    else:
                        day_label.setTextColor_(NSColor.labelColor())
                    day_label.setFont_(NSFont.systemFontOfSize_(12))
                    day_label.setStringValue_(str(day) if day != 0 else "")

                day_label.target = self
                self.addSubview_(day_label)
                self.date_labels.append(day_label)

        today = datetime.now()
        solar_today = Solar(today.year, today.month, today.day)
        lunar_today = Converter.Solar2Lunar(solar_today)
        self.lunar_label.setStringValue_(f"Âm lịch: {lunar_today.day:02d}/{lunar_today.month:02d}, {lunar_today.year}")
        self.subviews()[1].setStringValue_(f"Tháng {self.current_month}, {self.current_year}")

    def updateButtonStates(self):
        current_date = datetime.now()
        is_current_month = (self.current_month == current_date.month and self.current_year == current_date.year)
        self.current_button.setEnabled_(not is_current_month)

    def prevMonth_(self, sender):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.updateCalendar()
        self.updateButtonStates()

    def nextMonth_(self, sender):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.updateCalendar()
        self.updateButtonStates()

    def currentMonth_(self, sender):
        self.current_date = datetime.now()
        self.current_month = self.current_date.month
        self.current_year = self.current_date.year
        self.updateCalendar()
        self.updateButtonStates()

class CalendarAppDelegate(NSObject):
    def init(self):
        self = objc.super(CalendarAppDelegate, self).init()
        if self:
            logging.info("Initializing CalendarAppDelegate")
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)
            self.updateStatusBar()

            self.popover = NSPopover.alloc().init()
            self.calendar_view = CalendarView.alloc().initWithFrame_(NSMakeRect(0, 0, 469, 450))
            if self.calendar_view:
                self.popover.setContentSize_(NSSize(469, 580))
                self.popover.setContentViewController_(objc.lookUpClass("NSViewController").alloc().initWithNibName_bundle_(None, None))
                self.popover.contentViewController().setView_(self.calendar_view)
                self.calendar_view.setFrameOrigin_(NSMakePoint(0, 580 - 450))
            else:
                logging.error("Failed to initialize CalendarView")

            self.status_item.button().setAction_("togglePopover:")
            self.status_item.button().setTarget_(self)
            self.popover.setAnimates_(False)
            self.popover.setBehavior_(1)

            # Khởi tạo ngày cập nhật cuối cùng
            global last_update_date
            last_update_date = datetime.now().date()
            logging.info(f"Initialized last_update_date to {last_update_date}")

            # Thiết lập bộ quan sát sự kiện đánh thức
            self.setup_wakeup_listener()

            # Lên lịch cập nhật vào nửa đêm
            self.schedule_midnight_update()


            # Thêm timer định kỳ để đảm bảo cập nhật
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                60.0,  # Kiểm tra mỗi phút
                self,
                "check_and_update_date",
                None,
                True
            )
            logging.info("Scheduled periodic date check every 60 seconds")

        return self

    def setup_wakeup_listener(self):
        try:
            observer = WakeupObserver.alloc().initWithCallback_(self.check_and_update_date)
            center = NSDistributedNotificationCenter.defaultCenter()
            center.addObserver_selector_name_object_(
                observer,
                objc.selector(observer.onWakeup_, signature=b"v@:@"),
                "com.apple.screenIsUnlocked",
                None
            )
            logging.info("Wakeup listener setup successfully using NSDistributedNotificationCenter")
            self.wakeup_observer = observer  # Lưu tham chiếu để tránh bị thu hồi
        except Exception as e:
            logging.error(f"Error setting up wakeup listener: {str(e)}")

    def check_and_update_date(self):
        global last_update_date
        try:
            current_date = datetime.now().date()
            logging.info(f"check_and_update_date called, current_date: {current_date}, last_update_date: {last_update_date}")
            
            if current_date != last_update_date:
                self.updateCalendar_(None)
                last_update_date = current_date
                self.schedule_midnight_update()
                logging.info(f"Date updated to {current_date}")
            else:
                logging.info("No date update needed (same as last update)")
        except Exception as e:
            logging.error(f"Error in check_and_update_date: {str(e)}")

    def schedule_midnight_update(self):
        schedule_midnight_update(self, "check_and_update_date")

    def updateStatusBar(self):
        try:
            current_date = datetime.now()
            weekday = current_date.weekday()
            day = current_date.day
            days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
            weekday_str = days_vn[weekday] if weekday != 6 else "Chủ Nhật"
            base_path = "/Users/haonguyen/Projects/menu/menu_calendar/images/"
            icon_name = f"{base_path}calendar_{day}_icon.png"
            icon = NSImage.alloc().initWithContentsOfFile_(icon_name)
            date_str = f" {weekday_str}"
            mutable_attr_string = NSMutableAttributedString.alloc().initWithString_(date_str)
            if icon:
                attachment = NSTextAttachment.alloc().init()
                attachment.setImage_(icon)
                attachment.setBounds_(NSMakeRect(0, -4, 20, 20))
                attachment_string = NSAttributedString.attributedStringWithAttachment_(attachment)
                final_string = NSMutableAttributedString.alloc().initWithAttributedString_(attachment_string)
                final_string.appendAttributedString_(mutable_attr_string)
                self.status_item.button().setAttributedTitle_(final_string)
            else:
                logging.warning(f"Icon file {icon_name} not found, using text-only title")
                self.status_item.button().setAttributedTitle_(mutable_attr_string)
            logging.info(f"Updated status bar to day {day}, weekday {weekday_str}")
        except Exception as e:
            logging.error(f"Error updating status bar: {str(e)}")

    def updateCalendar_(self, notification):
        try:
            current_date = datetime.now()
            logging.info(f"Updating calendar at {current_date}, setting to {current_date.date()}")
            self.calendar_view.current_date = current_date
            self.calendar_view.current_month = current_date.month
            self.calendar_view.current_year = current_date.year
            self.updateStatusBar()
            self.calendar_view.updateCalendar()
        except TimeoutError as e:
            logging.error(f"Timeout error during calendar update: {str(e)}")
        except Exception as e:
            logging.error(f"Error updating calendar: {str(e)}")

    def togglePopover_(self, sender):
        try:
            if self.popover.isShown():
                self.popover.close()
                logging.info("Closed popover")
            else:
                self.popover.showRelativeToRect_ofView_preferredEdge_(sender.bounds(), sender, 3)
                self.popover.contentViewController().view().window().makeKeyAndOrderFront_(None)
                logging.info("Opened popover")
        except Exception as e:
            logging.error(f"Error toggling popover: {str(e)}")

    def applicationDidFinishLaunching_(self, notification):
        NSApplication.sharedApplication().setActivationPolicy_(1)
        logging.info("Application finished launching")

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        return False

    def applicationWillTerminate_(self, notification):
        NSNotificationCenter.defaultCenter().removeObserver_(self.wakeup_observer)
        NSDistributedNotificationCenter.defaultCenter().removeObserver_(self.wakeup_observer)
        logging.info("Application terminated, cleaned up observers")

if __name__ == "__main__":
    try:
        logging.info("Starting menu calendar application")
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(1)
        delegate = CalendarAppDelegate.alloc().init()
        app.setDelegate_(delegate)
        app.run()
    except Exception as e:
        logging.error(f"Error starting application: {str(e)}")