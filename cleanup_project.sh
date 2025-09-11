#!/bin/bash

# Script dọn dẹp project Menu Calendar
# Chỉ giữ lại những file cần thiết

set -e

echo "🧹 Dọn dẹp project Menu Calendar..."
echo "=================================="

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Danh sách file sẽ giữ lại
KEEP_FILES=(
    "menu_calendar.py"
    "images/"
    "MenuCalendar_Standalone.app/"
    "build_standalone.sh"
    "README.md"
    ".git/"
    ".gitignore"
)

# Danh sách file sẽ xóa
DELETE_FILES=(
    "build_app.sh"
    "check_after_restart.sh"
    "check_dependencies.sh"
    "com.menucalendar.app.plist"
    "create_dmg.sh"
    "fix_standalone.sh"
    "install_menu_calendar.sh"
    "install_standalone.sh"
    "install_to_applications.sh"
    "manage_autostart.sh"
    "menu_calendar.log"
    "MenuCalendar-Installer.dmg"
    "MenuCalendar.app/"
    "requirements.txt"
    "setup_autostart.sh"
    "setup_standalone_autostart.sh"
    "SHARING_GUIDE.md"
    "STANDALONE_GUIDE.md"
    ".DS_Store"
)

print_status "Files sẽ được GIỮ LẠI:"
for file in "${KEEP_FILES[@]}"; do
    if [ -e "$file" ]; then
        print_success "✅ $file"
    else
        print_warning "⚠️  $file (không tồn tại)"
    fi
done

echo ""
print_status "Files sẽ bị XÓA:"
for file in "${DELETE_FILES[@]}"; do
    if [ -e "$file" ]; then
        print_warning "🗑️  $file"
    else
        print_success "✅ $file (đã không tồn tại)"
    fi
done

echo ""
read -p "Bạn có chắc chắn muốn dọn dẹp? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Hủy dọn dẹp"
    exit 0
fi

print_status "Bắt đầu dọn dẹp..."

# Xóa các file không cần thiết
for file in "${DELETE_FILES[@]}"; do
    if [ -e "$file" ]; then
        rm -rf "$file"
        print_success "Đã xóa: $file"
    fi
done

# Tạo README mới với hướng dẫn build Standalone
print_status "Tạo README mới..."
cat > README.md << 'EOF'
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
EOF

print_success "README.md đã được cập nhật"

# Hiển thị kết quả cuối cùng
echo ""
print_success "🎉 Dọn dẹp hoàn tất!"
echo ""
print_status "Files còn lại:"
ls -la | grep -E "(menu_calendar.py|images|MenuCalendar_Standalone.app|build_standalone.sh|README.md|\.git)"

echo ""
print_status "📋 Hướng dẫn sử dụng:"
echo "   • Chạy app: open MenuCalendar_Standalone.app"
echo "   • Build lại: ./build_standalone.sh"
echo "   • Auto-start: System Preferences → Users & Groups → Login Items"
echo ""
print_success "✅ Project đã được dọn dẹp và tối ưu!"
