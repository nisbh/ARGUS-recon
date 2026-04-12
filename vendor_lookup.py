import os
import re


def load_oui(oui_path: str) -> dict:
    oui_db = {}

    if not os.path.exists(oui_path):
        print(f"Warning: OUI file not found at {oui_path}.")
        return oui_db

    with open(oui_path, "r", encoding="utf-8", errors="ignore") as oui_file:
        for line in oui_file:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                continue

            columns = stripped.split()
            if len(columns) < 3:
                continue

            prefix = columns[0]
            if prefix.count(":") > 2:
                continue

            normalized_prefix = prefix.replace(":", "").upper()[:6]
            vendor_name = " ".join(columns[2:]).strip()
            oui_db[normalized_prefix] = vendor_name

    return oui_db


def get_vendor(mac: str, oui_db: dict) -> str:
    normalized_mac = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    prefix = normalized_mac[:6]
    return oui_db.get(prefix, "Unknown")