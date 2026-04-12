import os
import re


def load_oui(oui_path: str) -> dict:
    oui_db = {}
    pattern = re.compile(
        r"^([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})\s+\(hex\)\s+(.+)$"
    )

    if not os.path.exists(oui_path):
        print(f"Warning: OUI file not found at {oui_path}.")
        return oui_db

    with open(oui_path, "r", encoding="utf-8", errors="ignore") as oui_file:
        for line in oui_file:
            match = pattern.match(line.strip())
            if match:
                prefix = (match.group(1) + match.group(2) + match.group(3)).upper()
                vendor_name = match.group(4).strip()
                oui_db[prefix] = vendor_name

    return oui_db


def get_vendor(mac: str, oui_db: dict) -> str:
    normalized_mac = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    prefix = normalized_mac[:6]
    return oui_db.get(prefix, "Unknown")