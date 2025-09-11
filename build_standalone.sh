#!/bin/bash

# Script build standalone Menu Calendar App với PyInstaller
# Sử dụng: ./build_standalone.sh

set -e

echo "🚀 Building Standalone Menu Calendar App..."
echo "=========================================="

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

# Kiểm tra PyInstaller
print_status "Kiểm tra PyInstaller..."
PYINSTALLER_PATH=""
if command -v pyinstaller &> /dev/null; then
    PYINSTALLER_PATH="pyinstaller"
    print_success "PyInstaller đã sẵn sàng"
elif [ -f "/Users/haonguyen/Library/Python/3.9/bin/pyinstaller" ]; then
    PYINSTALLER_PATH="/Users/haonguyen/Library/Python/3.9/bin/pyinstaller"
    print_success "PyInstaller đã sẵn sàng (user install)"
elif python3 -m PyInstaller --version &> /dev/null; then
    PYINSTALLER_PATH="python3 -m PyInstaller"
    print_success "PyInstaller đã sẵn sàng (module)"
else
    print_error "PyInstaller chưa được cài đặt"
    echo "💡 Cài đặt: pip3 install pyinstaller"
    exit 1
fi

# Kiểm tra file Python chính
if [ ! -f "menu_calendar.py" ]; then
    print_error "menu_calendar.py không tồn tại"
    exit 1
fi

# Dọn dẹp build cũ
print_status "Dọn dẹp build cũ..."
rm -rf build/ dist/ MenuCalendar_Standalone.app
print_success "Đã dọn dẹp"

# Tạo spec file cho PyInstaller
print_status "Tạo PyInstaller spec file..."
cat > menu_calendar.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['menu_calendar.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('images', 'images'),
    ],
    hiddenimports=[
        'objc',
        'AppKit',
        'Foundation',
        'lunarcalendar',
        'lunarcalendar.Converter',
        'lunarcalendar.Solar',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MenuCalendar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/MyIcon.icns',
)

app = BUNDLE(
    exe,
    name='MenuCalendar_Standalone.app',
    icon='images/MyIcon.icns',
    bundle_identifier='com.menucalendar.standalone',
    info_plist={
        'CFBundleName': 'Menu Calendar',
        'CFBundleDisplayName': 'Menu Calendar',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleDocumentTypes': [],
        'NSAppleScriptEnabled': False,
        'NSHumanReadableCopyright': 'Copyright © 2024 Menu Calendar. All rights reserved.',
    },
)
EOF

print_success "Spec file đã được tạo"

# Build với PyInstaller
print_status "Building standalone app với PyInstaller..."
echo "⏳ Quá trình này có thể mất vài phút..."

$PYINSTALLER_PATH --clean menu_calendar.spec

if [ $? -eq 0 ]; then
    print_success "Build thành công!"
else
    print_error "Build thất bại"
    exit 1
fi

# Kiểm tra app đã được tạo
if [ -d "dist/MenuCalendar_Standalone.app" ]; then
    print_success "Standalone app đã được tạo"
    
    # Copy vào thư mục gốc
    cp -r dist/MenuCalendar_Standalone.app .
    print_success "App đã được copy vào thư mục gốc"
    
    # Cấp quyền thực thi
    chmod +x MenuCalendar_Standalone.app/Contents/MacOS/MenuCalendar
    print_success "Quyền thực thi đã được cấp"
    
    # Hiển thị thông tin
    echo ""
    print_success "🎉 Standalone Menu Calendar App đã sẵn sàng!"
    echo ""
    echo "📱 Thông tin app:"
    echo "   • Tên: MenuCalendar_Standalone.app"
    echo "   • Kích thước: $(du -sh MenuCalendar_Standalone.app | cut -f1)"
    echo "   • Vị trí: $(pwd)/MenuCalendar_Standalone.app"
    echo ""
    echo "🚀 Cách sử dụng:"
    echo "   • Copy MenuCalendar_Standalone.app vào /Applications/"
    echo "   • Double-click để chạy"
    echo "   • Hoặc: open MenuCalendar_Standalone.app"
    echo ""
    echo "✨ Đặc điểm standalone:"
    echo "   • Không cần cài đặt Python"
    echo "   • Không cần cài đặt dependencies"
    echo "   • Chạy được trên mọi máy macOS 10.15+"
    echo "   • Chỉ cần copy vào Applications"
    
else
    print_error "Standalone app không được tạo"
    exit 1
fi

# Dọn dẹp file tạm
print_status "Dọn dẹp file tạm..."
rm -f menu_calendar.spec
rm -rf build/ dist/
print_success "Đã dọn dẹp"

echo ""
print_success "✅ Hoàn tất! Standalone app sẵn sàng để chia sẻ."
