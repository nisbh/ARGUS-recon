import json
import os

from tabulate import tabulate

from db import get_all_devices, init_db, upsert_device
from models import Device


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


# Assumption: this utility intentionally omits KeyboardInterrupt handling per the seed_db-specific requirement.
def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    config = load_config(config_path)

    db_path = os.path.abspath(os.path.join(script_dir, config["db_path"]))

    init_db(db_path)

    # Assumption: tabulate is imported here to satisfy the required output format.
    fake_devices = [
        Device(ip="192.168.1.10", mac="a4:c3:f0:11:22:33", vendor="Apple, Inc."),
        Device(ip="192.168.1.21", mac="34:ab:37:44:55:66", vendor="Samsung Electronics Co.,Ltd"),
        Device(ip="192.168.1.35", mac="b8:27:eb:77:88:99", vendor="Raspberry Pi Trading Ltd"),
        Device(ip="192.168.1.42", mac="f0:18:98:aa:bb:cc", vendor="Dell Inc."),
        Device(ip="192.168.1.88", mac="de:ad:be:ef:00:01", vendor="Unknown"),
    ]

    for device in fake_devices:
        upsert_device(db_path, device)

    devices = get_all_devices(db_path)

    table_data = []
    for device in devices:
        table_data.append(
            [
                device.ip,
                device.mac,
                device.vendor,
                device.first_seen,
                device.last_seen,
            ]
        )

    print("ARGUS-RECON — Network Device Table")
    print(
        tabulate(
            table_data,
            headers=["IP Address", "MAC Address", "Vendor", "First Seen", "Last Seen"],
            tablefmt="pretty",
        )
    )
    print(f"Seed complete. {len(devices)} devices in database.")


if __name__ == "__main__":
    main()