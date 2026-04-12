# Requires root privileges (sudo) — scapy needs raw socket access
from scapy.all import ICMP, IP, sr1


def guess_os(ip: str, timeout: float = 1.0) -> str:
    try:
        packet = IP(dst=ip) / ICMP()
        response = sr1(packet, timeout=timeout, verbose=0)
        if response is None:
            return "Unknown"

        ttl = response[IP].ttl

        if 113 <= ttl <= 128:
            return "Windows"
        if 49 <= ttl <= 64:
            return "Linux / macOS / Android / iOS"
        if 240 <= ttl <= 255:
            return "Network Device (router/switch)"
        if 17 <= ttl <= 32:
            return "Windows (older)"

        return f"Unknown (TTL={ttl})"
    except Exception:
        return "Unknown"
