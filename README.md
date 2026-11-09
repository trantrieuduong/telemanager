# TeleManager - Trình Quản Lý Đa Tài Khoản Telegram Desktop

**[English Version](/README_EN.md)**

TeleManager là một ứng dụng gọn nhẹ, hiệu năng cao dành cho Windows, được thiết kế để quản lý và khởi chạy đồng thời nhiều tài khoản Telegram Desktop hoàn toàn độc lập, tích hợp quản lý Proxy riêng biệt, theo dõi tiến trình theo thời gian thực và bảo vệ toàn vẹn dữ liệu phiên đăng nhập.

Dự án này được nâng cấp, tái cấu trúc và phát triển mở rộng từ dự án gốc: [telemanager-app/telemanager](https://github.com/telemanager-app/telemanager).

---

## Tính Năng Nổi Bật

- **Quản lý không giới hạn tài khoản**: Tạo và phân loại nhiều hồ sơ tài khoản (Công việc, Cá nhân, Crypto, Tự động hóa) trên cùng một máy tính.
- **Cách ly phiên hoạt động tuyệt đối**: Mỗi profile sở hữu một thư mục `tdata` riêng biệt thông qua tham số `-workdir`. Dữ liệu cache, lịch sử và phiên đăng nhập không bao giờ bị xung đột hay ghi đè lẫn nhau.
- **Giám sát trạng thái thời gian thực**: Tự động phát hiện chính xác tài khoản nào đang hoạt động (`Đang chạy`) hoặc đã tắt (`Đã đóng`).
- **Đóng tài khoản đang chạy an toàn**: Cho phép dừng và đóng tiến trình Telegram của từng profile trực tiếp trên giao diện chỉ với một thao tác.
- **Bảo vệ an toàn dữ liệu**: Hệ thống tự động khóa tính năng xóa hoặc đổi tên thư mục khi tài khoản đang chạy, triệt tiêu nguy cơ lỗi khóa file (`PermissionError`) hoặc làm hỏng session Telegram.
- **Quản lý Proxy chuyên biệt cho từng profile**:
  - Hỗ trợ các giao thức SOCKS5, HTTP và MTProto.
  - Công cụ dán nhanh định dạng chuỗi proxy (`host:port:user:pass` hoặc URL).
  - Tích hợp kiểm tra kết nối và đo độ trễ (latency tính bằng mili-giây) trực tiếp trước khi áp dụng.
  - Tự động sinh liên kết chuẩn `tg://` để nạp cấu hình proxy vào Telegram Desktop.
- **Tìm kiếm và lọc nhanh chóng**: Tìm kiếm tài khoản tức thì theo tên hiển thị, tên thư mục hoặc nội dung ghi chú.
- **Linh hoạt tên hiển thị**: Cho phép đặt tên hiển thị tiếng Việt có dấu và lưu thông tin bổ trợ (số điện thoại, phân loại).
- **Sao lưu và di chuyển an toàn**: Hỗ trợ xuất và nhập profile dưới dạng file nén `.zip`, giúp chuyển tài khoản sang máy tính khác nguyên vẹn phiên đăng nhập mà không cần xác thực lại.
- **Giao diện hiện đại**: Thiết kế theo phong cách Windows 11 với thư viện CustomTkinter, hỗ trợ đầy đủ Dark Mode.

---

## Cấu Trúc Dự Án

```text
telemanager/
├── bin/
│   └── Telegram.exe             # File thực thi Telegram Portable chính thức
├── profiles/
│   └── <profile_name>/          # Thư mục dữ liệu của từng profile
│       ├── tdata/               # Dữ liệu phiên đăng nhập Telegram
│       └── meta.json            # Thông tin cấu hình (tên hiển thị, ghi chú, proxy)
├── src/
│   ├── __init__.py
│   ├── config.py                # Cấu hình hệ thống và đường dẫn chuẩn qua sys.executable
│   ├── models/
│   │   ├── __init__.py
│   │   └── profile.py           # Mô hình dữ liệu Profile và ProxyConfig
│   ├── services/
│   │   ├── __init__.py
│   │   ├── process_service.py   # Quản lý, kiểm tra và đóng tiến trình Telegram
│   │   ├── profile_service.py   # Nghiệp vụ tạo, xóa an toàn, sao lưu, phục hồi
│   │   └── proxy_service.py     # Xử lý proxy, kiểm tra độ trễ, tạo liên kết tg://
│   └── ui/
│       ├── __init__.py
│       ├── app.py               # Cửa sổ chính điều phối ứng dụng
│       ├── components/
│       │   ├── __init__.py
│       │   ├── header.py        # Thanh tiêu đề và ô tìm kiếm thời gian thực
│       │   └── profile_card.py  # Thẻ hiển thị tài khoản, huy hiệu trạng thái, nút thao tác
│       └── dialogs/
│           ├── __init__.py
│           ├── profile_dialog.py # Hộp thoại tạo mới và chỉnh sửa profile
│           └── proxy_dialog.py   # Hộp thoại cấu hình và kiểm tra kết nối proxy
├── appicon.ico                  # Biểu tượng ứng dụng
├── main.py                      # Điểm khởi chạy chính của ứng dụng
├── README.md                    # Tài liệu tiếng Việt
└── README_EN.md                 # English documentation
```

---

## Hướng Dẫn Cài Đặt Và Chạy Mã Nguồn

### Yêu cầu hệ thống
- Hệ điều hành: Windows 10 hoặc Windows 11
- Python: Phiên bản 3.10 trở lên

### 1. Cài đặt các thư viện phụ thuộc
```bash
pip install customtkinter pillow
```

### 2. Chuẩn bị file thực thi Telegram
1. Tải bản **Telegram Desktop Portable** chính thức từ trang chủ: [desktop.telegram.org](https://desktop.telegram.org).
2. Tạo thư mục `bin` trong thư mục gốc dự án (nếu chưa có).
3. Đặt file `Telegram.exe` vào bên trong thư mục `bin/`.

### 3. Khởi chạy ứng dụng
```bash
python main.py
```

---

## Hướng Dẫn Đóng Gói Thành File Thực Thi (.exe)

Bạn có thể đóng gói toàn bộ mã nguồn thành một file thực thi độc lập duy nhất bằng `pyinstaller`:

1. Cài đặt PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Chạy lệnh biên dịch:
   ```bash
   pyinstaller --noconsole --onefile --icon=appicon.ico --name="TeleManager" main.py
   ```

3. Sau khi quá trình biên dịch hoàn tất, file thực thi `TeleManager.exe` sẽ nằm trong thư mục `dist/`. Hãy đặt file này nằm cùng cấp với thư mục `bin/` (chứa `Telegram.exe`) và `appicon.ico` để sử dụng.

---

## Nguyên Tắc Đảm Bảo Độ Trust Của Tài Khoản (Anti-Ban)

1. **Tuyệt đối không mở cùng 1 profile trên 2 máy cùng lúc**: Nếu 2 máy cùng truy cập một phiên làm việc với 2 địa chỉ IP khác nhau, hệ thống kiểm duyệt của Telegram sẽ nhận diện hành vi bất thường và hủy phiên đăng nhập ngay lập tức.
2. **Luôn tắt hoàn toàn Telegram trước khi sao lưu hoặc di chuyển**: Việc copy thư mục `tdata` khi Telegram đang chạy có thể khiến các file SQLite bị lỗi dở dang, dẫn đến hỏng phiên đăng nhập.
3. **Ưu tiên sử dụng Proxy dân cư tĩnh (Static Residential SOCKS5) hoặc Mobile Proxy 4G/5G**: Tránh sử dụng proxy Datacenter (IP từ các nhà cung cấp máy chủ đám mây như AWS, DigitalOcean, Linode...) vì Telegram thường xuyên quét và đưa các dải IP này vào danh sách rủi ro cao.
4. **Cố định môi trường mạng cho từng tài khoản**: Một tài khoản nên gắn liền với một proxy cố định hoặc cùng một dải mạng quốc gia, tránh đổi quốc gia liên tục trong thời gian ngắn.

---

## Tuyên Bố Miễn Trừ Trách Nhiệm (Disclaimer)

- TeleManager là phần mềm mã nguồn mở được phát triển nhằm mục đích hỗ trợ người dùng quản lý thuận tiện các phiên làm việc hợp pháp của chính họ trên môi trường máy tính cá nhân.
- Ứng dụng không can thiệp vào mã nguồn nội bộ của Telegram, không chỉnh sửa file thực thi của Telegram, và không có hành vi giải mã hay can thiệp trái phép vào giao thức bảo mật của Telegram.
- Người dùng tự chịu hoàn toàn trách nhiệm đối với việc tuân thủ [Điều khoản Dịch vụ của Telegram (Telegram Terms of Service)](https://telegram.org/tos). Tác giả và những người đóng góp cho dự án không chịu bất kỳ trách nhiệm pháp lý nào đối với các trường hợp tài khoản bị hạn chế, cảnh cáo, hoặc khóa do vi phạm chính sách của bên thứ ba, sử dụng proxy kém chất lượng hoặc hành vi lạm dụng nền tảng.

---

## Giấy Phép Sử Dụng (License)

Dự án này được phát hành theo giấy phép [MIT License](LICENSE).

Dự án nguyên bản ban đầu được phát triển bởi tác giả **Eyuel Engida** tại [https://github.com/telemanager-app/telemanager](https://github.com/telemanager-app/telemanager). Toàn bộ các cải tiến về kiến trúc mô-đun, quản lý proxy, theo dõi tiến trình và bảo vệ an toàn phiên làm việc được thực hiện trên phiên bản nâng cấp này.
