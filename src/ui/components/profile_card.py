import customtkinter as ctk
from typing import Callable
from ...models.profile import Profile


class ProfileCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        profile: Profile,
        is_running: bool,
        on_launch: Callable[[Profile], None],
        on_terminate: Callable[[Profile], None],
        on_edit: Callable[[Profile], None],
        on_proxy: Callable[[Profile], None],
        on_delete: Callable[[Profile], None],
        on_open_folder: Callable[[Profile], None],
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, fg_color="#242424", **kwargs)
        self.profile = profile
        self.is_running = is_running
        self.on_launch = on_launch
        self.on_terminate = on_terminate
        self.on_edit = on_edit
        self.on_proxy = on_proxy
        self.on_delete = on_delete
        self.on_open_folder = on_open_folder

        self._create_widgets()

    def _create_widgets(self):
        # Cột trái: Thông tin Profile
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Dòng 1: Tên hiển thị và Huy hiệu trạng thái
        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        title_text = self.profile.display_name or self.profile.folder_name
        self.lbl_name = ctk.CTkLabel(
            top_row,
            text=title_text,
            font=("Segoe UI", 14, "bold"),
            text_color="#ffffff",
            anchor="w",
        )
        self.lbl_name.pack(side="left", padx=(0, 8))

        # Huy hiệu trạng thái (Đang chạy / Đã đóng)
        status_text = "Đang chạy" if self.is_running else "Đã đóng"
        status_fg = "#143a18" if self.is_running else "#333333"
        status_text_color = "#66bb6a" if self.is_running else "#999999"

        self.lbl_status = ctk.CTkLabel(
            top_row,
            text=f"  {status_text}  ",
            font=("Segoe UI", 10, "bold"),
            fg_color=status_fg,
            text_color=status_text_color,
            corner_radius=4,
        )
        self.lbl_status.pack(side="left")

        # Dòng 2: Tên thư mục (nếu khác tên hiển thị) và Ghi chú
        details = []
        if self.profile.display_name != self.profile.folder_name:
            details.append(f"Thư mục: {self.profile.folder_name}")
        if self.profile.notes:
            details.append(self.profile.notes)

        if details:
            lbl_sub = ctk.CTkLabel(
                info_frame,
                text=" • ".join(details),
                font=("Segoe UI", 11),
                text_color="#aaaaaa",
                anchor="w",
            )
            lbl_sub.pack(fill="x", anchor="w", pady=(2, 0))

        # Dòng 3: Thông tin Proxy
        proxy = self.profile.proxy
        if proxy.enabled and proxy.host:
            proxy_info = f"Proxy: [{proxy.proxy_type}] {proxy.host}:{proxy.port}"
            proxy_color = "#64b5f6"
        else:
            proxy_info = "Không dùng Proxy (Dùng IP thật của máy)"
            proxy_color = "#ffb74d"

        lbl_proxy = ctk.CTkLabel(
            info_frame,
            text=proxy_info,
            font=("Segoe UI", 11),
            text_color=proxy_color,
            anchor="w",
        )
        lbl_proxy.pack(fill="x", anchor="w", pady=(2, 0))

        # Cột phải: Các nút thao tác
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=10)

        # Nút Mở Telegram
        self.btn_open = ctk.CTkButton(
            btn_frame,
            text="Mở",
            width=50,
            height=30,
            fg_color="#1f6aa5",
            hover_color="#144870",
            font=("Segoe UI", 12, "bold"),
            command=lambda: self.on_launch(self.profile),
        )
        self.btn_open.pack(side="left", padx=2)

        # Nút Đóng Telegram (chỉ kích hoạt khi đang chạy)
        self.btn_close = ctk.CTkButton(
            btn_frame,
            text="Đóng",
            width=50,
            height=30,
            fg_color="#a83232" if self.is_running else "#3a3a3a",
            hover_color="#8b1e1e" if self.is_running else "#3a3a3a",
            state="normal" if self.is_running else "disabled",
            font=("Segoe UI", 11, "bold"),
            command=lambda: self.on_terminate(self.profile),
        )
        self.btn_close.pack(side="left", padx=2)

        # Nút Sửa thông tin
        self.btn_edit = ctk.CTkButton(
            btn_frame,
            text="Sửa",
            width=44,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#505050",
            font=("Segoe UI", 11),
            command=lambda: self.on_edit(self.profile),
        )
        self.btn_edit.pack(side="left", padx=2)

        # Nút Proxy
        self.btn_proxy = ctk.CTkButton(
            btn_frame,
            text="Proxy",
            width=48,
            height=30,
            fg_color="#2b4c5e",
            hover_color="#1d3542",
            font=("Segoe UI", 11),
            command=lambda: self.on_proxy(self.profile),
        )
        self.btn_proxy.pack(side="left", padx=2)

        # Nút Mở thư mục trên máy
        self.btn_folder = ctk.CTkButton(
            btn_frame,
            text="Thư mục",
            width=62,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#505050",
            font=("Segoe UI", 11),
            command=lambda: self.on_open_folder(self.profile),
        )
        self.btn_folder.pack(side="left", padx=2)

        # Nút Xóa (Màu đỏ)
        self.btn_del = ctk.CTkButton(
            btn_frame,
            text="X",
            width=30,
            height=30,
            fg_color="#8b2626",
            hover_color="#5e1919",
            font=("Segoe UI", 11, "bold"),
            command=lambda: self.on_delete(self.profile),
        )
        self.btn_del.pack(side="left", padx=2)

    def set_running_status(self, is_running: bool):
        """Cập nhật lại trạng thái trực quan mà không cần vẽ lại toàn bộ widget."""
        self.is_running = is_running
        status_text = "Đang chạy" if is_running else "Đã đóng"
        status_fg = "#143a18" if is_running else "#333333"
        status_text_color = "#66bb6a" if is_running else "#999999"

        self.lbl_status.configure(
            text=f"  {status_text}  ",
            fg_color=status_fg,
            text_color=status_text_color,
        )

        if is_running:
            self.btn_close.configure(
                state="normal",
                fg_color="#a83232",
                hover_color="#8b1e1e",
            )
        else:
            self.btn_close.configure(
                state="disabled",
                fg_color="#3a3a3a",
                hover_color="#3a3a3a",
            )
