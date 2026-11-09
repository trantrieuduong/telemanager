import threading
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from ...models.profile import ProxyConfig
from ...services.proxy_service import ProxyService


class ProxyDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        profile_name: str,
        current_proxy: Optional[ProxyConfig] = None,
        on_save: Optional[Callable[[ProxyConfig], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.profile_name = profile_name
        self.current_proxy = current_proxy or ProxyConfig()
        self.on_save = on_save

        self.title(f"Cấu hình Proxy - {profile_name}")
        self.geometry("460x540")
        self.resizable(False, False)

        # Thiết lập cửa sổ dạng modal
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        self._populate_data()

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Tiêu đề
        lbl_head = ctk.CTkLabel(
            container,
            text=f"Cấu hình Proxy: {self.profile_name}",
            font=("Segoe UI", 15, "bold"),
        )
        lbl_head.pack(anchor="w", pady=(0, 10))

        # Checkbox Kích hoạt Proxy
        self.var_enabled = ctk.BooleanVar(value=self.current_proxy.enabled)
        self.chk_enabled = ctk.CTkCheckBox(
            container,
            text="Sử dụng Proxy cho tài khoản này",
            variable=self.var_enabled,
            font=("Segoe UI", 12, "bold"),
            command=self._toggle_proxy_inputs,
        )
        self.chk_enabled.pack(anchor="w", pady=(0, 12))

        # Khung Dán nhanh (Quick Paste)
        box_quick = ctk.CTkFrame(container, fg_color="#2b2b2b", corner_radius=6)
        box_quick.pack(fill="x", pady=(0, 12), padx=0)

        lbl_quick = ctk.CTkLabel(
            box_quick,
            text="Dán nhanh (hỗ trợ: host:port:user:pass hoặc socks5://...):",
            font=("Segoe UI", 11),
            text_color="#aaaaaa",
        )
        lbl_quick.pack(anchor="w", padx=10, pady=(8, 2))

        row_quick = ctk.CTkFrame(box_quick, fg_color="transparent")
        row_quick.pack(fill="x", padx=10, pady=(0, 8))

        self.entry_quick = ctk.CTkEntry(
            row_quick,
            placeholder_text="192.168.1.1:1080:user:pass",
            font=("Segoe UI", 11),
        )
        self.entry_quick.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_parse = ctk.CTkButton(
            row_quick,
            text="Điền nhanh",
            width=80,
            fg_color="#3a5a78",
            hover_color="#253e56",
            command=self._handle_quick_parse,
        )
        self.btn_parse.pack(side="left")

        # Khung Form chi tiết
        self.form_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True)

        # Loại Proxy
        lbl_type = ctk.CTkLabel(self.form_frame, text="Loại Proxy:", font=("Segoe UI", 12))
        lbl_type.pack(anchor="w")

        self.opt_type = ctk.CTkOptionMenu(
            self.form_frame,
            values=["SOCKS5", "HTTP", "MTProto"],
            command=self._handle_type_change,
        )
        self.opt_type.pack(fill="x", pady=(2, 8))

        # Host & Port
        row_host_port = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row_host_port.pack(fill="x", pady=(0, 8))

        # Host
        col_host = ctk.CTkFrame(row_host_port, fg_color="transparent")
        col_host.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(col_host, text="Host / IP:", font=("Segoe UI", 12)).pack(anchor="w")
        self.entry_host = ctk.CTkEntry(col_host, placeholder_text="127.0.0.1")
        self.entry_host.pack(fill="x", pady=(2, 0))

        # Port
        col_port = ctk.CTkFrame(row_host_port, fg_color="transparent")
        col_port.pack(side="left", padx=(6, 0))
        ctk.CTkLabel(col_port, text="Port:", font=("Segoe UI", 12)).pack(anchor="w")
        self.entry_port = ctk.CTkEntry(col_port, width=80, placeholder_text="1080")
        self.entry_port.pack(fill="x", pady=(2, 0))

        # Username
        self.lbl_user = ctk.CTkLabel(self.form_frame, text="Username (nếu có):", font=("Segoe UI", 12))
        self.lbl_user.pack(anchor="w")
        self.entry_user = ctk.CTkEntry(self.form_frame)
        self.entry_user.pack(fill="x", pady=(2, 8))

        # Password / Secret
        self.lbl_pass = ctk.CTkLabel(self.form_frame, text="Password / Secret:", font=("Segoe UI", 12))
        self.lbl_pass.pack(anchor="w")
        self.entry_pass = ctk.CTkEntry(self.form_frame, show="*")
        self.entry_pass.pack(fill="x", pady=(2, 10))

        # Khung Kiểm tra kết nối
        box_test = ctk.CTkFrame(self.form_frame, fg_color="#1e1e1e", corner_radius=6)
        box_test.pack(fill="x", pady=(0, 15))

        row_test = ctk.CTkFrame(box_test, fg_color="transparent")
        row_test.pack(fill="x", padx=10, pady=8)

        self.btn_test = ctk.CTkButton(
            row_test,
            text="Kiểm tra Proxy",
            width=110,
            fg_color="#2b5278",
            hover_color="#1d3b56",
            command=self._handle_test_connection,
        )
        self.btn_test.pack(side="left", padx=(0, 10))

        self.lbl_test_result = ctk.CTkLabel(
            row_test,
            text="Chưa kiểm tra",
            font=("Segoe UI", 11),
            text_color="#888888",
            anchor="w",
        )
        self.lbl_test_result.pack(side="left", fill="x", expand=True)

        # Các nút hành động dưới cùng
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
            text="Lưu cấu hình",
            width=120,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self._handle_save,
        )
        self.btn_save.pack(side="right")

        self._toggle_proxy_inputs()

    def _populate_data(self):
        p = self.current_proxy
        self.var_enabled.set(p.enabled)
        self.opt_type.set(p.proxy_type or "SOCKS5")
        self.entry_host.insert(0, p.host or "")
        self.entry_port.insert(0, str(p.port) if p.port else "1080")
        self.entry_user.insert(0, p.username or "")
        self.entry_pass.insert(0, p.secret if p.proxy_type == "MTProto" else p.password or "")
        self._toggle_proxy_inputs()

    def _toggle_proxy_inputs(self):
        enabled = self.var_enabled.get()
        state = "normal" if enabled else "disabled"
        self.opt_type.configure(state=state)
        self.entry_host.configure(state=state)
        self.entry_port.configure(state=state)
        self.entry_user.configure(state=state)
        self.entry_pass.configure(state=state)
        self.btn_test.configure(state=state)

    def _handle_type_change(self, choice: str):
        if choice == "MTProto":
            self.lbl_user.configure(text="Username (không dùng cho MTProto):")
            self.entry_user.configure(state="disabled")
            self.lbl_pass.configure(text="Secret key:")
        else:
            self.lbl_user.configure(text="Username (nếu có):")
            if self.var_enabled.get():
                self.entry_user.configure(state="normal")
            self.lbl_pass.configure(text="Password:")

    def _handle_quick_parse(self):
        text = self.entry_quick.get().strip()
        parsed = ProxyService.parse_proxy_string(text)
        if not parsed:
            messagebox.showwarning(
                "Định dạng không hỗ trợ",
                "Không thể nhận diện proxy.\nCác định dạng hợp lệ:\n- host:port\n- host:port:user:pass\n- socks5://user:pass@host:port",
                parent=self,
            )
            return

        self.var_enabled.set(True)
        self._toggle_proxy_inputs()
        self.opt_type.set(parsed.proxy_type)
        self.entry_host.delete(0, "end")
        self.entry_host.insert(0, parsed.host)
        self.entry_port.delete(0, "end")
        self.entry_port.insert(0, str(parsed.port))
        self.entry_user.delete(0, "end")
        self.entry_user.insert(0, parsed.username)
        self.entry_pass.delete(0, "end")
        self.entry_pass.insert(0, parsed.password)

    def _handle_test_connection(self):
        host = self.entry_host.get().strip()
        port_str = self.entry_port.get().strip()
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Lỗi", "Port phải là số nguyên hợp lệ (1 - 65535).", parent=self)
            return

        self.lbl_test_result.configure(text="Đang kiểm tra...", text_color="#e0e0e0")
        self.btn_test.configure(state="disabled")

        def _run_test():
            success, msg, latency = ProxyService.test_connection(host, port)
            self.after(0, lambda: self._update_test_ui(success, msg, latency))

        threading.Thread(target=_run_test, daemon=True).start()

    def _update_test_ui(self, success: bool, msg: str, latency: float):
        self.btn_test.configure(state="normal")
        if success:
            self.lbl_test_result.configure(
                text=f"Hoạt động ({latency} ms)",
                text_color="#66bb6a",
            )
        else:
            self.lbl_test_result.configure(
                text=f"Thất bại: {msg}",
                text_color="#ef5350",
            )

    def _handle_save(self):
        enabled = self.var_enabled.get()
        ptype = self.opt_type.get()
        host = self.entry_host.get().strip()
        port_str = self.entry_port.get().strip()

        port = 1080
        if enabled:
            if not host:
                messagebox.showerror("Lỗi", "Host/IP không được để trống khi bật proxy.", parent=self)
                return
            try:
                port = int(port_str)
                if port <= 0 or port > 65535:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Lỗi", "Port phải là số từ 1 đến 65535.", parent=self)
                return

        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()

        proxy_config = ProxyConfig(
            enabled=enabled,
            proxy_type=ptype,
            host=host,
            port=port,
            username=user if ptype != "MTProto" else "",
            password=pwd if ptype != "MTProto" else "",
            secret=pwd if ptype == "MTProto" else "",
        )

        if self.on_save:
            self.on_save(proxy_config)

        self.destroy()
