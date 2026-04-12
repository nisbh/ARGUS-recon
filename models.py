from dataclasses import dataclass
from typing import Optional


@dataclass
class Device:
    ip: str
    mac: str
    vendor: str = "Unknown"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None