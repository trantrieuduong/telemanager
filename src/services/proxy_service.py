import socket
import time
import urllib.parse
from typing import Tuple, Optional
from ..models.profile import ProxyConfig


class ProxyService:
    @staticmethod
    def test_connection(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, str, float]:
        """Kiểm tra kết nối TCP tới proxy và đo độ trễ (latency tính bằng mili-giây)."""
        if not host or port <= 0 or port > 65535:
            return False, "Địa chỉ IP/Host hoặc Port không hợp lệ.", 0.0

        start_time = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                return True, "Kết nối thành công.", round(latency_ms, 1)
        except socket.timeout:
            return False, "Kết nối quá thời gian chờ (Timeout).", 0.0
        except Exception as e:
            return False, f"Lỗi kết nối: {str(e)}", 0.0

    @staticmethod
    def build_deep_link(proxy: ProxyConfig) -> Optional[str]:
        """Tạo đường dẫn Deep Link tg:// để Telegram hiển thị hộp thoại xác nhận áp dụng proxy."""
        if not proxy.enabled or not proxy.host or proxy.port <= 0:
            return None

        ptype = proxy.proxy_type.upper()
        if ptype == "SOCKS5":
            params = {
                "server": proxy.host,
                "port": str(proxy.port),
            }
            if proxy.username:
                params["user"] = proxy.username
            if proxy.password:
                params["pass"] = proxy.password
            return f"tg://socks?{urllib.parse.urlencode(params)}"

        elif ptype == "HTTP":
            params = {
                "server": proxy.host,
                "port": str(proxy.port),
            }
            if proxy.username:
                params["user"] = proxy.username
            if proxy.password:
                params["pass"] = proxy.password
            return f"tg://http?{urllib.parse.urlencode(params)}"

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
        """Phân tích cú pháp nhanh từ các dạng chuỗi proxy phổ biến:
        - host:port
        - host:port:user:pass
        - socks5://user:pass@host:port
        - http://user:pass@host:port
        """
        text = raw.strip()
        if not text:
            return None

        # Dạng URL scheme: socks5://user:pass@host:port
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

        # Dạng host:port:user:pass hoặc host:port
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
