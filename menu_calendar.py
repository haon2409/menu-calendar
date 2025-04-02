import objc
from AppKit import (
    NSApplication, NSStatusBar, NSPopover, NSView, NSTextField, NSMakeRect, 
    NSColor, NSSize, NSButton, NSRoundedBezelStyle, NSCenterTextAlignment, 
    NSFont, NSImage, NSMutableAttributedString, NSTextAttachment, NSMenu, 
    NSMenuItem, NSMakePoint, NSTimer
)
from Foundation import (
    NSObject, NSAttributedString, NSDictionary, NSDistributedNotificationCenter
)
from datetime import datetime, timedelta
import calendar
from lunarcalendar import Converter, Solar
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Định nghĩa phạm vi (scope) truy cập và đường dẫn file
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/tasks'
]
CLIENT_SECRET_FILE = '/Users/haonguyen/Projects/menu/menu_calendar/client_secret_856485619448-q2tqisv610002j405r3er1o48jm7qrgo.apps.googleusercontent.com.json'
TOKEN_FILE = '/Users/haonguyen/Projects/menu/menu_calendar/token.json'

def get_service(api_name, api_version):
    """Tạo dịch vụ cho API được chỉ định (Tasks)."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        try:
            print("Access token đã hết hạn, đang làm mới bằng refresh token...")
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("Token đã được làm mới và lưu lại.")
        except RefreshError as e:
            print(f"Lỗi khi làm mới token: {e}. Yêu cầu đăng nhập lại...")
            creds = None
    
    if not creds or not creds.valid:
        print("Yêu cầu đăng nhập để cấp quyền truy cập...")
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, 
            SCOPES
        )
        # Nếu cần prompt='consent', áp dụng sau khi tạo flow
        flow.prompt = 'consent'  # Tùy chọn, chỉ thêm nếu cần buộc consent
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("Đăng nhập thành công! Token đã được lưu.")
    
    service = build(api_name, api_version, credentials=creds)
    return service

class ClickableTextField(NSTextField):
    def init(self):
        self = objc.super(ClickableTextField, self).init()
        if self:
            self.target = None
            self.action = None
        return self

    def mouseDown_(self, event):
        print("Mouse clicked on '...'")
        if self.target and self.action:
            NSApplication.sharedApplication().sendAction_to_from_(self.action, self.target, self)

class ClickableDayLabel(NSTextField):
    def init(self):
        self = objc.super(ClickableDayLabel, self).init()
        if self:
            self.target = None
            self.action = None
            self.task_date = None
        return self

    def mouseDown_(self, event):
        pass  # Bỏ qua click trái

    def rightMouseDown_(self, event):
        print(f"Right-clicked on day: {self.stringValue()} - Date: {self.task_date}")
        
        menu = NSMenu.alloc().initWithTitle_("Day Menu")
        add_task_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Add Task", "addTaskAction:", ""
        )
        add_task_item.setTarget_(self.target)
        add_task_item.setRepresentedObject_(self)
        menu.addItem_(add_task_item)
        
        NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

class TaskActionHandler(NSObject):
    def initWithTaskLabel_taskId_tasksService_(self, task_label, task_id, tasks_service):
        self = objc.super(TaskActionHandler, self).init()
        if self:
            self.task_label = task_label
            self.task_id = task_id
            self.tasks_service = tasks_service
            self.tasklist_id = None
        return self

    def completeAction_(self, sender):
        if not self.tasklist_id:
            tasklists = self.tasks_service.tasklists().list().execute()
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == "My List":
                    self.tasklist_id = tasklist['id']
                    break

        task = self.tasks_service.tasks().get(tasklist=self.tasklist_id, task=self.task_id).execute()
        current_status = task.get('status', 'needsAction')

        if current_status == 'needsAction':
            task['status'] = 'completed'
            task['completed'] = datetime.utcnow().isoformat() + 'Z'
        else:
            task['status'] = 'needsAction'
            if 'completed' in task:
                del task['completed']

        updated_task = self.tasks_service.tasks().update(
            tasklist=self.tasklist_id,
            task=self.task_id,
            body=task
        ).execute()

        print(f"Task '{self.task_label.stringValue()}' updated to status: {updated_task['status']}")
        NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_(
            "com.haonguyen.menucalendar.update",
            None
        )

    def editAction_(self, sender):
        if not self.tasklist_id:
            tasklists = self.tasks_service.tasklists().list().execute()
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == "My List":
                    self.tasklist_id = tasklist['id']
                    break

        task = self.tasks_service.tasks().get(tasklist=self.tasklist_id, task=self.task_id).execute()

        alert = objc.lookUpClass("NSAlert").alloc().init()
        alert.setMessageText_("Edit Task")
        alert.setInformativeText_("Enter new task details:")
        alert.addButtonWithTitle_("OK")
        alert.addButtonWithTitle_("Cancel")

        # Tạo container view để chứa các trường input
        container_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 80))
        
        # Trường nhập title
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 50, 60, 20))
        title_label.setStringValue_("Title:")
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        container_view.addSubview_(title_label)
        
        title_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 50, 220, 20))
        title_field.setStringValue_(task.get('title', ''))
        container_view.addSubview_(title_field)
        
        # Trường nhập details
        details_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 20, 60, 20))
        details_label.setStringValue_("Details:")
        details_label.setBezeled_(False)
        details_label.setDrawsBackground_(False)
        details_label.setEditable_(False)
        container_view.addSubview_(details_label)
        
        details_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 20, 220, 20))
        details_field.setStringValue_(task.get('notes', ''))
        container_view.addSubview_(details_field)
        
        alert.setAccessoryView_(container_view)

        response = alert.runModal()
        if response == 1000:
            new_title = title_field.stringValue().strip()
            new_details = details_field.stringValue().strip()
            if new_title:
                task['title'] = new_title
                task['notes'] = new_details
                self.tasks_service.tasks().update(
                    tasklist=self.tasklist_id,
                    task=self.task_id,
                    body=task
                ).execute()

                print(f"Task '{self.task_label.stringValue()}' updated to new title: {new_title}")
                NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_(
                    "com.haonguyen.menucalendar.update",
                    None
                )

    def removeAction_(self, sender):
        if not self.tasklist_id:
            tasklists = self.tasks_service.tasklists().list().execute()
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == "My List":
                    self.tasklist_id = tasklist['id']
                    break

        self.tasks_service.tasks().delete(
            tasklist=self.tasklist_id,
            task=self.task_id
        ).execute()

        print(f"Task '{self.task_label.stringValue()}' removed")
        NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_(
            "com.haonguyen.menucalendar.update",
            None
        )

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
            self.task_handlers = []
            self.task_info = {}
            self.lunar_label = None
            self.tasks_by_date = {}
            self.tasks_service = get_service('tasks', 'v1')
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

    def get_tasklist_id(self):
        tasklists = self.tasks_service.tasklists().list().execute()
        for tasklist in tasklists.get('items', []):
            if tasklist['title'] == "My List":
                return tasklist['id']
        new_tasklist = {'title': "My List"}
        result = self.tasks_service.tasklists().insert(body=new_tasklist).execute()
        return result['id']

    def get_tasks(self, due_min, due_max):
        self.tasks_by_date = {}
        due_min_iso = due_min + 'T00:00:00.000Z'
        due_max_iso = due_max + 'T23:59:59.999Z'

        tasklist_id = self.get_tasklist_id()
        all_tasks = []
        page_token = None
        while True:
            tasks = self.tasks_service.tasks().list(
                tasklist=tasklist_id,
                maxResults=100,
                pageToken=page_token,
                dueMin=due_min_iso,
                dueMax=due_max_iso,
                showCompleted=True,
                showHidden=True
            ).execute()
            all_tasks.extend(tasks.get('items', []))
            page_token = tasks.get('nextPageToken')
            if not page_token:
                break

        for task in all_tasks:
            due = task.get('due')
            if due:
                due_date = datetime.strptime(due, "%Y-%m-%dT%H:%M:%S.%fZ").date()
                if due_date not in self.tasks_by_date:
                    self.tasks_by_date[due_date] = []
                self.tasks_by_date[due_date].append(task)

        # Sắp xếp tasks trong mỗi ngày theo position (ngược lại)
        for date in self.tasks_by_date:
            self.tasks_by_date[date].sort(key=lambda x: x.get('position', '00000000000000000000'), reverse=True)

    def updateCalendar(self):
        self.updateCalendarUI()
        self.loadTasks()  # Tải tasks ngay lập tức thay vì delay

    def updateCalendarUI(self):
        for label in self.date_labels:
            label.removeFromSuperview()
        self.date_labels = []
        self.task_handlers = []
        self.task_info = {}

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
                task_date = (start_date + timedelta(days=day_offset)).date()
                day_offset += 1

                day_label.task_date = task_date

                # Xử lý ngày hiện tại với nền tròn
                if day == current_date.day and self.current_month == current_date.month and self.current_year == current_date.year:
                    # Tạo hình tròn chứa số ngày
                    circle_diameter = 19  # Đường kính vừa phải
                    image = NSImage.alloc().initWithSize_(NSSize(circle_diameter, circle_diameter))
                    image.lockFocus()
                    
                    # Vẽ hình tròn
                    circle_path = objc.lookUpClass("NSBezierPath").bezierPathWithOvalInRect_(
                        NSMakeRect(0, 0, circle_diameter, circle_diameter)
                    )
                    NSColor.systemOrangeColor().setFill()  # Màu tương phản
                    circle_path.fill()
                    
                    # Vẽ số ngày
                    day_str = str(day)
                    day_attributes = {
                        "NSFont": NSFont.systemFontOfSize_(12),
                        "NSColor": NSColor.blackColor(),
                    }
                    day_attr_string = NSAttributedString.alloc().initWithString_attributes_(day_str, day_attributes)
                    text_size = day_attr_string.size()
                    day_attr_string.drawAtPoint_(NSMakePoint((circle_diameter - text_size.width) / 2, (circle_diameter - text_size.height) / 2))
                    
                    image.unlockFocus()
                    
                    # Tạo attachment cho hình tròn
                    attachment = NSTextAttachment.alloc().init()
                    attachment.setImage_(image)                    
                    day_label.setFrameOrigin_(NSMakePoint(self.padding + col * (55 + 4) + 14, 340 + offset - row * 68 + 2))
                    day_label.setAttributedStringValue_(NSAttributedString.attributedStringWithAttachment_(attachment))                    
                else:
                    # Các ngày khác không có nền tròn
                    if day == 0 or task_date.month != self.current_month:
                        day_label.setTextColor_(NSColor.grayColor())
                    else:
                        day_label.setTextColor_(NSColor.labelColor())
                    day_label.setFont_(NSFont.systemFontOfSize_(12))
                    day_label.setStringValue_(str(day) if day != 0 else str(task_date.day))

                day_label.target = self
                self.addSubview_(day_label)
                self.date_labels.append(day_label)

        today = datetime.now()
        solar_today = Solar(today.year, today.month, today.day)
        lunar_today = Converter.Solar2Lunar(solar_today)
        self.lunar_label.setStringValue_(f"Âm lịch: {lunar_today.day:02d}/{lunar_today.month:02d}, {lunar_today.year}")
        self.subviews()[1].setStringValue_(f"Tháng {self.current_month}, {self.current_year}")

    def loadTasks(self):
        offset = 30
        first_weekday, days_in_month = calendar.monthrange(self.current_year, self.current_month)
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        due_min = (datetime(self.current_year, self.current_month, 1) - timedelta(days=first_weekday)).strftime("%Y-%m-%d")
        last_week = cal[-1]
        if 0 in last_week:
            last_day_of_month = days_in_month
            next_days = [d for d in last_week if d == 0]
            max_next_day = len(next_days)
            due_max_date = datetime(self.current_year, self.current_month, last_day_of_month) + timedelta(days=max_next_day)
        else:
            due_max_date = datetime(self.current_year, self.current_month, max([day for week in cal for day in week if day != 0]))
        due_max = due_max_date.strftime("%Y-%m-%d")

        self.get_tasks(due_min, due_max)

        start_date = datetime(self.current_year, self.current_month, 1) - timedelta(days=first_weekday)
        day_offset = 0

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                task_date = (start_date + timedelta(days=day_offset)).date()
                day_offset += 1

                base_y = 340 + offset - row * 68
                task_labels = []
                tasks = self.tasks_by_date.get(task_date, [])
                for i in range(4):
                    if i == 3 and len(tasks) > 3:
                        task_label = ClickableTextField.alloc().init()
                        task_label = task_label.initWithFrame_(NSMakeRect(self.padding + col * (55 + 4), base_y + 50 - (i * 12) - 10, 55, 10))
                        task_label.setStringValue_("...")
                        task_label.setBezeled_(False)
                        task_label.setDrawsBackground_(True)
                        task_label.setBackgroundColor_(NSColor.systemCyanColor())
                        task_label.setTextColor_(NSColor.blackColor())
                        task_label.setEditable_(False)
                        task_label.setAlignment_(NSCenterTextAlignment)
                        task_label.setFont_(NSFont.systemFontOfSize_(8))
                        task_label.target = self
                        task_label.action = "showTaskPopover:"
                        self.task_info[task_label] = {
                            'day': day if day != 0 else task_date.day,
                            'task_labels': task_labels,
                            'tasks': tasks
                        }
                    elif i < len(tasks):
                        task_label = NSTextField.alloc().init()
                        task_label.initWithFrame_(NSMakeRect(self.padding + col * (55 + 4), base_y + 50 - (i * 12) - 10, 55, 10))
                        full_title = tasks[i].get('title', 'No Title')
                        max_length = 10
                        display_title = full_title if len(full_title) <= max_length else full_title[:max_length - 3] + '...'

                        task_label.setStringValue_(display_title)
                        
                        # Tạo tooltip với title và details
                        details = tasks[i].get('notes', '')
                        tooltip = full_title
                        if details:
                            tooltip += f"\n{details}"
                        task_label.setToolTip_(tooltip)

                        menu = NSMenu.alloc().initWithTitle_("Task Menu")
                        handler = TaskActionHandler.alloc().initWithTaskLabel_taskId_tasksService_(
                            task_label, tasks[i].get('id'), self.tasks_service
                        )
                        self.task_handlers.append(handler)

                        task_status = tasks[i].get('status', 'needsAction')
                        menu_title = "Complete" if task_status == 'needsAction' else "Incomplete"
                        complete_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(menu_title, "completeAction:", "")
                        complete_item.setTarget_(handler)
                        menu.addItem_(complete_item)

                        edit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Edit", "editAction:", "")
                        edit_item.setTarget_(handler)
                        menu.addItem_(edit_item)

                        remove_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Remove", "removeAction:", "")
                        remove_item.setTarget_(handler)
                        menu.addItem_(remove_item)

                        task_label.setMenu_(menu)
                        task_labels.append(task_label)
                    else:
                        continue

                    task_label.setBezeled_(False)
                    task_label.setDrawsBackground_(True)
                    task_status = tasks[i].get('status', 'needsAction') if i < len(tasks) else 'needsAction'
                    if task_status == 'completed':
                        task_label.setBackgroundColor_(NSColor.grayColor())
                        task_label.setTextColor_(NSColor.blackColor())
                    else:
                        task_label.setBackgroundColor_(NSColor.systemCyanColor())
                        task_label.setTextColor_(NSColor.blackColor())

                    task_label.setEditable_(False)
                    task_label.setAlignment_(NSCenterTextAlignment)
                    task_label.setFont_(NSFont.systemFontOfSize_(8))

                    self.addSubview_(task_label)
                    self.date_labels.append(task_label)

        self.setNeedsDisplay_(True)
    
    def showAddTaskAlert_(self, sender):
        alert = objc.lookUpClass("NSAlert").alloc().init()
        alert.setMessageText_(f"Add Task for {sender.task_date}")
        alert.setInformativeText_("Enter task details:")
        alert.addButtonWithTitle_("Add")
        alert.addButtonWithTitle_("Cancel")

        # Tạo container view
        container_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 140))
        
        # Trường title
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 110, 60, 20))
        title_label.setStringValue_("Title:")
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        container_view.addSubview_(title_label)
        
        title_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 110, 220, 20))
        title_field.setStringValue_("")
        container_view.addSubview_(title_field)
        
        # Trường details
        details_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 80, 60, 20))
        details_label.setStringValue_("Details:")
        details_label.setBezeled_(False)
        details_label.setDrawsBackground_(False)
        details_label.setEditable_(False)
        container_view.addSubview_(details_label)
        
        details_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 80, 220, 20))
        details_field.setStringValue_("")
        container_view.addSubview_(details_field)
        
        # Hàng Repeat
        repeat_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 50, 60, 20))
        repeat_label.setStringValue_("Repeat:")
        repeat_label.setBezeled_(False)
        repeat_label.setDrawsBackground_(False)
        repeat_label.setEditable_(False)
        container_view.addSubview_(repeat_label)
        
        self.repeat_checkbox = objc.lookUpClass("NSButton").alloc().initWithFrame_(NSMakeRect(65, 50, 36, 20))
        self.repeat_checkbox.setButtonType_(1)  # NSButtonTypeSwitch
        self.repeat_checkbox.setTitle_("")
        self.repeat_checkbox.setTarget_(self)
        self.repeat_checkbox.setAction_("toggleRepeatOptions:")
        container_view.addSubview_(self.repeat_checkbox)
        
        # Hàng repeat options (ban đầu ẩn)
        self.repeat_options_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 30))
        self.repeat_options_view.setHidden_(True)
        
        repeat_menu = objc.lookUpClass("NSPopUpButton").alloc().initWithFrame_(NSMakeRect(70, 0, 50, 24))
        repeat_menu.addItemsWithTitles_(["1", "2", "3", "4"])
        self.repeat_options_view.addSubview_(repeat_menu)
        
        unit_menu = objc.lookUpClass("NSPopUpButton").alloc().initWithFrame_(NSMakeRect(130, 0, 80, 24))
        unit_menu.addItemsWithTitles_(["Day(s)", "Week(s)", "Month(s)"])
        self.repeat_options_view.addSubview_(unit_menu)
        
        times_menu = objc.lookUpClass("NSPopUpButton").alloc().initWithFrame_(NSMakeRect(220, 0, 50, 24))
        times_menu.addItemsWithTitles_([str(i) for i in range(2, 13)])
        self.repeat_options_view.addSubview_(times_menu)    

        container_view.addSubview_(self.repeat_options_view)
        self.repeat_options_view.setFrame_(NSMakeRect(0, 20, 300, 24))
        
        alert.setAccessoryView_(container_view)

        response = alert.runModal()
        if response == 1000:  # Nút "Add" được nhấn
            new_title = title_field.stringValue().strip()
            new_details = details_field.stringValue().strip()
            if new_title:
                tasklist_id = self.get_tasklist_id()
                base_date = sender.task_date  # Ngày được chọn
                
                # Danh sách các task sẽ được tạo
                task_bodies = []
                
                if self.repeat_checkbox.state() != 1:  # Không lặp lại
                    task_body = {
                        'title': new_title,
                        'notes': new_details,
                        'due': base_date.isoformat() + 'T00:00:00.000Z',
                        'status': 'needsAction'
                    }
                    task_bodies.append(task_body)
                else:  # Lặp lại
                    repeat_count = int(repeat_menu.titleOfSelectedItem())  # Số đơn vị lặp lại
                    unit = unit_menu.titleOfSelectedItem()  # Đơn vị: Day(s), Week(s), Month(s)
                    times = int(times_menu.titleOfSelectedItem())  # Tổng số task
                    
                    current_date = base_date
                    for i in range(times):
                        # Tính ngày đến hạn cho task hiện tại
                        if i == 0:
                            due_date = current_date
                        else:
                            if unit == "Day(s)":
                                current_date = current_date + timedelta(days=repeat_count)
                            elif unit == "Week(s)":
                                current_date = current_date + timedelta(weeks=repeat_count)
                            elif unit == "Month(s)":
                                # Tính tháng tiếp theo
                                new_month = current_date.month + repeat_count
                                new_year = current_date.year + (new_month - 1) // 12
                                new_month = (new_month - 1) % 12 + 1
                                # Lấy số ngày tối đa của tháng mới
                                max_days = calendar.monthrange(new_year, new_month)[1]
                                # Nếu ngày hiện tại vượt quá max_days, điều chỉnh thành ngày cuối tháng
                                new_day = min(current_date.day, max_days)
                                current_date = current_date.replace(year=new_year, month=new_month, day=new_day)
                            due_date = current_date
                        
                        task_body = {
                            'title': new_title,
                            'notes': new_details,
                            'due': due_date.isoformat() + 'T00:00:00.000Z',
                            'status': 'needsAction'
                        }
                        task_bodies.append(task_body)
                
                # Gọi API để tạo tất cả các task
                for task_body in task_bodies:
                    new_task = self.tasks_service.tasks().insert(
                        tasklist=tasklist_id,
                        body=task_body
                    ).execute()
                    print(f"Task '{new_title}' added for {task_body['due'][:10]} with ID: {new_task['id']}")
                
                # Cập nhật UI một lần sau khi tất cả task được tạo
                NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_(
                    "com.haonguyen.menucalendar.update",
                    None
                )

    def toggleRepeatOptions_(self, sender):
        self.repeat_options_view.setHidden_(sender.state() != 1)

    def addTaskAction_(self, sender):
        day_label = sender.representedObject()
        if day_label and day_label.task_date:
            self.showAddTaskAlert_(day_label)
        else:
            print("Error: Could not retrieve task date for adding task")

    def showTaskPopover_(self, sender):
        print("Showing popover for '...'")
        popover = NSPopover.alloc().init()
        popover.setBehavior_(1)
        popover.setAnimates_(False)

        task_info = self.task_info.get(sender, {})
        tasks = task_info.get('tasks', [])
        num_tasks = len(tasks)

        popover_height = 10 + num_tasks * 25 if num_tasks > 0 else 30
        popover_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 200, popover_height))

        button_attributes = {"NSFont": NSFont.systemFontOfSize_(10)}

        for i, task in enumerate(tasks):
            y_position = popover_height - 25 - (i * 25)
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, y_position, 120, 16))
            full_title = task.get('title', 'No Title')
            max_length = 15
            display_title = full_title if len(full_title) <= max_length else full_title[:max_length - 3] + '...'

            label.setStringValue_(display_title)
            label.setToolTip_(full_title)
            label.setBezeled_(False)
            label.setDrawsBackground_(True)
            label.setEditable_(False)
            label.setAlignment_(NSCenterTextAlignment)
            label.setFont_(NSFont.systemFontOfSize_(11))

            task_status = task.get('status', 'needsAction')
            if task_status == 'completed':
                label.setBackgroundColor_(NSColor.grayColor())
                label.setTextColor_(NSColor.blackColor())
            else:
                label.setBackgroundColor_(NSColor.systemCyanColor())
                label.setTextColor_(NSColor.blackColor())

            popover_view.addSubview_(label)

            handler = TaskActionHandler.alloc().initWithTaskLabel_taskId_tasksService_(
                label, task.get('id'), self.tasks_service
            )
            self.task_handlers.append(handler)

            complete_button = NSButton.alloc().initWithFrame_(NSMakeRect(132, y_position - 2, 36, 18))
            complete_icon = "✅" if task_status == 'needsAction' else "↩️"
            complete_title = NSAttributedString.alloc().initWithString_attributes_(complete_icon, button_attributes)
            complete_button.setAttributedTitle_(complete_title)
            complete_button.setBezelStyle_(NSRoundedBezelStyle)
            complete_button.setTarget_(handler)
            complete_button.setAction_("completeAction:")
            complete_button.setAlignment_(NSCenterTextAlignment)
            complete_button.setRefusesFirstResponder_(True)
            popover_view.addSubview_(complete_button)

            edit_button = NSButton.alloc().initWithFrame_(NSMakeRect(162, y_position - 2, 36, 18))
            edit_title = NSAttributedString.alloc().initWithString_attributes_("✏️", button_attributes)
            edit_button.setAttributedTitle_(edit_title)
            edit_button.setBezelStyle_(NSRoundedBezelStyle)
            edit_button.setTarget_(handler)
            edit_button.setAction_("editAction:")
            edit_button.setAlignment_(NSCenterTextAlignment)
            edit_button.setRefusesFirstResponder_(True)
            popover_view.addSubview_(edit_button)

            remove_button = NSButton.alloc().initWithFrame_(NSMakeRect(192, y_position - 2, 36, 18))
            remove_title = NSAttributedString.alloc().initWithString_attributes_("❌", button_attributes)
            remove_button.setAttributedTitle_(remove_title)
            remove_button.setBezelStyle_(NSRoundedBezelStyle)
            remove_button.setTarget_(handler)
            remove_button.setAction_("removeAction:")
            remove_button.setAlignment_(NSCenterTextAlignment)
            remove_button.setRefusesFirstResponder_(True)
            popover_view.addSubview_(remove_button)

        popover.setContentSize_(NSSize(230, popover_height))
        popover.setContentViewController_(objc.lookUpClass("NSViewController").alloc().init())
        popover.contentViewController().setView_(popover_view)
        popover.showRelativeToRect_ofView_preferredEdge_(sender.bounds(), sender, 2)

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
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)
            self.updateStatusBar()

            self.popover = NSPopover.alloc().init()
            self.calendar_view = CalendarView.alloc().initWithFrame_(NSMakeRect(0, 0, 469, 450))
            if self.calendar_view:
                self.popover.setContentSize_(NSSize(469, 580))
                self.popover.setContentViewController_(objc.lookUpClass("NSViewController").alloc().initWithNibName_bundle_(None, None))
                self.popover.contentViewController().setView_(self.calendar_view)
                self.calendar_view.setFrameOrigin_(NSMakePoint(0, 580 - 450))

            self.status_item.button().setAction_("togglePopover:")
            self.status_item.button().setTarget_(self)
            self.popover.setAnimates_(False)
            self.popover.setBehavior_(1)

            center = NSDistributedNotificationCenter.defaultCenter()
            center.addObserver_selector_name_object_(
                self,
                "updateCalendar:",
                "com.haonguyen.menucalendar.update",
                None
            )
        return self

    def updateStatusBar(self):
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
            self.status_item.button().setAttributedTitle_(mutable_attr_string)

    def updateCalendar_(self, notification):
        self.updateStatusBar()
        self.calendar_view.updateCalendar()

    def togglePopover_(self, sender):
        if self.popover.isShown():
            self.popover.close()
        else:
            # Hiển thị giao diện trước
            self.popover.showRelativeToRect_ofView_preferredEdge_(sender.bounds(), sender, 3)
            self.popover.contentViewController().view().window().makeKeyAndOrderFront_(None)
            
            # Sử dụng NSTimer để gọi API sau khi giao diện đã hiển thị
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.1,  # Delay 0.1 giây
                self.calendar_view,
                "loadTasks",
                None,
                False
            )

    def applicationDidFinishLaunching_(self, notification):
        NSApplication.sharedApplication().setActivationPolicy_(1)

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        return False
if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)
    delegate = CalendarAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()