import sqlite3
from datetime import datetime

from models import Device


def init_db(db_path: str) -> None:
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            mac TEXT NOT NULL UNIQUE,
            vendor TEXT,
            first_seen TEXT,
            last_seen TEXT,
            status TEXT DEFAULT 'UNKNOWN',
            os_guess TEXT DEFAULT 'Unknown'
        )
        """
    )
    try:
        cursor.execute(
            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'UNKNOWN'"
        )
        cursor.execute(
            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS os_guess TEXT DEFAULT 'Unknown'"
        )
    except sqlite3.OperationalError:
        cursor.execute("PRAGMA table_info(devices)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "status" not in existing_columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'UNKNOWN'")

        if "os_guess" not in existing_columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN os_guess TEXT DEFAULT 'Unknown'")
    connection.commit()
    connection.close()


def upsert_device(db_path: str, device: Device) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM devices WHERE mac = ?", (device.mac,))
    existing_row = cursor.fetchone()

    if existing_row is None:
        cursor.execute(
            """
            INSERT INTO devices (ip, mac, vendor, first_seen, last_seen, status, os_guess)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device.ip,
                device.mac,
                device.vendor,
                now,
                now,
                device.status,
                device.os_guess,
            ),
        )
    else:
        cursor.execute(
            """
            UPDATE devices
            SET ip = ?, vendor = ?, last_seen = ?, status = ?, os_guess = ?
            WHERE mac = ?
            """,
            (device.ip, device.vendor, now, device.status, device.os_guess, device.mac),
        )

    connection.commit()
    connection.close()


def get_all_devices(db_path: str) -> list[Device]:
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT ip, mac, vendor, first_seen, last_seen, status, os_guess
        FROM devices
        ORDER BY last_seen DESC
        """
    )
    rows = cursor.fetchall()
    connection.close()

    devices = []
    for row in rows:
        devices.append(
            Device(
                ip=row[0],
                mac=row[1],
                vendor=row[2] if row[2] else "Unknown",
                first_seen=row[3],
                last_seen=row[4],
                status=row[5] if row[5] else "UNKNOWN",
                os_guess=row[6] if row[6] else "Unknown",
            )
        )
    return devices