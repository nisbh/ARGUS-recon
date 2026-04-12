import argparse
import json
import os
import sys
import time

from tabulate import tabulate

from db import get_all_devices, init_db, upsert_device
from models import Device
from scanner import scan_network
from vendor_lookup import get_vendor, load_oui


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def print_device_table(devices: list[Device]) -> None:
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


def run_scan_cycle(interface: str, subnet: str, db_path: str, oui_db: dict) -> None:
    scanned_devices = scan_network(interface, subnet)
    for device in scanned_devices:
        device.vendor = get_vendor(device.mac, oui_db)
        upsert_device(db_path, device)

    devices_for_display = get_all_devices(db_path)
    print_device_table(devices_for_display)


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    config = load_config(config_path)

    interface = config["interface"]
    subnet = config["subnet"]
    db_path = os.path.abspath(os.path.join(script_dir, config["db_path"]))

    init_db(db_path)

    oui_path = os.path.join(script_dir, "oui.txt")
    oui_db = load_oui(oui_path)

    parser = argparse.ArgumentParser(description="ARGUS-RECON network scanner")
    parser.add_argument(
        "--rescan",
        action="store_true",
        help="Run scans continuously every 60 seconds.",
    )
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("ARP scanning requires root privileges. Run with sudo.")
        sys.exit(1)

    try:
        if args.rescan:
            while True:
                os.system("clear")
                run_scan_cycle(interface, subnet, db_path, oui_db)
                time.sleep(60)
        else:
            run_scan_cycle(interface, subnet, db_path, oui_db)
    except KeyboardInterrupt:
        print("Scan stopped. Database saved.")
        sys.exit(0)
    except ValueError as error:
        print(f"Scan configuration error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()