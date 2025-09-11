# Menu Calendar - Standalone App

Ứng dụng lịch hiển thị trong menu bar của macOS với hỗ trợ âm lịch Việt Nam.

## ✨ Tính năng

- 📅 Hiển thị lịch dương và âm lịch
- 🎯 Icon động theo ngày trong menu bar
- 🖱️ Click để mở popover lịch chi tiết
- 🔄 Tự động cập nhật khi hệ thống thức dậy
- ⏰ Cập nhật vào nửa đêm mỗi ngày
- 🎨 Giao diện đẹp với màu sắc phân biệt ngày trong tuần

## 🚀 Cách sử dụng

### **Chạy Standalone App (Khuyến nghị)**

```bash
open MenuCalendar_Standalone.app
```

### **Thiết lập Auto-Start**

1. **Mở System Preferences** → **Users & Groups** → **Login Items**
2. **Click "+"** và chọn `MenuCalendar_Standalone.app`
3. **Restart máy** để kiểm tra

## 🔧 Build Standalone App

### **Yêu cầu:**
- macOS 10.15+
- Python 3.x
- PyInstaller: `pip3 install pyinstaller`

### **Cách build:**

```bash
# Build Standalone App
./build_standalone.sh

# Cài đặt vào Applications (tùy chọn)
sudo cp -r MenuCalendar_Standalone.app /Applications/
```

### **Sau khi build:**
- File `MenuCalendar_Standalone.app` sẽ được tạo
- App có thể chạy độc lập, không cần Python
- Có thể copy sang máy khác và chạy ngay

## 📁 Cấu trúc project

```
menu_calendar/
├── menu_calendar.py              # Source code chính
├── images/                       # Thư mục icon các ngày
├── MenuCalendar_Standalone.app/  # Standalone App (sau khi build)
├── build_standalone.sh          # Script build Standalone
└── README.md                    # Hướng dẫn này
```

## 🛠️ Phát triển

### **Chỉnh sửa source code:**
1. Sửa file `menu_calendar.py`
2. Chạy `./build_standalone.sh` để build lại
3. Test với `open MenuCalendar_Standalone.app`

### **Debug:**
- Logs được ghi vào file log trong App Bundle
- Có thể chạy trực tiếp: `python3 menu_calendar.py`

## 📋 Troubleshooting

### **App không chạy:**
- Kiểm tra quyền thực thi: `chmod +x MenuCalendar_Standalone.app/Contents/MacOS/MenuCalendar`
- Kiểm tra thư mục `images` có trong App Bundle không

### **Auto-start không hoạt động:**
- Kiểm tra Login Items trong System Preferences
- Đảm bảo checkbox được tick

## 🎯 Kết luận

**MenuCalendar_Standalone.app** là phiên bản hoàn hảo:
- ✅ Không cần Python dependencies
- ✅ Chạy được trên mọi máy macOS 10.15+
- ✅ Dễ dàng chia sẻ và cài đặt
- ✅ Tích hợp tốt với macOS Login Items

**Chúc bạn sử dụng vui vẻ!** 🎉
