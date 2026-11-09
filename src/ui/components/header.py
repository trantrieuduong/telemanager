import customtkinter as ctk
from typing import Callable


class AppHeader(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_search_change: Callable[[str], None],
        on_refresh: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, corner_radius=0, fg_color="#181818", **kwargs)
        self.on_search_change = on_search_change
        self.on_refresh = on_refresh

        self._create_widgets()

    def _create_widgets(self):
        # Dòng tiêu đề ứng dụng
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_title = ctk.CTkLabel(
            title_frame,
            text="TeleManager",
            font=("Segoe UI", 18, "bold"),
            text_color="#ffffff",
        )
        self.lbl_title.pack(side="left")

        self.lbl_count = ctk.CTkLabel(
            title_frame,
            text="0 tài khoản",
            font=("Segoe UI", 12),
            text_color="#888888",
        )
        self.lbl_count.pack(side="right")

        # Dòng thanh tìm kiếm và nút làm mới
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.entry_search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Tìm kiếm theo tên, thư mục, ghi chú...",
            height=32,
            font=("Segoe UI", 12),
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_search.bind("<KeyRelease>", self._handle_search)

        self.btn_clear = ctk.CTkButton(
            search_frame,
            text="X",
            width=32,
            height=32,
            fg_color="#333333",
            hover_color="#444444",
            command=self._clear_search,
        )
        self.btn_clear.pack(side="left", padx=(0, 6))

        self.btn_refresh = ctk.CTkButton(
            search_frame,
            text="Làm mới",
            width=75,
            height=32,
            fg_color="#2b5278",
            hover_color="#1d3b56",
            font=("Segoe UI", 12),
            command=self.on_refresh,
        )
        self.btn_refresh.pack(side="left")

    def _handle_search(self, event=None):
        query = self.entry_search.get()
        self.on_search_change(query)

    def _clear_search(self):
        self.entry_search.delete(0, "end")
        self.on_search_change("")

    def update_account_count(self, count: int, total: int):
        if count == total:
            self.lbl_count.configure(text=f"{total} tài khoản")
        else:
            self.lbl_count.configure(text=f"Lọc {count}/{total} tài khoản")
