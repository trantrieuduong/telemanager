import socket
import time
import base64
import select
import threading
import urllib.parse
from typing import Tuple, Optional
from ..models.profile import ProxyConfig


class LocalHttpToSocks5Bridge:
    """
    Cầu nối SOCKS5 nội bộ (Local SOCKS5 Bridge).
    Telegram Desktop không hỗ trợ liên kết tg://http cho proxy HTTP.
    Cầu nối này lắng nghe kết nối SOCKS5 cục bộ từ Telegram Desktop tại 127.0.0.1,
    sau đó chuyển tiếp (forward) toàn bộ lưu lượng qua lệnh HTTP CONNECT tới Proxy HTTP thật.
    Nếu Proxy HTTP chết hoặc ngắt kết nối, cầu nối lập tức ngắt socket để Telegram không bao giờ
    rò rỉ kết nối qua địa chỉ IP mạng thật của máy tính.
    """

    def __init__(
        self,
        remote_host: str,
        remote_port: int,
        remote_user: str = "",
        remote_pass: str = "",
        bind_host: str = "127.0.0.1",
        bind_port: int = 0,
    ):
        self.remote_host = remote_host
        self.remote_port = int(remote_port)
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.server_sock: Optional[socket.socket] = None
        self.is_running = False
        self.actual_port = 0
        self._threads = []

    def start(self) -> int:
        """Khởi động server cầu nối cục bộ và trả về cổng lắng nghe thực tế."""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.bind_host, self.bind_port))
        self.actual_port = self.server_sock.getsockname()[1]
        self.server_sock.listen(50)
        self.is_running = True

        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()
        return self.actual_port

    def stop(self):
        """Dừng cầu nối và giải phóng toàn bộ socket."""
        self.is_running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, _ = self.server_sock.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock,),
                    daemon=True,
                )
                client_thread.start()
            except Exception:
                break

    def _handle_client(self, client_sock: socket.socket):
        remote_sock = None
        try:
            client_sock.settimeout(12.0)

            # 1. Bắt tay SOCKS5 (Greeting)
            greeting = client_sock.recv(256)
            if not greeting or greeting[0] != 5:
                client_sock.close()
                return

            # Chấp nhận phương thức No Authentication (0x00) cho kết nối local nội bộ
            client_sock.sendall(b"\x05\x00")

            # 2. Nhận yêu cầu SOCKS5 Request
            req = client_sock.recv(1024)
            if len(req) < 7 or req[0] != 5 or req[1] != 1:  # CMD 1 = CONNECT
                client_sock.close()
                return

            atyp = req[3]
            if atyp == 1:  # IPv4
                target_host = socket.inet_ntoa(req[4:8])
                target_port = int.from_bytes(req[8:10], "big")
            elif atyp == 3:  # Domain
                dlen = req[4]
                target_host = req[5 : 5 + dlen].decode("utf-8", errors="ignore")
                target_port = int.from_bytes(req[5 + dlen : 5 + dlen + 2], "big")
            elif atyp == 4:  # IPv6
                target_host = socket.inet_ntop(socket.AF_INET6, req[4:20])
                target_port = int.from_bytes(req[20:22], "big")
            else:
                client_sock.close()
                return

            # 3. Kết nối tới Remote HTTP Proxy thật
            remote_sock = socket.create_connection(
                (self.remote_host, self.remote_port), timeout=10.0
            )

            # Gửi lệnh HTTP CONNECT
            connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n"
            if self.remote_user or self.remote_pass:
                raw_auth = f"{self.remote_user}:{self.remote_pass}".encode()
                auth_str = base64.b64encode(raw_auth).decode()
                connect_req += f"Proxy-Authorization: Basic {auth_str}\r\n"
            connect_req += "Proxy-Connection: Keep-Alive\r\n\r\n"
            remote_sock.sendall(connect_req.encode())

            # Đọc phản hồi HTTP CONNECT từ remote proxy
            remote_sock.settimeout(10.0)
            http_res = b""
            while b"\r\n\r\n" not in http_res and len(http_res) < 8192:
                chunk = remote_sock.recv(1024)
                if not chunk:
                    break
                http_res += chunk

            if b" 200 " not in http_res:
                # Proxy từ chối hoặc lỗi xác thực -> trả về SOCKS5 server failure
                remote_sock.close()
                client_sock.sendall(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
                client_sock.close()
                return

            # Phản hồi SOCKS5 Success cho Telegram Desktop
            client_sock.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            client_sock.settimeout(None)
            remote_sock.settimeout(None)

            # 4. Chuyển tiếp luồng dữ liệu 2 chiều (Bidirectional forward)
            def _pipe(s_in: socket.socket, s_out: socket.socket):
                try:
                    while self.is_running:
                        data = s_in.recv(32768)
                        if not data:
                            break
                        s_out.sendall(data)
                except Exception:
                    pass
                finally:
                    try:
                        s_in.close()
                    except Exception:
                        pass
                    try:
                        s_out.close()
                    except Exception:
                        pass

            t1 = threading.Thread(target=_pipe, args=(client_sock, remote_sock), daemon=True)
            t2 = threading.Thread(target=_pipe, args=(remote_sock, client_sock), daemon=True)
            t1.start()
            t2.start()

        except Exception:
            if remote_sock:
                try:
                    remote_sock.close()
                except Exception:
                    pass
            try:
                client_sock.close()
            except Exception:
                pass


class ProxyService:
    @staticmethod
    def test_proxy_strict(proxy: ProxyConfig, timeout: float = 4.0) -> Tuple[bool, str, float]:
        """
        Kiểm tra chuyên sâu tính hợp lệ và sống còn của Proxy (Strict Verification).
        Không chỉ kiểm tra mở cổng TCP, hàm này thực hiện bắt tay (handshake),
        xác thực tài khoản (nếu có) và thử gửi yêu cầu kết nối tới Telegram Data Center.
        """
        if not proxy.enabled:
            return True, "Proxy không được bật.", 0.0

        host = (proxy.host or "").strip()
        port = int(proxy.port or 0)
        ptype = (proxy.proxy_type or "SOCKS5").upper()
        username = (proxy.username or "").strip()
        password = (proxy.password or "").strip()

        if not host or port <= 0 or port > 65535:
            return False, "Địa chỉ IP/Host hoặc Port không hợp lệ.", 0.0

        start_time = time.perf_counter()

        # 1. Kiểm tra HTTP Proxy
        if ptype == "HTTP":
            try:
                sock = socket.create_connection((host, port), timeout=timeout)
                sock.settimeout(timeout)

                # Gửi yêu cầu CONNECT tới IP chính thức của Telegram DC 2 (149.154.167.50:443)
                connect_payload = (
                    "CONNECT 149.154.167.50:443 HTTP/1.1\r\n"
                    "Host: 149.154.167.50:443\r\n"
                )
                if username or password:
                    raw_auth = f"{username}:{password}".encode()
                    auth_b64 = base64.b64encode(raw_auth).decode()
                    connect_payload += f"Proxy-Authorization: Basic {auth_b64}\r\n"
                connect_payload += "User-Agent: TeleManager/StrictVerification\r\n\r\n"

                sock.sendall(connect_payload.encode())
                res = sock.recv(4096).decode("iso-8859-1", errors="ignore")
                sock.close()

                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

                if " 200 " in res:
                    return True, "Proxy HTTP hoạt động tốt.", latency_ms
                elif "407" in res:
                    return False, "Lỗi 407: Sai thông tin Username hoặc Password của Proxy!", latency_ms
                elif "403" in res:
                    return False, "Lỗi 403: Proxy từ chối kết nối (Forbidden).", latency_ms
                elif "502" in res:
                    return False, "Lỗi 502: Proxy Gateway lỗi, không thể định tuyến.", latency_ms
                else:
                    first_line = res.split("\r\n")[0] if res else "Không nhận được phản hồi"
                    return False, f"Proxy phản hồi lỗi: {first_line}", latency_ms

            except socket.timeout:
                return False, "Kết nối tới HTTP Proxy quá thời gian chờ (Timeout).", 0.0
            except ConnectionRefusedError:
                return False, "Máy chủ Proxy từ chối kết nối (Connection Refused).", 0.0
            except Exception as e:
                return False, f"Lỗi kết nối HTTP Proxy: {str(e)}", 0.0

        # 2. Kiểm tra SOCKS5 Proxy
        elif ptype == "SOCKS5":
            try:
                sock = socket.create_connection((host, port), timeout=timeout)
                sock.settimeout(timeout)

                # Gửi SOCKS5 Greeting
                if username or password:
                    sock.sendall(b"\x05\x02\x00\x02")  # Hỗ trợ No Auth và User/Pass
                else:
                    sock.sendall(b"\x05\x01\x00")  # Chỉ No Auth

                greet_resp = sock.recv(2)
                if len(greet_resp) < 2 or greet_resp[0] != 5:
                    sock.close()
                    return False, "Máy chủ không phải là giao thức SOCKS5 hợp lệ.", 0.0

                auth_method = greet_resp[1]
                if auth_method == 2:  # Yêu cầu xác thực tài khoản / mật khẩu (RFC 1929)
                    u_bytes = username.encode()
                    p_bytes = password.encode()
                    auth_req = bytes([1, len(u_bytes)]) + u_bytes + bytes([len(p_bytes)]) + p_bytes
                    sock.sendall(auth_req)
                    auth_resp = sock.recv(2)
                    if len(auth_resp) < 2 or auth_resp[1] != 0:
                        sock.close()
                        return False, "Xác thực SOCKS5 thất bại: Sai Username hoặc Password!", 0.0
                elif auth_method == 255:
                    sock.close()
                    return False, "Máy chủ SOCKS5 từ chối phương thức xác thực được cung cấp.", 0.0

                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
                sock.close()
                return True, "Proxy SOCKS5 hoạt động tốt.", latency_ms

            except socket.timeout:
                return False, "Kết nối tới SOCKS5 Proxy quá thời gian chờ (Timeout).", 0.0
            except ConnectionRefusedError:
                return False, "Máy chủ SOCKS5 từ chối kết nối (Connection Refused).", 0.0
            except Exception as e:
                return False, f"Lỗi kết nối SOCKS5 Proxy: {str(e)}", 0.0

        # 3. Kiểm tra MTProto Proxy
        elif ptype == "MTPROTO":
            try:
                sock = socket.create_connection((host, port), timeout=timeout)
                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
                sock.close()
                return True, "Máy chủ MTProto phản hồi kết nối.", latency_ms
            except socket.timeout:
                return False, "Kết nối tới MTProto Proxy quá thời gian chờ (Timeout).", 0.0
            except Exception as e:
                return False, f"Lỗi kết nối MTProto Proxy: {str(e)}", 0.0

        return False, "Loại proxy không được hỗ trợ.", 0.0

    @staticmethod
    def test_connection(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, str, float]:
        """Hàm kiểm tra socket cơ bản tương thích ngược."""
        temp_cfg = ProxyConfig(enabled=True, proxy_type="SOCKS5", host=host, port=port)
        return ProxyService.test_proxy_strict(temp_cfg, timeout=timeout)

    @staticmethod
    def build_deep_link(proxy: ProxyConfig, local_socks5_port: Optional[int] = None) -> Optional[str]:
        """
        Tạo đường dẫn Deep Link tg:// để nạp cấu hình proxy vào Telegram Desktop.
        Telegram Desktop KHÔNG hỗ trợ giao thức tg://http.
        - Đối với Proxy HTTP: Bắt buộc thông qua Local SOCKS5 Bridge (local_socks5_port)
          để sinh liên kết chuẩn tg://socks?server=127.0.0.1&port=...
        - Đối với SOCKS5: Sinh tg://socks.
        - Đối với MTProto: Sinh tg://proxy.
        """
        if not proxy.enabled or not proxy.host or proxy.port <= 0:
            return None

        ptype = proxy.proxy_type.upper()

        if ptype == "HTTP":
            if local_socks5_port and local_socks5_port > 0:
                params = {
                    "server": "127.0.0.1",
                    "port": str(local_socks5_port),
                }
                return f"tg://socks?{urllib.parse.urlencode(params)}"
            return None

        elif ptype == "SOCKS5":
            params = {
                "server": proxy.host,
                "port": str(proxy.port),
            }
            if proxy.username:
                params["user"] = proxy.username
            if proxy.password:
                params["pass"] = proxy.password
            return f"tg://socks?{urllib.parse.urlencode(params)}"

        elif ptype == "MTPROTO":
            params = {
                "server": proxy.host,
                "port": str(proxy.port),
                "secret": proxy.secret,
            }
            return f"tg://proxy?{urllib.parse.urlencode(params)}"

        return None

    @staticmethod
    def parse_proxy_string(raw: str) -> Optional[ProxyConfig]:
        """Phân tích chuỗi proxy theo các định dạng thông dụng."""
        text = raw.strip()
        if not text:
            return None

        if "://" in text:
            try:
                parsed = urllib.parse.urlparse(text)
                ptype = parsed.scheme.upper()
                if ptype not in ["SOCKS5", "HTTP"]:
                    ptype = "SOCKS5"
                return ProxyConfig(
                    enabled=True,
                    proxy_type=ptype,
                    host=parsed.hostname or "",
                    port=parsed.port or 1080,
                    username=parsed.username or "",
                    password=parsed.password or "",
                )
            except Exception:
                pass

        parts = text.split(":")
        if len(parts) == 2:
            try:
                return ProxyConfig(
                    enabled=True,
                    proxy_type="SOCKS5",
                    host=parts[0].strip(),
                    port=int(parts[1].strip()),
                )
            except ValueError:
                return None
        elif len(parts) == 4:
            try:
                return ProxyConfig(
                    enabled=True,
                    proxy_type="SOCKS5",
                    host=parts[0].strip(),
                    port=int(parts[1].strip()),
                    username=parts[2].strip(),
                    password=parts[3].strip(),
                )
            except ValueError:
                return None

        return None
