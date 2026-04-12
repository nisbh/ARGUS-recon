import ipaddress

from scapy.all import ARP, Ether, srp

from models import Device


def scan_network(interface: str, subnet: str) -> list[Device]:
    ipaddress.ip_network(subnet, strict=False)
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)

    # NOTE: srp() requires root privileges. Run with sudo.
    answered, _ = srp(packet, iface=interface, timeout=2, verbose=0)

    devices = []
    for _, received in answered:
        ip = received.psrc
        mac = received.hwsrc.lower()
        devices.append(Device(ip=ip, mac=mac))

    return devices