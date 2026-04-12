from dataclasses import dataclass
from typing import Optional


@dataclass
class Device:
    ip: str
    mac: str
    vendor: str = "Unknown"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    is_local_admin: bool = False
    hostname: str = ""
    status: str = "UNKNOWN"
    os_guess: str = "Unknown"