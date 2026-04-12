# Requires root privileges (sudo) — scapy needs raw socket access
from scapy.all import ICMP, IP, sr1


def probe_host(ip: str, timeout: float = 1.0) -> bool:
    try:
        packet = IP(dst=ip) / ICMP()
        response = sr1(packet, timeout=timeout, verbose=0)
        return response is not None
    except Exception:
        return False
