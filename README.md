Menu Calendar - A Menu Bar Calendar for macOS
Overview
Menu Calendar is a lightweight macOS menu bar application displaying the current date with dynamic icons and a popover calendar view. It supports both Gregorian and Lunar calendars, auto-updates on system wake/sleep, and schedules midnight refreshes.
Features

Menu Bar Display: Shows weekday and day with icon (e.g., calendar_1_icon.png for day 1).
Popover Calendar: Interactive monthly calendar with day clicks for navigation.
Dual Calendar Support: Gregorian and Vietnamese Lunar dates via lunarcalendar library.
Auto-Updates: Refreshes on system wakeup, midnight, and manual toggle.
Logging: Detailed logs in menu_calendar.log for debugging.
Clickable Elements: Navigate months/years via clicks on labels.
Resource Handling: Supports PyInstaller bundles for standalone deployment.

Requirements

macOS 10.15+
Python 3.x
PyObjC (pip install pyobjc)
PyInstaller (pip install pyinstaller)
Lunarcalendar (pip install lunarcalendar)

Installation

Clone the repository:git clone https://github.com/haon2409/menu-calendar.git
cd menu-calendar


Install dependencies:pip install pyobjc pyinstaller lunarcalendar


Build the standalone app:chmod +x build_standalone.sh
./build_standalone.sh


The built app (MenuCalendar_Standalone.app) will be in the project root.

File Structure

menu_calendar.py: Core application logic.
build_standalone.sh: Script to build the standalone app with PyInstaller.
images/: Folder with icons (e.g., MyIcon.icns, calendar_{day}_icon.png).
menu_calendar.spec: Generated PyInstaller spec file (temporary).

Usage

Run MenuCalendar_Standalone.app (or python menu_calendar.py for development).
The app appears in the menu bar with the current weekday and day icon.
Click the menu bar icon to toggle the calendar popover.
Click day labels to navigate months; view Lunar dates on hover/click.
The app auto-refreshes at midnight or on system wakeup.

Notes

Icons must be in images/ (e.g., calendar_1_icon.png to calendar_31_icon.png).
Logs are saved to menu_calendar.log in the script directory.
Standalone build requires no Python installation; copy to /Applications/ and run.
Fallback to text if icons are missing.

Troubleshooting

Icons not showing: Ensure images/ contains required PNG/ICNS files.
Build fails: Verify PyInstaller and dependencies; check logs for errors.
No Lunar dates: Install lunarcalendar and confirm Vietnamese locale support.
Updates not working: Review menu_calendar.log for wakeup/midnight scheduling issues.

License
MIT License. See LICENSE for details.