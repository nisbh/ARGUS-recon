# ARGUS-RECON
Network Discovery Module — Part of the ARGUS Framework

## Overview
- ARP-based device discovery on a local subnet
- MAC vendor identification via Wireshark OUI database
- SQLite storage, CLI table output
- Part of a 4-module framework (argus-recon, argus-veil, argus-oracle, argus-iris)

## Requirements
- Python 3.10+
- Linux only (Kali or Ubuntu recommended)
- Must be run with sudo (scapy requires raw socket access)

```bash
pip install scapy tabulate
```

## Setup
1. Clone the repo.

```bash
git clone https://github.com/ARGUSFramework/argus-recon.git
cd argus-recon
```

2. Download the OUI database.

```bash
wget -O oui.txt https://www.wireshark.org/download/automated/data/manuf
```

3. Copy config.example.json to config.json and edit values.

```bash
cp config.example.json config.json
```

- interface: your network interface (find with the command below)

```bash
ip a
```

- gateway_ip: your gateway (find with the command below)

```bash
ip route
```

- subnet: your subnet in CIDR notation (e.g. 192.168.1.0/24)
- db_path: path to shared argus.db (default: ../argus.db)

## Usage
- Single scan:

```bash
sudo python main.py
```

- Continuous rescan every 60 seconds:

```bash
sudo python main.py --rescan
```

- Populate test data without a live scan:

```bash
sudo python seed_db.py
```

## Output
- CLI table with columns: IP Address | MAC Address | Vendor | First Seen | Last Seen
- Data persisted to SQLite at db_path

## Authorization Notice

> WARNING
>
> This tool sends ARP packets across the network. Only run it
> on networks you own or have explicit written permission to test.
> Unauthorized use may violate computer misuse laws.

## File Structure
- main.py: CLI entry point for scan, enrich, store, and table display
- scanner.py: ARP network scanner using scapy srp
- vendor_lookup.py: Wireshark manuf parser and MAC vendor resolver
- db.py: SQLite initialization, upsert, and device retrieval helpers
- models.py: Device dataclass used across the module
- seed_db.py: Utility to insert sample devices and print table output
- config.json: Active runtime configuration for interface, subnet, and db path
- config.example.json: Template configuration file for initial setup
- oui.txt: Wireshark OUI/manuf vendor mapping database file
- requirements.txt: Python dependency list for this module

## Database Schema

```text
devices
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  ip          TEXT NOT NULL
  mac         TEXT NOT NULL UNIQUE
  vendor      TEXT
  first_seen  TEXT
  last_seen   TEXT
```

## Part of ARGUS
This module shares argus.db with:
- argus-veil (ARP poisoning / MITM)
- argus-oracle (DNS interception)
- argus-iris (Flask dashboard)

Each is a separate repo under the ARGUSFramework organisation.
