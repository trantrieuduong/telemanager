import sys
import os

# Đảm bảo thư mục gốc được thêm vào sys.path để hỗ trợ cả chạy script lẫn đóng gói exe
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.ui.app import TelegramManagerApp

if __name__ == "__main__":
    app = TelegramManagerApp()
    app.mainloop()
