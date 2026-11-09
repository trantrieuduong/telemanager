import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable
from ...models.profile import Profile


class ProfileDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        profile: Optional[Profile] = None,
        on_save: Optional[Callable[[str, str, str], None]] = None,
        is_running: bool = False,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.profile = profile
        self.on_save = on_save
        self.is_running = is_running
        self.is_edit_mode = profile is not None

        title = "Sửa Profile" if self.is_edit_mode else "Tạo Profile Mới"
        self.title(title)
        self.geometry("420x420")
        self.resizable(False, False)

        # Thiết lập cửa sổ dạng modal
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        self._populate_data()

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Tiêu đề hộp thoại
        header_text = "Chỉnh sửa Profile" if self.is_edit_mode else "Thêm Profile Mới"
        lbl_head = ctk.CTkLabel(container, text=header_text, font=("Segoe UI", 16, "bold"))
        lbl_head.pack(anchor="w", pady=(0, 15))

        # Trường: Tên thư mục (Folder Name)
        lbl_folder = ctk.CTkLabel(
            container,
            text="Tên thư mục (không dấu, không ký tự đặc biệt):",
            font=("Segoe UI", 12),
        )
        lbl_folder.pack(anchor="w")

        self.entry_folder = ctk.CTkEntry(container, placeholder_text="Ví dụ: acc_01 hoặc work_crypto")
        self.entry_folder.pack(fill="x", pady=(4, 10))

        if self.is_edit_mode and self.is_running:
            lbl_warn = ctk.CTkLabel(
                container,
                text="Tài khoản đang chạy. Không thể đổi tên thư mục lúc này.",
                font=("Segoe UI", 11),
                text_color="#e57373",
            )
            lbl_warn.pack(anchor="w", pady=(0, 6))
            self.entry_folder.configure(state="disabled")

        # Trường: Tên hiển thị (Display Name)
        lbl_display = ctk.CTkLabel(
            container,
            text="Tên hiển thị (có thể gõ tiếng Việt có dấu):",
            font=("Segoe UI", 12),
        )
        lbl_display.pack(anchor="w")

        self.entry_display = ctk.CTkEntry(container, placeholder_text="Ví dụ: Tài khoản Công việc 01")
        self.entry_display.pack(fill="x", pady=(4, 10))

        # Trường: Ghi chú (Notes)
        lbl_notes = ctk.CTkLabel(container, text="Ghi chú / Số điện thoại:", font=("Segoe UI", 12))
        lbl_notes.pack(anchor="w")

        self.entry_notes = ctk.CTkEntry(
            container,
            placeholder_text="Ví dụ: SĐT: +84912345678, tạo ngày 01/2026",
        )
        self.entry_notes.pack(fill="x", pady=(4, 20))

        # Các nút hành động
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom")

        self.btn_cancel = ctk.CTkButton(
            btn_box,
            text="Hủy",
            width=90,
            fg_color="#333333",
            hover_color="#444444",
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Lưu thông tin",
            width=120,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._handle_save,
        )
        self.btn_save.pack(side="right")

    def _populate_data(self):
        if self.profile:
            self.entry_folder.insert(0, self.profile.folder_name)
            self.entry_display.insert(0, self.profile.display_name or self.profile.folder_name)
            self.entry_notes.insert(0, self.profile.notes or "")

    def _handle_save(self):
        folder_name = self.entry_folder.get().strip()
        display_name = self.entry_display.get().strip()
        notes = self.entry_notes.get().strip()

        if not folder_name:
            messagebox.showerror("Lỗi", "Tên thư mục không được để trống.", parent=self)
            return

        if self.on_save:
            self.on_save(folder_name, display_name, notes)

        self.destroy()
