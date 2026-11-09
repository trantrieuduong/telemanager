import os
import json
import shutil
import re
import zipfile
from datetime import datetime
from typing import List, Tuple, Optional
from ..models.profile import Profile, ProxyConfig


class ProfileService:
    # Các ký tự bị cấm trong tên thư mục của hệ điều hành Windows
    INVALID_CHARS_REGEX = re.compile(r'[<>:"/\\|?*]')

    @classmethod
    def validate_folder_name(cls, name: str) -> Tuple[bool, str, str]:
        """Kiểm tra và làm sạch tên thư mục theo quy tắc của Windows."""
        stripped = name.strip()
        if not stripped:
            return False, "Tên không được để trống hoặc chỉ chứa khoảng trắng.", ""

        if cls.INVALID_CHARS_REGEX.search(stripped):
            return False, 'Tên chứa ký tự không hợp lệ (không được chứa: < > : " / \\ | ? *)', ""

        # Loại bỏ các dấu chấm ở cuối tên thư mục vì Windows không cho phép
        safe_name = stripped.rstrip(". ")
        if not safe_name:
            return False, "Tên thư mục không hợp lệ.", ""

        return True, "", safe_name

    @classmethod
    def list_profiles(cls, profiles_dir: str) -> List[Profile]:
        """Đọc tất cả các profile hiện có trong thư mục profiles."""
        if not os.path.exists(profiles_dir):
            return []

        profiles = []
        try:
            entries = os.listdir(profiles_dir)
        except Exception:
            return []

        for entry in entries:
            folder_path = os.path.join(profiles_dir, entry)
            if not os.path.isdir(folder_path):
                continue

            meta_file = os.path.join(folder_path, "meta.json")
            profile_data = {}
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                except Exception:
                    profile_data = {}

            profile = Profile.from_dict(folder_name=entry, data=profile_data)
            profiles.append(profile)

        # Sắp xếp danh sách theo tên hiển thị
        profiles.sort(key=lambda p: (p.display_name or p.folder_name).lower())
        return profiles

    @classmethod
    def create_profile(
        cls,
        profiles_dir: str,
        folder_name: str,
        display_name: str = "",
        notes: str = "",
        proxy: Optional[ProxyConfig] = None,
    ) -> Tuple[bool, str, Optional[Profile]]:
        """Tạo một profile mới với kiểm tra hợp lệ và trùng lặp."""
        is_valid, err_msg, safe_name = cls.validate_folder_name(folder_name)
        if not is_valid:
            return False, err_msg, None

        # Kiểm tra trùng tên thư mục (không phân biệt hoa thường)
        existing_folders = [
            f.lower()
            for f in os.listdir(profiles_dir)
            if os.path.isdir(os.path.join(profiles_dir, f))
        ]
        if safe_name.lower() in existing_folders:
            return False, f"Thư mục profile '{safe_name}' đã tồn tại.", None

        target_dir = os.path.join(profiles_dir, safe_name)
        try:
            os.makedirs(target_dir, exist_ok=False)
        except Exception as e:
            return False, f"Không thể tạo thư mục: {str(e)}", None

        # Khởi tạo đối tượng Profile và lưu meta.json
        final_display_name = display_name.strip() if display_name.strip() else safe_name
        profile = Profile(
            folder_name=safe_name,
            display_name=final_display_name,
            notes=notes.strip(),
            proxy=proxy or ProxyConfig(),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        cls.save_profile_meta(profiles_dir, profile)
        return True, "Tạo profile thành công.", profile

    @classmethod
    def update_profile(
        cls,
        profiles_dir: str,
        current_folder: str,
        new_folder_name: str,
        display_name: str,
        notes: str,
        proxy: ProxyConfig,
        is_running: bool,
    ) -> Tuple[bool, str, str]:
        """Cập nhật thông tin profile và đổi tên thư mục nếu có yêu cầu."""
        final_folder_name = current_folder
        old_path = os.path.join(profiles_dir, current_folder)

        if not os.path.exists(old_path):
            return False, f"Không tìm thấy thư mục profile: {current_folder}", current_folder

        # Xử lý đổi tên thư mục nếu có sự thay đổi
        clean_new_folder = new_folder_name.strip()
        if clean_new_folder and clean_new_folder.lower() != current_folder.lower():
            if is_running:
                return False, "Tài khoản đang hoạt động. Vui lòng đóng Telegram trước khi đổi tên thư mục.", current_folder

            is_valid, err_msg, safe_new_name = cls.validate_folder_name(clean_new_folder)
            if not is_valid:
                return False, err_msg, current_folder

            # Kiểm tra xem tên mới có bị trùng với folder khác không
            existing_folders = [
                f.lower()
                for f in os.listdir(profiles_dir)
                if os.path.isdir(os.path.join(profiles_dir, f)) and f.lower() != current_folder.lower()
            ]
            if safe_new_name.lower() in existing_folders:
                return False, f"Thư mục '{safe_new_name}' đã tồn tại.", current_folder

            new_path = os.path.join(profiles_dir, safe_new_name)
            try:
                os.rename(old_path, new_path)
                final_folder_name = safe_new_name
            except Exception as e:
                return False, f"Lỗi khi đổi tên thư mục: {str(e)}", current_folder

        # Lưu metadata mới
        final_display_name = display_name.strip() if display_name.strip() else final_folder_name
        profile = Profile(
            folder_name=final_folder_name,
            display_name=final_display_name,
            notes=notes.strip(),
            proxy=proxy,
        )
        cls.save_profile_meta(profiles_dir, profile)
        return True, "Cập nhật profile thành công.", final_folder_name

    @classmethod
    def delete_profile(
        cls, profiles_dir: str, folder_name: str, is_running: bool
    ) -> Tuple[bool, str]:
        """Xóa một profile với cơ chế bảo vệ an toàn dữ liệu."""
        if is_running:
            return (
                False,
                f"Tài khoản '{folder_name}' đang chạy. Vui lòng đóng Telegram trước khi xóa.",
            )

        target_path = os.path.join(profiles_dir, folder_name)
        if not os.path.exists(target_path):
            return False, f"Không tìm thấy thư mục profile: {folder_name}"

        try:
            shutil.rmtree(target_path)
            return True, "Đã xóa profile thành công."
        except PermissionError:
            return (
                False,
                "Không thể xóa vì một số file đang bị khóa bởi hệ thống. Vui lòng kiểm tra và tắt tiến trình Telegram liên quan.",
            )
        except Exception as e:
            return False, f"Lỗi khi xóa: {str(e)}"

    @classmethod
    def export_profile_to_zip(
        cls, profiles_dir: str, folder_name: str, export_zip_path: str, is_running: bool
    ) -> Tuple[bool, str]:
        """Sao lưu (nén) toàn bộ thư mục profile và dữ liệu phiên thành file .zip duy nhất."""
        if is_running:
            return (
                False,
                f"Tài khoản '{folder_name}' đang chạy. Vui lòng đóng Telegram trước khi sao lưu để đảm bảo toàn vẹn dữ liệu phiên đăng nhập.",
            )

        source_dir = os.path.join(profiles_dir, folder_name)
        if not os.path.exists(source_dir):
            return False, f"Không tìm thấy thư mục profile: {folder_name}"

        try:
            with zipfile.ZipFile(export_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Đường dẫn tương đối bên trong file zip
                        rel_path = os.path.relpath(file_path, source_dir)
                        zf.write(file_path, rel_path)
            return True, "Đã sao lưu profile thành file zip thành công."
        except Exception as e:
            return False, f"Lỗi khi tạo file zip: {str(e)}"

    @classmethod
    def import_profile_from_zip(
        cls, profiles_dir: str, zip_path: str, custom_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Profile]]:
        """Phục hồi (giải nén) profile từ file .zip vào thư mục profiles."""
        if not os.path.exists(zip_path):
            return False, "File zip không tồn tại.", None

        # Xác định tên thư mục đích
        if custom_name and custom_name.strip():
            base_name = custom_name.strip()
        else:
            filename = os.path.splitext(os.path.basename(zip_path))[0]
            base_name = re.sub(r"^(backup|profile)[-_]", "", filename, flags=re.IGNORECASE).strip()
            if not base_name:
                base_name = filename

        is_valid, err_msg, safe_name = cls.validate_folder_name(base_name)
        if not is_valid:
            safe_name = "imported_profile"

        # Đảm bảo không ghi đè lên thư mục hiện có
        existing = [
            f.lower()
            for f in os.listdir(profiles_dir)
            if os.path.isdir(os.path.join(profiles_dir, f))
        ]
        final_name = safe_name
        counter = 1
        while final_name.lower() in existing:
            final_name = f"{safe_name}_{counter}"
            counter += 1

        target_dir = os.path.join(profiles_dir, final_name)
        try:
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)

            # Đọc lại meta nếu có hoặc tạo meta mặc định
            meta_file = os.path.join(target_dir, "meta.json")
            meta_data = {}
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                except Exception:
                    meta_data = {}

            profile = Profile.from_dict(folder_name=final_name, data=meta_data)
            # Cập nhật lại tên hiển thị nếu chưa có
            if not profile.display_name:
                profile.display_name = final_name
            cls.save_profile_meta(profiles_dir, profile)

            return True, f"Đã nhập tài khoản '{profile.display_name}' thành công.", profile
        except Exception as e:
            # Dọn dẹp nếu giải nén bị lỗi giữa chừng
            if os.path.exists(target_dir):
                try:
                    shutil.rmtree(target_dir)
                except Exception:
                    pass
            return False, f"Lỗi khi giải nén file zip: {str(e)}", None

    @classmethod
    def save_profile_meta(cls, profiles_dir: str, profile: Profile) -> bool:
        """Lưu thông tin metadata vào file meta.json trong thư mục profile."""
        meta_file = os.path.join(profiles_dir, profile.folder_name, "meta.json")
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
