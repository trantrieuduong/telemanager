from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ProxyConfig:
    enabled: bool = False
    proxy_type: str = "SOCKS5"  # SOCKS5, HTTP, MTProto
    host: str = ""
    port: int = 1080
    username: str = ""
    password: str = ""
    secret: str = ""  # Dành riêng cho giao thức MTProto

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "proxy_type": self.proxy_type,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "secret": self.secret,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyConfig":
        if not isinstance(data, dict):
            return cls()
        return cls(
            enabled=data.get("enabled", False),
            proxy_type=data.get("proxy_type", "SOCKS5"),
            host=data.get("host", ""),
            port=int(data.get("port", 1080) or 1080),
            username=data.get("username", ""),
            password=data.get("password", ""),
            secret=data.get("secret", ""),
        )


@dataclass
class Profile:
    folder_name: str
    display_name: str = ""
    notes: str = ""
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    created_at: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.folder_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "display_name": self.display_name,
            "notes": self.notes,
            "proxy": self.proxy.to_dict(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, folder_name: str, data: Dict[str, Any]) -> "Profile":
        if not isinstance(data, dict):
            return cls(folder_name=folder_name, display_name=folder_name)

        proxy_data = data.get("proxy", {})
        proxy_config = ProxyConfig.from_dict(proxy_data)

        return cls(
            folder_name=folder_name,
            display_name=data.get("display_name") or folder_name,
            notes=data.get("notes", ""),
            proxy=proxy_config,
            created_at=data.get("created_at", ""),
        )
