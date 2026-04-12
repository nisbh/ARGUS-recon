# Requires root privileges (sudo) — scapy needs raw socket access
from scapy.all import DNS, DNSQR, IP, NBNSQueryRequest, NBNSQueryResponse, UDP, sr1


def mdns_lookup(ip: str, timeout: float = 2.0) -> str:
    try:
        name = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
        packet = (
            IP(dst="224.0.0.251")
            / UDP(dport=5353)
            / DNS(rd=0, qd=DNSQR(qname=name, qtype="PTR"))
        )
        response = sr1(packet, timeout=timeout, verbose=0)

        if response is None or not response.haslayer(DNS):
            return ""

        dns_layer = response.getlayer(DNS)
        if dns_layer is None or dns_layer.ancount <= 0 or dns_layer.an is None:
            return ""

        first_answer = dns_layer.an
        rdata = getattr(first_answer, "rdata", b"")

        if isinstance(rdata, bytes):
            return rdata.decode(errors="ignore").rstrip(".")

        return str(rdata).rstrip(".")
    except Exception:
        return ""


def netbios_lookup(ip: str, timeout: float = 1.0) -> str:
    try:
        packet = (
            IP(dst=ip)
            / UDP(dport=137)
            / NBNSQueryRequest(
                SUFFIX="file server service",
                QUESTION_NAME="*",
                QUESTION_TYPE="NBSTAT",
            )
        )
        response = sr1(packet, timeout=timeout, verbose=0)

        if response is None or not response.haslayer(NBNSQueryResponse):
            return ""

        nbns_layer = response.getlayer(NBNSQueryResponse)
        if nbns_layer is None:
            return ""

        # Assumption: NBNSQueryResponse.RR_NAME is treated as the first returned name entry.
        raw_name = getattr(nbns_layer, "RR_NAME", b"")

        if isinstance(raw_name, bytes):
            return raw_name.decode(errors="ignore").strip()

        return str(raw_name).strip()
    except Exception:
        return ""
