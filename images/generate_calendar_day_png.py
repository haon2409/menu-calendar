from PIL import Image, ImageDraw, ImageFont

# Kích thước ảnh
icon_size = 256

# Tạo các file từ 1 đến 31
for day in range(1, 32):
    # Tạo ảnh mới với nền trong suốt
    image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Tính chiều cao phần màu đỏ (1/6 tổng chiều cao)
    red_height = icon_size // 6

    # Tạo nền trắng với góc bo tròn
    radius = 20
    draw.rounded_rectangle(
        [0, 0, icon_size, icon_size],
        radius=radius,
        fill='white'
    )

    # Vẽ phần màu đỏ ở phía trên với góc bo tròn ở trên
    draw.rounded_rectangle(
        [0, 0, icon_size, red_height],
        radius=radius,
        fill='red',
        corners=(True, True, False, False)
    )

    # Tải font
    font_size = 180  # Font size đã chỉnh thành 200
    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        font_size = 50  # Giảm kích thước nếu dùng font mặc định

    # Văn bản là số ngày
    text = str(day)

    # Tính kích thước văn bản
    text_width, text_height = draw.textlength(text, font=font), font_size

    # Tính vị trí để canh giữa văn bản
    x = (icon_size - text_width) // 2  # Canh giữa trái-phải
    white_height = icon_size - red_height  # Chiều cao phần trắng
    offset = 10
    y = red_height + (white_height - text_height) // 2 - offset  # Canh giữa và nhích lên

    # Vẽ số ngày màu đen
    draw.text((x, y), text, fill='black', font=font)

    # Lưu ảnh với tên file tương ứng
    filename = f'calendar_{day}_icon.png'
    image.save(filename, 'PNG')

    print(f"Icon {filename} đã được tạo và lưu")

print("Đã tạo xong tất cả 31 icon!")