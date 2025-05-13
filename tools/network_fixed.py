import socket
import whois
from typing import Annotated, Dict, List, Union, Any
from .tool_decorator import recon_tool

# --- DNS Lookup Tool ---
@recon_tool
def dns_lookup(
    domain: Annotated[str, "The domain name to lookup."],
    record_types: Annotated[List[str], "Specific record types to lookup"] = None,
    timeout: Annotated[int, "Timeout for DNS queries in seconds"] = 5,
    nameserver: Annotated[str, "Custom nameserver to use"] = None
) -> Dict[str, List[str]]:
    """
    Performs DNS lookups for a given domain with customizable record types.
    
    Args:
        domain: The domain name to lookup.
        record_types: Specific record types to lookup (A, AAAA, MX, NS, TXT, CNAME, SOA, etc).
                      If None, will lookup A, AAAA, MX, NS, TXT records.
        timeout: Timeout for DNS queries in seconds.
        nameserver: Custom nameserver to use for lookups.
        
    Returns:
        A dictionary with record types as keys and lists of records as values.
    """
    # Default record types to query if not specified
    default_record_types = ["A", "AAAA", "MX", "NS", "TXT"]
    record_types_to_query = record_types or default_record_types
    
    # Convert to uppercase for consistency
    record_types_to_query = [r.upper() for r in record_types_to_query]
    
    # Initialize results dictionary
    results = {r: [] for r in record_types_to_query}
    
    try:
        import dns.resolver
        from dns.exception import DNSException

        # Setup resolver
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        
        # Use custom nameserver if provided
        if nameserver:
            resolver.nameservers = [nameserver]

        # Query each record type
        for record_type in record_types_to_query:
            try:
                answers = resolver.resolve(domain, record_type)
                
                # Format the results based on record type
                if record_type == "A" or record_type == "AAAA":
                    results[record_type] = [r.address for r in answers]
                elif record_type == "MX":
                    results[record_type] = sorted([f"{r.preference} {r.exchange}" for r in answers])
                elif record_type == "NS" or record_type == "CNAME" or record_type == "PTR":
                    results[record_type] = sorted([str(r.target) for r in answers])
                elif record_type == "TXT":
                    txt_records = []
                    for rdata in answers:
                        txt_records.extend([txt.decode('utf-8', errors='replace') for txt in rdata.strings])
                    results[record_type] = txt_records
                elif record_type == "SOA":
                    results[record_type] = []
                    for rdata in answers:
                        results[record_type].append(f"mname={rdata.mname} rname={rdata.rname} serial={rdata.serial} refresh={rdata.refresh} retry={rdata.retry} expire={rdata.expire} minimum={rdata.minimum}")
                elif record_type == "CAA":
                    results[record_type] = [f"flags={r.flags} tag={r.tag} value={r.value}" for r in answers]
                else:
                    # Generic handling for other record types
                    results[record_type] = [str(r) for r in answers]
            except dns.resolver.NoAnswer:
                # No records of this type
                pass
            except dns.resolver.NXDOMAIN:
                # Domain doesn't exist
                return {"error": f"Domain {domain} does not exist."}
            except dns.resolver.NoNameservers:
                results[f"{record_type}_error"] = "No nameservers available for this query"
            except DNSException as e:
                results[f"{record_type}_error"] = f"DNS query error: {str(e)}"

    except ImportError:
        return {"error": "dnspython library is required for DNS lookups"}
    except Exception as e:
        return {"error": f"DNS lookup failed: {str(e)}"}

    # Remove empty record types
    return {k: v for k, v in results.items() if v and not k.endswith('_error')}

# --- WHOIS Lookup Tool ---
@recon_tool
def whois_lookup(
    domain: Annotated[str, "The domain name to perform WHOIS lookup."],
    server: Annotated[str, "Custom WHOIS server to use"] = None,
    timeout: Annotated[int, "Timeout for WHOIS query in seconds"] = 10,
    format_output: Annotated[bool, "Return formatted output as dict instead of raw text"] = False
) -> Union[str, Dict[str, Any]]:
    """
    Performs a WHOIS lookup for the given domain.
    
    Args:
        domain: The domain name to perform WHOIS lookup.
        server: Custom WHOIS server to use (e.g., "whois.verisign-grs.com" for .com domains)
        timeout: Timeout for WHOIS query in seconds
        format_output: Return formatted output as dict instead of raw text
        
    Returns:
        The raw WHOIS information as a string or formatted as a dictionary if format_output=True.
    """
    try:
        import whois
        from socket import timeout as socket_timeout
        
        # Special case for .vn domains
        vn_domain = domain.endswith('.vn')
        
        try:
            # Try standard whois library
            w = None
            try:
                # Some versions of python-whois don't support server parameter
                if server:
                    try:
                        w = whois.whois(domain, server=server)
                    except (TypeError, Exception):
                        # Fallback if server param not supported
                        w = whois.whois(domain)
                else:
                    w = whois.whois(domain)
            except Exception as e:
                if "server" in str(e):
                    # Try without server parameter if that was the issue
                    w = whois.whois(domain)
                else:
                    raise
            
            # If we have a valid result
            if w:
                # Handle formatted output
                if format_output and hasattr(w, 'domain_name'):
                    # Format the output as a clean dictionary
                    result = {}
                    for key in ['domain_name', 'registrar', 'whois_server', 'creation_date', 
                                'expiration_date', 'updated_date', 'name_servers', 'status',
                                'emails', 'dnssec', 'registrant', 'admin', 'tech']:
                        if hasattr(w, key) and getattr(w, key):
                            result[key] = getattr(w, key)
                    return result
                
                # Otherwise return raw text
                if hasattr(w, 'text') and w.text:
                    return str(w.text)
                    
                # If no text attribute but we have a structured response
                if hasattr(w, 'domain_name'):
                    return str(w)
        
        except socket_timeout:
            return {"error": f"WHOIS lookup timed out after {timeout} seconds"}
        
        except Exception as e:
            # Handle .vn domains separately if needed
            if vn_domain:
                try:
                    # Try specialized module for .vn domains if available
                    try:
                        from pythonwhois import get_whois
                        result = get_whois(domain, server="whois.vn")
                        if result and 'raw' in result:
                            return '\n'.join(result['raw'])
                    except ImportError:
                        return {"error": "pythonwhois library is required for .vn WHOIS lookup"}
                    except Exception as nested_e:
                        return {"error": f"WHOIS lookup for .vn domain failed: {str(nested_e)}"}
                except Exception as vn_e:
                    return {"error": f"WHOIS lookup for .vn domain failed: {str(vn_e)}"}
            
            return {"error": f"WHOIS lookup failed: {str(e)}"}
            
        return "WHOIS information not available"
        
    except ImportError:
        return {"error": "python-whois library is required for WHOIS lookup"}
    except Exception as e:
        return {"error": f"WHOIS lookup error: {str(e)}"}
