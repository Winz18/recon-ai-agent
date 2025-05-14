import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Union, Annotated
from .tool_decorator import recon_tool

@recon_tool
def scan_ports(
    target: Annotated[str, "Target IP address or hostname to scan"],
    ports: Annotated[Optional[List[int]], "List of specific ports to scan. If None, scans top 100 common ports"] = None,
    timeout: Annotated[float, "Socket connection timeout in seconds"] = 1.0,
    threads: Annotated[int, "Number of threads to use for scanning"] = 10,
    scan_type: Annotated[str, "Type of scan: 'tcp' or 'udp'"] = "tcp"
) -> Dict[int, Dict[str, Union[bool, str]]]:
    """
    Scan ports on a target host using basic socket connections.
    
    Args:
        target: IP address or hostname to scan
        ports: List of port numbers to scan. If None, scans top 100 common ports
        timeout: Socket connection timeout in seconds
        threads: Number of threads for concurrent scanning
        scan_type: Type of scan ('tcp' or 'udp')
        
    Returns:
        Dictionary with port numbers as keys and dictionaries as values containing:
        - 'open': Boolean indicating if the port is open
        - 'service': String indicating the likely service (if known)
    """
    # Default to top 100 common ports if not specified
    if ports is None:
        ports = get_top_ports(100)
    
    results = {}
    scan_lock = threading.Lock()
    
    # Resolve the hostname to IP address
    try:
        ip_address = socket.gethostbyname(target)
    except socket.gaierror:
        return {"error": f"Could not resolve hostname: {target}"}
    
    def scan_port(port):
        try:
            # Choose socket type based on scan_type
            if scan_type.lower() == "tcp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif scan_type.lower() == "udp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                return  # Invalid scan type
                
            sock.settimeout(timeout)
            
            # For TCP, check if can connect
            if scan_type.lower() == "tcp":
                result = sock.connect_ex((ip_address, port))
                is_open = (result == 0)
            # For UDP, send a packet and check for response or error
            else:
                sock.sendto(b'', (ip_address, port))
                try:
                    sock.recvfrom(1024)
                    is_open = True
                except socket.timeout:
                    # UDP is tricky - no response could mean filtered or closed
                    # For simplicity, we'll assume it might be open/filtered
                    is_open = True
                except:
                    is_open = False
            
            sock.close()
            
            if is_open:
                # Try to identify the service
                service = get_service_name(port)
                
                with scan_lock:
                    results[port] = {
                        "open": True,
                        "service": service
                    }
        except Exception as e:
            with scan_lock:
                results[port] = {
                    "open": False,
                    "error": str(e)
                }
    
    # Scan ports in parallel using thread pool
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(scan_port, ports)
    
    # Return only open ports
    return {k: v for k, v in results.items() if v.get("open", False)}

def get_service_name(port: int) -> str:
    """
    Get the service name for a port number from the system database if available.
    
    Args:
        port: Port number
        
    Returns:
        Service name or 'unknown'
    """
    try:
        return socket.getservbyport(port)
    except (socket.error, OSError):
        # Common services not in system database
        common_ports = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            3306: "MySQL",
            3389: "RDP",
            8080: "HTTP-Proxy",
            8443: "HTTPS-Alt"
        }
        return common_ports.get(port, "unknown")

def get_top_ports(count: int = 100) -> List[int]:
    """
    Returns a list of top common ports to scan.
    
    Args:
        count: Number of top ports to return (max 1000)
        
    Returns:
        List of port numbers
    """
    # Top 100 common ports - based on nmap's common port list
    top_ports = [
        21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
        143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080,
        81, 85, 88, 8081, 8000, 8008, 8443, 8888, 9100, 9999,
        1025, 1028, 1030, 1720, 2000, 2001, 5060, 8083, 6001, 8002,
        3001, 3128, 5000, 5432, 27017, 10000, 5800, 5631, 631, 8082,
        6000, 7000, 7001, 7002, 8009, 8010, 8031, 8889, 9000, 9001,
        9090, 9091, 9200, 9300, 50000, 49152, 49153, 49154, 49155, 49156,
        102, 107, 109, 115, 123, 513, 514, 587, 1080, 1433,
        1434, 2049, 2082, 2083, 2086, 2087, 2095, 2096, 3000, 5357,
        5631, 5666, 5800, 5901, 6379, 6665, 6666, 6667, 6668, 6669
    ]
    return top_ports[:count]
