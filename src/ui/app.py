import os
import customtkinter as ctk
from tkinter import messagebox
from typing import List, Dict

from .. import config
from ..models.profile import Profile, ProxyConfig
from ..services.process_service import ProcessService
from ..services.profile_service import ProfileService
from ..services.proxy_service import ProxyService
from .components.header import AppHeader
from .components.profile_card import ProfileCard
from .dialogs.profile_dialog import ProfileDialog
from .dialogs.proxy_dialog import ProxyDialog


class TelegramManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Cấu hình giao diện tổng thể
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

        # Cửa sổ ứng dụng
        self.title(config.APP_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(520, 500)

        # Đặt biểu tượng ứng dụng nếu tồn tại
        if os.path.exists(config.APP_ICON):
            try:
                self.iconbitmap(config.APP_ICON)
            except Exception:
                pass

        # Khởi tạo các services
        self.process_service = ProcessService()
        self.profile_service = ProfileService()
        self.proxy_service = ProxyService()

        # Trạng thái ứng dụng
        self.all_profiles: List[Profile] = []
        self.cards_map: Dict[str, ProfileCard] = {}
        self.search_query: str = ""

        # Xây dựng giao diện
        self._create_widgets()

        # Quét và nạp danh sách ban đầu
        self.refresh_profiles()

        # Kích hoạt vòng lặp theo dõi trạng thái tiến trình định kỳ
        self._schedule_status_check()

    def _create_widgets(self):
        # 1. Header (Tiêu đề + Thanh tìm kiếm + Nút làm mới)
        self.header = AppHeader(
            self,
            on_search_change=self._handle_search_change,
            on_refresh=self.refresh_profiles,
        )
        self.header.pack(fill="x", padx=0, pady=0)

        # 2. Danh sách cuộn chứa các ProfileCard
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách tài khoản")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(10, 10))

        # 3. Footer (Nút Tạo Profile Mới và Mở thư mục Profiles)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_open_profiles_dir = ctk.CTkButton(
            footer_frame,
            text="Thư mục Profiles",
            width=140,
            height=38,
            fg_color="#333333",
            hover_color="#444444",
            font=("Segoe UI", 12),
            command=self._handle_open_profiles_dir,
        )
        self.btn_open_profiles_dir.pack(side="left")

        self.btn_add = ctk.CTkButton(
            footer_frame,
            text="+ Tạo Profile Mới",
            height=38,
            fg_color="#1f6aa5",
            hover_color="#144870",
            font=("Segoe UI", 13, "bold"),
            command=self._handle_create_new,
        )
        self.btn_add.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _check_exe(self) -> bool:
        if not os.path.exists(config.TELEGRAM_EXE):
            messagebox.showerror(
                "Lỗi thiếu file",
                f"Không tìm thấy file Telegram.exe!\n\nVui lòng sao chép file 'Telegram.exe' vào thư mục:\n{config.BIN_DIR}",
                parent=self,
            )
            return False
        return True

    def refresh_profiles(self):
        """Đọc lại toàn bộ danh sách profile từ ổ cứng và vẽ lại giao diện."""
        self.all_profiles = self.profile_service.list_profiles(config.PROFILES_DIR)

        # Quét tiến trình đang chạy ngầm
        self.process_service.scan_running_profiles_async(config.PROFILES_DIR)

        self._render_profile_list()

    def _render_profile_list(self):
        # Xóa các widget cũ
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.cards_map.clear()

        # Lọc theo từ khóa tìm kiếm
        query = self.search_query.lower().strip()
        filtered: List[Profile] = []
        for p in self.all_profiles:
            display_match = query in p.display_name.lower()
            folder_match = query in p.folder_name.lower()
            notes_match = query in p.notes.lower()
            if not query or display_match or folder_match or notes_match:
                filtered.append(p)

        # Cập nhật số lượng tài khoản trên Header
        self.header.update_account_count(len(filtered), len(self.all_profiles))

        if not filtered:
            msg = "Không tìm thấy tài khoản phù hợp." if query else "Chưa có tài khoản nào. Hãy tạo profile mới!"
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame,
                text=msg,
                font=("Segoe UI", 13),
                text_color="#888888",
            )
            lbl_empty.pack(pady=40)
            return

        for p in filtered:
            is_running = self.process_service.is_running(p.folder_name)
            card = ProfileCard(
                self.scroll_frame,
                profile=p,
                is_running=is_running,
                on_launch=self._handle_launch,
                on_terminate=self._handle_terminate,
                on_edit=self._handle_edit,
                on_proxy=self._handle_proxy,
                on_delete=self._handle_delete,
                on_open_folder=self._handle_open_folder,
            )
            card.pack(fill="x", pady=4)
            self.cards_map[p.folder_name.lower()] = card

    def _handle_search_change(self, query: str):
        self.search_query = query
        self._render_profile_list()

    def _schedule_status_check(self):
        """Kiểm tra trạng thái tiến trình định kỳ mỗi 3 giây."""
        self.process_service.scan_running_profiles_async(config.PROFILES_DIR)

        for folder_key, card in list(self.cards_map.items()):
            is_running = self.process_service.is_running(card.profile.folder_name)
            if card.is_running != is_running:
                card.set_running_status(is_running)

        self.after(3000, self._schedule_status_check)

    def _handle_launch(self, profile: Profile):
        if not self._check_exe():
            return

        profile_path = os.path.join(config.PROFILES_DIR, profile.folder_name)

        # 1. Chốt chặn kiểm tra Proxy nghiêm ngặt (Strict Launch Gate)
        if profile.proxy.enabled:
            # Kiểm tra bắt buộc sống còn của proxy trước khi cho phép mở
            success, err_msg, latency = self.proxy_service.test_proxy_strict(profile.proxy, timeout=4.0)
            if not success:
                messagebox.showerror(
                    "CHẶN KHỞI CHẠY - PROXY KHÔNG HOẠT ĐỘNG",
                    f"Tài khoản: {profile.display_name}\n\n"
                    f"Proxy [{profile.proxy.proxy_type}] {profile.proxy.host}:{profile.proxy.port} "
                    f"KHÔNG HOẠT ĐỘNG HOẶC XÁC THỰC THẤT BẠI!\n\n"
                    f"Chi tiết lỗi: {err_msg}\n\n"
                    "CẢNH BÁO AN TOÀN:\n"
                    "Để bảo vệ tài khoản khỏi bị cấm và TUYỆT ĐỐI NGĂN CHẶN việc rò rỉ địa chỉ IP thật của máy tính, "
                    "hệ thống đã từ chối khởi chạy Telegram.\n\n"
                    "Vui lòng cấu hình lại Proxy còn hoạt động trước khi mở tài khoản này.",
                    parent=self,
                )
                return
        else:
            # Cảnh báo người dùng nếu tài khoản chưa cấu hình proxy
            confirm = messagebox.askyesno(
                "Cảnh báo không dùng Proxy",
                f"Tài khoản '{profile.display_name}' HIỆN CHƯA BẬT PROXY.\n\n"
                "Nếu tiếp tục, tài khoản sẽ kết nối trực tiếp bằng địa chỉ IP thật của máy tính này.\n\n"
                "Bạn có chắc chắn muốn mở tài khoản bằng IP thật không?",
                parent=self,
            )
            if not confirm:
                return

        # 2. Khởi chạy Telegram qua ProcessService kèm cấu hình Proxy được quản lý
        success = self.process_service.launch(
            exe_path=config.TELEGRAM_EXE,
            profile_path=profile_path,
            folder_name=profile.folder_name,
            proxy=profile.proxy,
        )

        if success:
            key = profile.folder_name.lower()
            if key in self.cards_map:
                self.cards_map[key].set_running_status(True)
        else:
            messagebox.showerror(
                "Lỗi khởi chạy",
                f"Không thể khởi chạy Telegram cho profile: {profile.display_name}",
                parent=self,
            )

    def _handle_terminate(self, profile: Profile):
        """Đóng tiến trình Telegram đang chạy của profile."""
        if not self.process_service.is_running(profile.folder_name):
            return

        confirm = messagebox.askyesno(
            "Xác nhận đóng",
            f"Bạn có chắc muốn đóng tiến trình Telegram của tài khoản '{profile.display_name}'?",
            parent=self,
        )
        if not confirm:
            return

        profile_path = os.path.join(config.PROFILES_DIR, profile.folder_name)
        self.process_service.terminate_profile(profile_path, profile.folder_name)

        # Cập nhật ngay trạng thái trên giao diện
        key = profile.folder_name.lower()
        if key in self.cards_map:
            self.cards_map[key].set_running_status(False)

    def _handle_create_new(self):
        def _on_save(folder_name: str, display_name: str, notes: str):
            success, msg, new_profile = self.profile_service.create_profile(
                profiles_dir=config.PROFILES_DIR,
                folder_name=folder_name,
                display_name=display_name,
                notes=notes,
            )
            if not success:
                messagebox.showerror("Lỗi tạo profile", msg, parent=self)
                return

            self.refresh_profiles()

            # Hỏi người dùng có muốn khởi chạy ngay không
            if messagebox.askyesno(
                "Khởi chạy",
                f"Đã tạo profile '{new_profile.display_name}'. Bạn có muốn khởi chạy Telegram ngay bây giờ không?",
                parent=self,
            ):
                self._handle_launch(new_profile)

        ProfileDialog(self, on_save=_on_save)

    def _handle_edit(self, profile: Profile):
        is_running = self.process_service.is_running(profile.folder_name)

        def _on_save(new_folder: str, new_display: str, new_notes: str):
            success, msg, final_folder = self.profile_service.update_profile(
                profiles_dir=config.PROFILES_DIR,
                current_folder=profile.folder_name,
                new_folder_name=new_folder,
                display_name=new_display,
                notes=new_notes,
                proxy=profile.proxy,
                is_running=is_running,
            )
            if not success:
                messagebox.showerror("Lỗi cập nhật", msg, parent=self)
                return

            self.refresh_profiles()

        ProfileDialog(self, profile=profile, on_save=_on_save, is_running=is_running)

    def _handle_proxy(self, profile: Profile):
        def _on_save(new_proxy: ProxyConfig):
            profile.proxy = new_proxy
            self.profile_service.save_profile_meta(config.PROFILES_DIR, profile)
            self.refresh_profiles()

        ProxyDialog(
            self,
            profile_name=profile.display_name,
            current_proxy=profile.proxy,
            on_save=_on_save,
        )

    def _handle_delete(self, profile: Profile):
        is_running = self.process_service.is_running(profile.folder_name)
        if is_running:
            messagebox.showwarning(
                "Không thể xóa",
                f"Tài khoản '{profile.display_name}' đang chạy.\nVui lòng đóng Telegram của tài khoản này trước khi xóa.",
                parent=self,
            )
            return

        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa tài khoản '{profile.display_name}' ({profile.folder_name})?\n\nCảnh báo: Toàn bộ dữ liệu đăng nhập (tdata) sẽ bị xóa vĩnh viễn!",
            parent=self,
        )
        if not confirm:
            return

        success, msg = self.profile_service.delete_profile(
            profiles_dir=config.PROFILES_DIR,
            folder_name=profile.folder_name,
            is_running=is_running,
        )
        if success:
            self.refresh_profiles()
        else:
            messagebox.showerror("Lỗi xóa", msg, parent=self)

    def _handle_open_folder(self, profile: Profile):
        folder_path = os.path.join(config.PROFILES_DIR, profile.folder_name)
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở thư mục: {str(e)}", parent=self)
        else:
            messagebox.showerror("Lỗi", "Thư mục profile không tồn tại.", parent=self)

    def _handle_open_profiles_dir(self):
        if os.path.exists(config.PROFILES_DIR):
            try:
                os.startfile(config.PROFILES_DIR)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở thư mục: {str(e)}", parent=self)
