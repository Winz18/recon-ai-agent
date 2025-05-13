import requests
import dns.resolver
import re
import concurrent.futures
from typing import Annotated, Dict, List, Set, Union, Any
from .tool_decorator import recon_tool

@recon_tool
def search_subdomains(
    domain: Annotated[str, "The domain to find subdomains for"],
    use_apis: Annotated[bool, "Whether to use online services"] = True,
    custom_wordlist: Annotated[List[str], "Custom subdomain wordlist to try"] = None,
    max_threads: Annotated[int, "Maximum number of concurrent DNS lookups"] = 10,
    timeout: Annotated[int, "DNS lookup timeout in seconds"] = 3
) -> Union[List[str], Dict[str, Any]]:
    """
    Searches for subdomains of a given domain using passive techniques.
    
    Args:
        domain: The base domain to find subdomains for
        use_apis: Whether to use online services (can be slower but more comprehensive)
        custom_wordlist: Custom subdomain wordlist to try in addition to common ones
        max_threads: Maximum number of concurrent DNS lookups
        timeout: DNS lookup timeout in seconds
        
    Returns:
        A list of discovered subdomains or an error dictionary
    """
    discovered_domains: Set[str] = set()
    
    # Clean up domain input
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]  # remove path if exists
    
    # Default common subdomains to check
    common_subdomains = [
        "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
        "smtp", "secure", "vpn", "m", "shop", "ftp", "api", "admin", "test",
        "dev", "portal", "support", "docs", "gitlab", "status", "cdn", "cloud",
        "images", "img", "download", "downloads", "app", "apps", "staging", 
        "auth", "cp", "cpanel", "wap", "mobile", "dashboard", "media", "video",
        "email", "autodiscover", "autoconfig", "dns", "direct", "direct-connect",
        "events", "login", "intranet", "connect", "ws", "web"
    ]
    
    # Merge with custom wordlist if provided
    if custom_wordlist:
        common_subdomains.extend(custom_wordlist)
    
    def check_subdomain(sub):
        """Helper function to check if a subdomain exists via DNS"""
        subdomain = f"{sub}.{domain}"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout
            # Try to resolve the domain
            resolver.resolve(subdomain, 'A')
            return subdomain
        except dns.resolver.NXDOMAIN:
            # Domain doesn't exist
            return None
        except dns.resolver.NoAnswer:
            # Try AAAA record before deciding it doesn't exist
            try:
                resolver.resolve(subdomain, 'AAAA')
                return subdomain
            except:
                return None
        except Exception:
            return None
    
    # 1. Check subdomain brute-force with threading to speed up lookups
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_subdomain = {executor.submit(check_subdomain, sub): sub for sub in common_subdomains}
        for future in concurrent.futures.as_completed(future_to_subdomain):
            result = future.result()
            if result:
                discovered_domains.add(result)
    
    # 2. Use API methods for finding subdomains
    if use_apis:
        try:
            # CertSpotter API - good for finding subdomains via certificate transparency logs
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
            
        try:
            # VirusTotal API (requires API key for better results)
            # Using the free endpoint without API key, which is limited
            vt_url = f"https://www.virustotal.com/api/v3/domains/{domain}/subdomains"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # Note: Without an API key, this might not work well
            response = requests.get(vt_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for item in data.get('data', []):
                        if 'id' in item:
                            discovered_domains.add(item['id'])
        except Exception as e:
            # Just silently ignore VirusTotal errors, as it might not work without an API key
            pass
    
    # 3. Look for SPF/DMARC records that might contain subdomains
    try:
        # Check TXT records for SPF
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        answers = resolver.resolve(domain, 'TXT')
        
        for rdata in answers:
            for txt_string in rdata.strings:
                txt_record = txt_string.decode("utf-8", errors='ignore')
                # Find all include:domain.com entries in SPF records
                if "include:" in txt_record or "include :" in txt_record:
                    spf_includes = re.findall(r'include:([a-zA-Z0-9._-]+)', txt_record)
                    spf_includes.extend(re.findall(r'include :([a-zA-Z0-9._-]+)', txt_record))
                    for include in spf_includes:
                        if include.endswith(domain):
                            discovered_domains.add(include)
        
        # Check for DMARC record which might contain reporting destinations
        try:
            dmarc_domain = f"_dmarc.{domain}"
            dmarc_answers = resolver.resolve(dmarc_domain, 'TXT')
            for rdata in dmarc_answers:
                for txt_string in rdata.strings:
                    txt_record = txt_string.decode("utf-8", errors='ignore')
                    # Look for rua or ruf entries
                    rua_matches = re.findall(r'rua=mailto:([^@]+@([a-zA-Z0-9.-]+))', txt_record)
                    ruf_matches = re.findall(r'ruf=mailto:([^@]+@([a-zA-Z0-9.-]+))', txt_record)
                    
                    for _, domain_part in rua_matches + ruf_matches:
                        if domain_part.endswith(domain):
                            discovered_domains.add(domain_part)
        except Exception:
            # DMARC record might not exist
            pass
            
    except Exception as e:
        # TXT records might not exist
        pass
    
    # Remove the main domain if it's in the list
    if domain in discovered_domains:
        discovered_domains.remove(domain)
    
    result = sorted(list(discovered_domains))
    if not result:
        return {"message": f"No subdomains found for {domain} using available methods."}
    return result

@recon_tool
def related_domains_search(
    domain: Annotated[str, "The base domain to find related domains for"],
    patterns: Annotated[List[str], "Patterns to try (e.g., ['{keyword}-cdn', '{keyword}-api'])"] = None,
    keywords: Annotated[List[str], "Additional keywords to extract from the domain"] = None,
    tlds: Annotated[List[str], "TLDs to check (e.g., ['com', 'net', 'org'])"] = None,
    check_existence: Annotated[bool, "Verify domain existence via DNS"] = True
) -> Union[List[str], Dict[str, Any]]:
    """
    Searches for domains related to the given domain based on patterns, keywords, and TLDs.
    
    Args:
        domain: The base domain to find related domains for
        patterns: Pattern templates using {keyword} as placeholder
        keywords: Additional keywords to extract from the domain
        tlds: List of TLDs to check with the base domain name
        check_existence: Whether to verify domain existence via DNS lookup
        
    Returns:
        A list of potentially related domains
    """
    if not domain:
        return {"error": "Domain parameter is required"}
    
    # Clean up domain input
    base_domain = re.sub(r'^https?://', '', domain)
    base_domain = base_domain.split('/')[0]  # remove path if exists
    
    # Extract the domain parts
    parts = base_domain.split('.')
    if len(parts) < 2:
        return {"error": "Invalid domain format"}
    
    # Get the main domain name without TLD
    main_name = parts[-2]
    current_tld = parts[-1]
    
    # Initialize the related domains set
    related_domains = set()
    
    # 1. Generate domains with different TLDs
    default_tlds = ["com", "net", "org", "io", "app", "dev", "co", "me", "info", "biz"]
    tld_list = tlds or default_tlds
    
    for tld in tld_list:
        if tld != current_tld:
            related_domain = f"{main_name}.{tld}"
            related_domains.add(related_domain)
    
    # 2. Generate domains based on patterns
    default_patterns = [
        "{keyword}-cdn", 
        "{keyword}-api", 
        "{keyword}-app",
        "{keyword}-dev", 
        "{keyword}-staging", 
        "{keyword}-prod",
        "{keyword}-test",
        "{keyword}cdn", 
        "{keyword}api", 
        "{keyword}app",
        "cdn-{keyword}", 
        "api-{keyword}", 
        "app-{keyword}",
        "dev-{keyword}", 
        "staging-{keyword}", 
        "prod-{keyword}",
        "test-{keyword}"
    ]
    
    pattern_list = patterns or default_patterns
    
    # Add main domain name as a keyword
    all_keywords = [main_name]
    
    # Add additional keywords if provided
    if keywords:
        all_keywords.extend(keywords)
    
    # Generate additional keywords from the main domain
    # For example, if domain is "example-company":
    # - Split by dash: "example", "company"
    if "-" in main_name:
        all_keywords.extend(main_name.split("-"))
    
    # Generate pattern-based domains
    for keyword in all_keywords:
        for pattern in pattern_list:
            related_name = pattern.replace("{keyword}", keyword)
            for tld in tld_list:
                related_domain = f"{related_name}.{tld}"
                related_domains.add(related_domain)
    
    # Remove the original domain if it's in the list
    if base_domain in related_domains:
        related_domains.remove(base_domain)
    
    # 3. Verify existence of domains via DNS if requested
    if check_existence:
        verified_domains = []
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        
        for domain_to_check in related_domains:
            try:
                # Try to resolve the domain
                resolver.resolve(domain_to_check, 'A')
                verified_domains.append(domain_to_check)
            except:
                try:
                    # Try AAAA record before deciding it doesn't exist
                    resolver.resolve(domain_to_check, 'AAAA')
                    verified_domains.append(domain_to_check)
                except:
                    pass  # Domain doesn't exist
        
        result = sorted(verified_domains)
    else:
        result = sorted(list(related_domains))
    
    if not result:
        return {"message": f"No related domains found for {domain} using available methods."}
    
    return result