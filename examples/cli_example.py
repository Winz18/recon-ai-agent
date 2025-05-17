#!/usr/bin/env python3
"""
Example demonstrating the improved CLI interface for the reconnaissance framework.
This shows how to use progress indicators, tables, and other formatting.
"""

import os
import sys
import time
import random
from typing import List, Dict

# Add the project root to the path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import the CLI utility
from utils.cli import cli, set_verbosity

def simulate_port_scan(target: str, ports: List[int]) -> Dict:
    """
    Simulate a port scan with progress indicators.
    
    Args:
        target: Target to scan
        ports: List of ports to scan
        
    Returns:
        Results of the scan
    """
    # Start a progress indicator
    cli.start_progress("port_scan", f"Scanning {len(ports)} ports on {target}")
    
    # Simulate scanning each port
    open_ports = []
    for i, port in enumerate(ports):
        # Sleep to simulate work
        time.sleep(0.1)
        
        # Simulate random findings
        is_open = random.random() > 0.7
        if is_open:
            service = random.choice(['http', 'ssh', 'smtp', 'ftp', 'unknown'])
            open_ports.append({'port': port, 'status': 'open', 'service': service})
            cli.update_progress("port_scan", 1, f"Found open port {port} ({service})")
        else:
            cli.update_progress("port_scan", 1)
    
    # Stop the progress indicator
    cli.stop_progress("port_scan", success=True, message=f"Completed port scan with {len(open_ports)} open ports found")
    
    return {
        'target': target,
        'total_ports_scanned': len(ports),
        'open_ports': open_ports
    }

def simulate_subdomain_enum(domain: str) -> Dict:
    """
    Simulate subdomain enumeration with progress indicators.
    
    Args:
        domain: Domain to enumerate
        
    Returns:
        Results of the enumeration
    """
    # Start a progress indicator
    cli.start_progress("subdomain_enum", f"Enumerating subdomains for {domain}")
    
    # Generate random subdomains
    subdomains = []
    total_to_find = random.randint(5, 15)
    
    common_subdomains = ['www', 'mail', 'admin', 'blog', 'shop', 'api', 'dev', 
                         'test', 'staging', 'app', 'secure', 'vpn', 'cdn', 
                         'docs', 'support', 'forum', 'gitlab', 'jenkins']
    
    for i in range(total_to_find):
        # Sleep to simulate work
        time.sleep(0.2)
        
        # Add a random subdomain
        subdomain = random.choice(common_subdomains) + str(random.randint(1, 100))
        subdomains.append(f"{subdomain}.{domain}")
        
        # Update progress
        cli.update_progress("subdomain_enum", 1, f"Found subdomain: {subdomain}.{domain}")
    
    # Stop the progress indicator
    cli.stop_progress("subdomain_enum", success=True, 
                     message=f"Found {len(subdomains)} subdomains for {domain}")
    
    return {
        'domain': domain,
        'total_found': len(subdomains),
        'subdomains': subdomains
    }

def main():
    """Main function to demonstrate the CLI interface."""
    # Set verbosity level
    set_verbosity(2)  # 0=quiet, 1=normal, 2=verbose, 3=debug
    
    # Display header
    cli.header("CLI DEMONSTRATION")
    cli.subheader("This example shows the improved CLI interface")
    
    # Example of different message types
    cli.info("This is an information message")
    cli.warning("This is a warning message")
    cli.error("This is an error message")
    cli.success("This is a success message")
    cli.verbose("This is a verbose message (only shown in verbose mode)")
    cli.debug("This is a debug message (only shown in debug mode)")
    
    cli.divider()
    
    # Simulate reconnaissance workflow
    target = "example.com"
    cli.subheader(f"Simulating reconnaissance on {target}")
    
    # Simulate port scanning
    cli.info("Starting port scanning")
    ports = list(range(20, 30)) + [80, 443, 8080, 8443]
    port_results = simulate_port_scan(target, ports)
    
    # Display port results in a table
    if port_results['open_ports']:
        cli.display_results_table(
            headers=["Port", "Status", "Service"],
            rows=[[p['port'], p['status'], p['service']] for p in port_results['open_ports']],
            title="Open Ports"
        )
    
    cli.divider()
    
    # Simulate subdomain enumeration
    cli.info("Starting subdomain enumeration")
    subdomains_results = simulate_subdomain_enum(target)
    
    # Display subdomain results in a table
    if subdomains_results['subdomains']:
        # Split into two columns for cleaner display
        rows = []
        subdomains = subdomains_results['subdomains']
        half = len(subdomains) // 2 + len(subdomains) % 2
        for i in range(half):
            row = [subdomains[i]]
            if i + half < len(subdomains):
                row.append(subdomains[i + half])
            else:
                row.append("")
            rows.append(row)
        
        cli.display_results_table(
            headers=["Subdomain", "Subdomain"],
            rows=rows,
            title="Discovered Subdomains"
        )
    
    # Display summary
    findings = {
        "Open Ports": port_results['open_ports'],
        "Subdomains": subdomains_results['subdomains']
    }
    
    cli.display_summary(
        target=target,
        duration=None,  # Automatically calculated from start time
        tasks_completed=2,
        findings=findings
    )

if __name__ == "__main__":
    main() 