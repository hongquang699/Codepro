"""Emergency threat containment (IP blacklist, maintenance lock)."""
from typing import Set

class EmergencyContainment:
    _banned_ips: Set[str] = set()
    _banned_users: Set[str] = set()
    _maintenance_mode: bool = False

    @classmethod
    def ban_ip(cls, ip: str):
        if ip:
            cls._banned_ips.add(ip.strip())

    @classmethod
    def unban_ip(cls, ip: str):
        cls._banned_ips.discard(ip.strip())

    @classmethod
    def is_ip_banned(cls, ip: str) -> bool:
        return ip.strip() in cls._banned_ips

    @classmethod
    def ban_user(cls, username: str):
        if username:
            cls._banned_users.add(username.strip().lower())

    @classmethod
    def is_user_banned(cls, username: str) -> bool:
        return username.strip().lower() in cls._banned_users

    @classmethod
    def set_maintenance_mode(cls, enabled: bool):
        cls._maintenance_mode = enabled

    @classmethod
    def is_maintenance_mode(cls) -> bool:
        return cls._maintenance_mode
