import argparse
import csv
import json
import os
import socket
import sys
import time
from datetime import datetime

from tabulate import tabulate

from db import get_all_devices, init_db, upsert_device
from enrichment import mdns_lookup, netbios_lookup
from fingerprint import guess_os
from models import Device
from probe import probe_host
from scanner import scan_network
from vendor_lookup import get_vendor, load_oui


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def validate_required_fields(config: dict) -> None:
    required_fields = ["interface", "gateway_ip", "subnet", "db_path"]
    for field in required_fields:
        if field not in config:
            print(f"[ARGUS-RECON] ERROR: Missing required config field: {field}")
            sys.exit(1)


def validate_interface_exists(interface: str) -> None:
    if not os.path.exists(f"/sys/class/net/{interface}"):
        available_interfaces = ", ".join(sorted(os.listdir("/sys/class/net/")))
        print(f"[ARGUS-RECON] ERROR: Interface '{interface}' not found on this system.")
        print(f"Available interfaces: {available_interfaces}")
        sys.exit(1)


def is_locally_administered_mac(mac: str) -> bool:
    normalized_mac = mac.replace(":", "").replace("-", "")
    if len(normalized_mac) < 2:
        return False

    try:
        first_octet = int(normalized_mac[0:2], 16)
    except ValueError:
        return False

    return first_octet & 0x02 == 0x02


def resolve_hostname(ip_address: str) -> str:
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except (socket.herror, socket.gaierror):
        return ""


def format_status_for_display(status: str) -> str:
    normalized_status = status.upper() if status else "UNKNOWN"
    if normalized_status == "ACTIVE":
        return "✓ ACTIVE"
    if normalized_status == "STALE":
        return "✗ STALE"
    return "  UNKNOWN"


def print_device_table(devices: list[Device]) -> list[list[str]]:
    table_data = []
    for device in devices:
        flags = "⚠ local MAC" if device.is_local_admin else ""
        table_data.append(
            [
                device.ip,
                device.mac,
                device.vendor,
                device.hostname,
                device.os_guess,
                format_status_for_display(device.status),
                device.first_seen,
                device.last_seen,
                flags,
            ]
        )

    print("ARGUS-RECON — Network Device Table")
    print(
        tabulate(
            table_data,
            headers=[
                "IP Address",
                "MAC Address",
                "Vendor",
                "Hostname",
                "OS Guess",
                "Status",
                "First Seen",
                "Last Seen",
                "Flags",
            ],
            tablefmt="pretty",
        )
    )
    return table_data


def write_csv_report(table_data: list[list[str]]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"argus_recon_{timestamp}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "IP Address",
                "MAC Address",
                "Vendor",
                "Hostname",
                "OS Guess",
                "Status",
                "First Seen",
                "Last Seen",
                "Flags",
            ]
        )
        writer.writerows(table_data)
    return filename


def run_scan_cycle(
    interface: str,
    subnet: str,
    db_path: str,
    oui_db: dict,
    output_format: str | None,
    no_probe: bool,
) -> None:
    scanned_devices = scan_network(interface, subnet)
    scanned_by_mac = {}

    for device in scanned_devices:
        device.vendor = get_vendor(device.mac, oui_db)
        device.hostname = resolve_hostname(device.ip)

        if not device.hostname:
            mdns_hostname = mdns_lookup(device.ip)
            if mdns_hostname:
                device.hostname = mdns_hostname
            else:
                netbios_hostname = netbios_lookup(device.ip)
                if netbios_hostname:
                    device.hostname = netbios_hostname

        if no_probe:
            device.status = "UNKNOWN"
            device.os_guess = "Unknown"
        else:
            is_active = probe_host(device.ip)
            if is_active:
                device.status = "ACTIVE"
                device.os_guess = guess_os(device.ip)
            else:
                device.status = "STALE"
                device.os_guess = "Unknown"

        if is_locally_administered_mac(device.mac):
            device.is_local_admin = True
            device.vendor = "Unknown (randomised MAC)"

        upsert_device(db_path, device)
        scanned_by_mac[device.mac.lower()] = device

    devices_for_display = get_all_devices(db_path)
    for device in devices_for_display:
        scanned_device = scanned_by_mac.get(device.mac.lower())
        if scanned_device is not None:
            device.hostname = scanned_device.hostname
            device.is_local_admin = scanned_device.is_local_admin
            device.status = scanned_device.status
            device.os_guess = scanned_device.os_guess
            if scanned_device.is_local_admin:
                device.vendor = "Unknown (randomised MAC)"
        elif is_locally_administered_mac(device.mac):
            device.is_local_admin = True

    table_data = print_device_table(devices_for_display)

    if output_format == "csv":
        filename = write_csv_report(table_data)
        print(f"[ARGUS-RECON] Report saved to {filename}")


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    config = load_config(config_path)
    validate_required_fields(config)

    parser = argparse.ArgumentParser(description="ARGUS-RECON network scanner")
    parser.add_argument(
        "--rescan",
        action="store_true",
        help="Run scans continuously every 60 seconds.",
    )
    parser.add_argument(
        "--interface",
        help="Override the interface value from config.json.",
    )
    parser.add_argument(
        "--subnet",
        help="Override the subnet value from config.json.",
    )
    parser.add_argument(
        "--output",
        choices=["csv"],
        help="Write scan output to CSV after each scan cycle.",
    )
    parser.add_argument(
        "--no-probe",
        action="store_true",
        help="Disable ICMP probing and TTL fingerprinting.",
    )
    args = parser.parse_args()

    config_interface = config["interface"]
    validate_interface_exists(config_interface)

    interface = args.interface if args.interface else config_interface
    subnet = args.subnet if args.subnet else config["subnet"]
    validate_interface_exists(interface)

    db_path = os.path.abspath(os.path.join(script_dir, config["db_path"]))

    # Assumption: "project directory" means the directory containing main.py.
    project_root = script_dir
    if not db_path.endswith(".db"):
        print("[ARGUS-RECON] ERROR: db_path must point to a .db file.")
        sys.exit(1)

    oui_path = os.path.join(script_dir, "oui.txt")
    if not os.path.isfile(oui_path):
        print(f"[ARGUS-RECON] ERROR: oui.txt not found at {oui_path}")
        print(
            "Download it with: wget -O oui.txt https://www.wireshark.org/download/automated/data/manuf"
        )
        sys.exit(1)

    oui_db = load_oui(oui_path)

    init_db(db_path)

    print(f"[ARGUS-RECON] Scanning {subnet} on interface {interface}")
    print(f"[ARGUS-RECON] Host probing: {'DISABLED' if args.no_probe else 'ENABLED'}")

    if os.geteuid() != 0:
        print("ARP scanning requires root privileges. Run with sudo.")
        sys.exit(1)

    try:
        if args.rescan:
            while True:
                os.system("clear")
                run_scan_cycle(interface, subnet, db_path, oui_db, args.output, args.no_probe)
                time.sleep(60)
        else:
            run_scan_cycle(interface, subnet, db_path, oui_db, args.output, args.no_probe)
    except KeyboardInterrupt:
        print("Scan stopped. Database saved.")
        sys.exit(0)
    except ValueError as error:
        print(f"Scan configuration error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()