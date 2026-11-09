import os
import subprocess
import threading
from typing import Dict, Set, Optional


class ProcessService:
    def __init__(self):
        # Lưu trữ các tiến trình được khởi chạy trực tiếp từ ứng dụng
        self._active_processes: Dict[str, subprocess.Popen] = {}
        # Bộ nhớ đệm danh sách profile đang chạy được quét từ hệ thống
        self._system_running_profiles: Set[str] = set()
        self._is_scanning = False

    def launch(
        self,
        exe_path: str,
        profile_path: str,
        folder_name: str,
        deep_link: Optional[str] = None,
    ) -> bool:
        """Khởi chạy Telegram.exe với tham số -workdir và liên kết deep link nếu có."""
        if not os.path.exists(exe_path):
            return False

        if not os.path.exists(profile_path):
            os.makedirs(profile_path, exist_ok=True)

        cmd = [exe_path, "-workdir", profile_path]
        if deep_link:
            cmd.append(deep_link)

        try:
            proc = subprocess.Popen(cmd)
            key = folder_name.lower()
            self._active_processes[key] = proc
            self._system_running_profiles.add(key)
            return True
        except Exception:
            return False

    def terminate_profile(self, profile_path: str, folder_name: str) -> bool:
        """Đóng tiến trình Telegram đang chạy của profile một cách an toàn và triệt để."""
        key = folder_name.lower()
        stopped_any = False

        # 1. Đóng tiến trình được quản lý bởi Popen
        proc = self._active_processes.get(key)
        if proc is not None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                stopped_any = True
            except Exception:
                pass
            finally:
                self._active_processes.pop(key, None)

        # 2. Tìm và đóng tất cả tiến trình Telegram.exe có CommandLine khớp với thư mục profile
        norm_profile_path = os.path.abspath(profile_path).replace("'", "''")
        ps_kill_cmd = (
            f"$target = '{norm_profile_path}'.ToLower(); "
            "Get-CimInstance Win32_Process -Filter \"name = 'Telegram.exe'\" | "
            "Where-Object { $_.CommandLine -and $_.CommandLine.ToLower().Contains($target) } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        )

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_kill_cmd],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
            )
            if res.returncode == 0:
                stopped_any = True
        except Exception:
            pass

        # Xóa khỏi bộ nhớ đệm trạng thái chạy
        self._system_running_profiles.discard(key)
        return stopped_any

    def is_running(self, folder_name: str) -> bool:
        """Kiểm tra một profile có đang hoạt động hay không."""
        key = folder_name.lower()

        # 1. Kiểm tra tiến trình được giữ trong phiên của ứng dụng
        proc = self._active_processes.get(key)
        if proc is not None:
            if proc.poll() is None:
                return True
            else:
                del self._active_processes[key]

        # 2. Kiểm tra từ danh sách hệ thống đã quét
        return key in self._system_running_profiles

    def scan_running_profiles_async(self, profiles_dir: str):
        """Quét hệ thống trong luồng nền để tìm các profile đang chạy."""
        if self._is_scanning:
            return

        def _scan():
            self._is_scanning = True
            try:
                running = self._detect_running_profiles_from_system(profiles_dir)
                self._system_running_profiles = running
            finally:
                self._is_scanning = False

        thread = threading.Thread(target=_scan, daemon=True)
        thread.start()

    def _detect_running_profiles_from_system(self, profiles_dir: str) -> Set[str]:
        """Truy vấn các tiến trình Telegram.exe qua PowerShell để kiểm tra dòng lệnh."""
        running_set: Set[str] = set()
        norm_profiles_dir = os.path.abspath(profiles_dir).lower()

        ps_cmd = (
            'Get-CimInstance Win32_Process -Filter "name = \'Telegram.exe\'" '
            "| ForEach-Object { $_.CommandLine }"
        )

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.splitlines()
                for line in lines:
                    line_lower = line.lower()
                    if "-workdir" in line_lower and norm_profiles_dir in line_lower:
                        idx = line_lower.find(norm_profiles_dir)
                        if idx != -1:
                            sub = line[idx + len(norm_profiles_dir) :]
                            sub = sub.lstrip("\\/\"'")
                            folder = ""
                            for char in sub:
                                if char in ['\\', '/', '"', "'"]:
                                    break
                                folder += char
                            folder = folder.strip()
                            if folder:
                                running_set.add(folder.lower())
        except Exception:
            pass

        # Hợp nhất với các tiến trình vẫn đang hoạt động trong phiên ứng dụng
        for k, p in list(self._active_processes.items()):
            if p.poll() is None:
                running_set.add(k)
            else:
                del self._active_processes[k]

        return running_set
