import os
import sys

# Xác định thư mục gốc của dự án dựa vào sys.executable hoặc __file__
if getattr(sys, "frozen", False):
    # Khi chạy bằng bản đã đóng gói (.exe)
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Khi chạy trong môi trường script Python thông thường
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BIN_DIR = os.path.join(BASE_DIR, "bin")
TELEGRAM_EXE = os.path.join(BIN_DIR, "Telegram.exe")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
APP_ICON = os.path.join(BASE_DIR, "appicon.ico")

# Tạo các thư mục cần thiết nếu chưa tồn tại
os.makedirs(BIN_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

# Cấu hình giao diện CustomTkinter
APPEARANCE_MODE = "Dark"
COLOR_THEME = "blue"
APP_TITLE = "Telegram Manager"
WINDOW_WIDTH = 680
WINDOW_HEIGHT = 580
