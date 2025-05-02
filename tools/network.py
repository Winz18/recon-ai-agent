import socket
import whois
from typing import Annotated, Dict, List

# --- DNS Lookup Tool ---
def dns_lookup(domain: Annotated[str, "The domain name to lookup."]) -> Dict[str, List[str]]:
    """
    Performs DNS lookups (A, AAAA, MX, NS, TXT records) for a given domain.
    Returns a dictionary with record types as keys and lists of records as values.
    """
    results = {"A": [], "AAAA": [], "MX": [], "NS": [], "TXT": []}
    try:
        # A records
        results["A"] = [ip[4][0] for ip in socket.getaddrinfo(domain, None, socket.AF_INET)]
    except socket.gaierror:
        pass # Ignore if no IPv4 records found
    except Exception as e:
        print(f"[Tool Error - dns_lookup A] {domain}: {e}")

    try:
        # AAAA records
        results["AAAA"] = [ip[4][0] for ip in socket.getaddrinfo(domain, None, socket.AF_INET6)]
    except socket.gaierror:
        pass # Ignore if no IPv6 records found
    except Exception as e:
        print(f"[Tool Error - dns_lookup AAAA] {domain}: {e}")

    # Lưu ý: Các record khác (MX, NS, TXT) cần thư viện như dnspython
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        for record_type in ["MX", "NS", "TXT"]:
            try:
                answers = resolver.resolve(domain, record_type)
                if record_type == "MX":
                    results[record_type] = sorted([f"{r.preference} {r.exchange}" for r in answers])
                elif record_type == "TXT":
                     # Decode TXT records and join multi-string records
                    records = []
                    for rdata in answers:
                        records.extend([txt.decode('utf-8', errors='replace') for txt in rdata.strings])
                    results[record_type] = records
                else: # NS
                    results[record_type] = sorted([str(r.target) for r in answers])
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
                pass # Ignore if no records of this type or domain doesn't exist
            except Exception as e_inner:
                 print(f"[Tool Error - dns_lookup {record_type}] {domain}: {e_inner}")

    except ImportError:
        print("[Tool Warning] dnspython not installed. Skipping MX, NS, TXT lookups.")
    except Exception as e_outer:
        print(f"[Tool Error - dns_lookup outer] {domain}: {e_outer}")


    # Trả về kết quả, loại bỏ các list rỗng để gọn gàng
    return {k: v for k, v in results.items() if v}

# --- WHOIS Lookup Tool ---
def whois_lookup(domain: Annotated[str, "The domain name to perform WHOIS lookup."]) -> str:
    """
    Performs a WHOIS lookup for the given domain.
    Returns the raw WHOIS information as a string.
    """
    try:
        w = whois.whois(domain)
        # Kiểm tra xem có trả về thông tin không (một số TLD có thể không có)
        if w and w.text:
             # Lấy thông tin dưới dạng text
             # Đôi khi w.text là list, cần join lại
            if isinstance(w.text, list):
                return "\n".join(w.text)
            return w.text
        else:
            return f"No WHOIS information found or available for {domain} via python-whois."
    except Exception as e:
        return f"Error during WHOIS lookup for {domain}: {e}"