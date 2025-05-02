import requests
import dns.resolver
import re
from typing import Annotated, Dict, List, Set, Union

def search_subdomains(
    domain: Annotated[str, "The domain to find subdomains for"],
    use_apis: Annotated[bool, "Whether to use online services"] = True,
) -> List[str]:
    """
    Searches for subdomains of a given domain using passive techniques.
    
    Args:
        domain: The base domain to find subdomains for
        use_apis: Whether to use online services (can be slower but more comprehensive)
        
    Returns:
        A list of discovered subdomains
    """
    discovered_domains: Set[str] = set()
    
    # Xóa http/https và chỉ lấy tên miền
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]  # remove path if exists
    
    # Thêm dns brute force tìm subdomain phổ biến
    common_subdomains = [
        "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
        "smtp", "secure", "vpn", "m", "shop", "ftp", "api", "admin", "test",
        "dev", "portal", "support", "docs", "gitlab", "status"
    ]
    
    # 1. Kiểm tra subdomain phổ biến bằng DNS
    for sub in common_subdomains:
        subdomain = f"{sub}.{domain}"
        try:
            dns.resolver.resolve(subdomain, 'A')
            discovered_domains.add(subdomain)
        except:
            pass  # Subdomain không tồn tại hoặc không thể truy vấn
    
    # 2. Sử dụng Security Trails API (thêm key nếu có)
    if use_apis:
        try:
            # Gửi yêu cầu tới certspotter
            certspotter_url = f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
            response = requests.get(certspotter_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for cert in data:
                    for dns_name in cert.get("dns_names", []):
                        if dns_name.endswith(f".{domain}") or dns_name == domain:
                            discovered_domains.add(dns_name)
        except Exception as e:
            print(f"Error querying certspotter: {e}")
    
    # 3. Sử dụng truy vấn DNS TXT để tìm SPF records (có thể chứa subdomain)
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                txt_record = txt_string.decode("utf-8")
                # Tìm các mục include trong SPF
                if "include:" in txt_record:
                    spf_includes = re.findall(r'include:([a-zA-Z0-9._-]+)', txt_record)
                    for include in spf_includes:
                        if include.endswith(domain):
                            discovered_domains.add(include)
    except:
        pass  # No TXT records or error querying
    
    # Sắp xếp kết quả
    result = sorted(list(discovered_domains))
    return result