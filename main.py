# main.py
import sys
import os
import argparse
import json
import logging
from typing import Dict, List, Optional, Union
from colorama import init, Fore, Style
from termcolor import colored

# Initialize colorama for Windows support
init()

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import config
from config import settings
from utils.logging_setup import setup_logging, get_logger

# Cài đặt logging
logger = setup_logging()

def print_banner():
    """Print a colorful banner for the application."""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     █▀█ █▀▀ █▀▀ █▀█ █▄░█   ▄▀█ █ ▄▄ ▄▀█ █▀▀ █▀▀ █▄░█ ▀█▀        ║
    ║     █▀▄ ██▄ █▄▄ █▄█ █░▀█   █▀█ █ ░░ █▀█ █▄█ ██▄ █░▀█ ░█░        ║
    ║                                                                  ║
    ║     AI-Powered Reconnaissance for Network Security Testing       ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(colored(banner, 'cyan'))

def print_section(title):
    """Print a section title with styling."""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}=== {title} ==={Style.RESET_ALL}\n")

def print_success(message):
    """Print a success message with styling."""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message with styling."""
    print(f"{Fore.RED}{Style.BRIGHT}ERROR: {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an info message with styling."""
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def print_warning(message):
    """Print a warning message with styling."""
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def parse_port_range(port_range_str):
    """Parse port range string into a list of ports."""
    if not port_range_str:
        return None
    
    ports = []
    ranges = port_range_str.split(',')
    for r in ranges:
        if '-' in r:
            start, end = map(int, r.split('-'))
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(r))
    return ports

def main():
    """
    Entry point for reconnaissance workflows.
    Parses command line arguments and runs the selected workflow.
    """
    print_banner()
    
    parser = argparse.ArgumentParser(
        description='AI-powered Reconnaissance for Network Security Testing',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic settings
    basic_group = parser.add_argument_group('Basic Settings')
    basic_group.add_argument('-d', '--domain', type=str, default=settings.DEFAULT_TARGET_DOMAIN,
                      help=f'Target domain to analyze')
    basic_group.add_argument('-m', '--model', type=str, default="gemini-2.5-pro-preview-05-06",
                      help='Google Vertex AI model ID to use')
    basic_group.add_argument('-w', '--workflow', type=str, choices=["standard", "quick", "deep"], default="standard",
                      help='Workflow to run')
    basic_group.add_argument('-o', '--output', type=str, choices=["markdown", "html", "json"], default="markdown",
                      help='Output format for the report')
    basic_group.add_argument('--no-save', action='store_true',
                      help='Do not save the report to a file')
    basic_group.add_argument('--no-raw-data', action='store_true',
                      help='Do not save raw data to a file')
    
    # Tool groups - enable/disable specific tool sets
    tools_group = parser.add_argument_group('Tool Groups')
    tools_group.add_argument('--enable-dns', action='store_true', default=True,
                      help='Enable DNS reconnaissance')
    tools_group.add_argument('--disable-dns', action='store_true',
                      help='Disable DNS reconnaissance')
    tools_group.add_argument('--enable-whois', action='store_true', default=True,
                      help='Enable WHOIS reconnaissance')
    tools_group.add_argument('--disable-whois', action='store_true',
                      help='Disable WHOIS reconnaissance')
    tools_group.add_argument('--enable-headers', action='store_true', default=True,
                      help='Enable HTTP headers scanning')
    tools_group.add_argument('--disable-headers', action='store_true',
                      help='Disable HTTP headers scanning')
    tools_group.add_argument('--enable-subdomains', action='store_true', default=True,
                      help='Enable subdomain enumeration')
    tools_group.add_argument('--disable-subdomains', action='store_true',
                      help='Disable subdomain enumeration')
    tools_group.add_argument('--enable-ports', action='store_true', default=True,
                      help='Enable port scanning')
    tools_group.add_argument('--disable-ports', action='store_true',
                      help='Disable port scanning')
    tools_group.add_argument('--enable-osint', action='store_true', default=True,
                      help='Enable OSINT gathering')
    tools_group.add_argument('--disable-osint', action='store_true',
                      help='Disable OSINT gathering')
    tools_group.add_argument('--enable-tech', action='store_true', default=True,
                      help='Enable technology detection')
    tools_group.add_argument('--disable-tech', action='store_true',
                      help='Disable technology detection')
    tools_group.add_argument('--enable-screenshot', action='store_true', default=True,
                      help='Enable website screenshots')
    tools_group.add_argument('--disable-screenshot', action='store_true',
                      help='Disable website screenshots')
    
    # Tool-specific parameters for port scanning
    port_group = parser.add_argument_group('Port Scanning Options')
    port_group.add_argument('--ports', type=str,
                      help='Ports to scan (e.g., "80,443,8080" or "20-25,80,443-445")')
    port_group.add_argument('--port-timeout', type=float, default=1.0,
                      help='Timeout for port scanning in seconds')
    port_group.add_argument('--port-threads', type=int, default=10,
                      help='Number of threads for port scanning')
    port_group.add_argument('--port-scan-type', type=str, choices=['tcp', 'udp'], default='tcp',
                      help='Type of port scan: tcp or udp')
    
    # Subdomain enumeration parameters
    subdomain_group = parser.add_argument_group('Subdomain Enumeration Options')
    subdomain_group.add_argument('--use-apis', action='store_true', default=True,
                      help='Use external APIs for subdomain enumeration')
    subdomain_group.add_argument('--max-subdomains', type=int, default=100,
                      help='Maximum number of subdomains to retrieve')
    
    # HTTP options
    http_group = parser.add_argument_group('HTTP Options')
    http_group.add_argument('--http-timeout', type=float, default=10.0,
                      help='Timeout for HTTP requests in seconds')
    http_group.add_argument('--user-agent', type=str,
                      help='Custom User-Agent for HTTP requests')
    
    # Google dorking options
    osint_group = parser.add_argument_group('OSINT Options')
    osint_group.add_argument('--dorks-limit', type=int, default=10,
                      help='Maximum number of Google dork results to retrieve')
    
    args = parser.parse_args()
    
    # Process the arguments - resolve any conflicts with explicit disable flags
    if args.disable_dns:
        args.enable_dns = False
    if args.disable_whois:
        args.enable_whois = False
    if args.disable_headers:
        args.enable_headers = False
    if args.disable_subdomains:
        args.enable_subdomains = False
    if args.disable_ports:
        args.enable_ports = False
    if args.disable_osint:
        args.enable_osint = False
    if args.disable_tech:
        args.enable_tech = False
    if args.disable_screenshot:
        args.enable_screenshot = False
    
    # Parse port range if provided
    port_list = parse_port_range(args.ports) if args.ports else None
    
    # Display the configuration
    print_section("CONFIGURATION")
    print_info(f"Target Domain: {args.domain}")
    print_info(f"Workflow: {args.workflow}")
    print_info(f"Output Format: {args.output}")
    print_info(f"Save Report: {not args.no_save}")
    print_info(f"Save Raw Data: {not args.no_raw_data}")
    
    print_section("ENABLED TOOLS")
    if args.enable_dns:
        print_info("✓ DNS Reconnaissance")
    if args.enable_whois:
        print_info("✓ WHOIS Lookup")
    if args.enable_headers:
        print_info("✓ HTTP Headers Analysis")
    if args.enable_subdomains:
        print_info("✓ Subdomain Enumeration")
    if args.enable_ports:
        print_info("✓ Port Scanning")
        if port_list:
            print_info(f"  └─ Custom ports: {args.ports}")
        print_info(f"  └─ Scan type: {args.port_scan_type.upper()}")
    if args.enable_osint:
        print_info("✓ OSINT Gathering (Google Dorking)")
    if args.enable_tech:
        print_info("✓ Technology Detection")
    if args.enable_screenshot:
        print_info("✓ Website Screenshots")
    
    print_section(f"STARTING RECONNAISSANCE ON {args.domain}")
    logger.info(f"Starting '{args.workflow}' reconnaissance workflow for: {args.domain}")
    
    # Select and run the appropriate workflow based on user choice
    if args.workflow in ["standard", "quick", "deep"]:
        try:
            # Import the standard workflow
            from workflows.standard_recon_workflow import run_standard_recon_workflow
            
            # Create tool configuration based on user parameters
            tool_config = {
                "enable_dns": args.enable_dns,
                "enable_whois": args.enable_whois,
                "enable_headers": args.enable_headers,
                "enable_subdomains": args.enable_subdomains,
                "enable_ports": args.enable_ports,
                "enable_osint": args.enable_osint,
                "enable_tech": args.enable_tech,
                "enable_screenshot": args.enable_screenshot,
                
                # Tool-specific parameters
                "port_list": port_list,
                "port_timeout": args.port_timeout,
                "port_threads": args.port_threads,
                "port_scan_type": args.port_scan_type,
                
                "use_subdomain_apis": args.use_apis,
                "max_subdomains": args.max_subdomains,
                
                "http_timeout": args.http_timeout,
                "user_agent": args.user_agent,
                
                "dorks_limit": args.dorks_limit,
                
                # Workflow intensity - adjust parameters based on workflow type
                "workflow_type": args.workflow
            }
            
            # Run the standard workflow with the specified parameters
            report, report_path = run_standard_recon_workflow(
                target_domain=args.domain, 
                model_id=args.model,
                output_format=args.output,
                save_report=not args.no_save,
                save_raw_data=not args.no_raw_data,
                tool_config=tool_config
            )
            
            # Print a summary of the report
            print_section("RECONNAISSANCE REPORT SUMMARY")
            print_info(f"Target: {args.domain}")
            
            # For JSON output, format it nicely
            if args.output == "json":
                try:
                    json_obj = json.loads(report)
                    if "executive_summary" in json_obj:
                        print_success(f"\nExecutive Summary: {json_obj['executive_summary'].get('overview', 'No summary available.')}")
                        
                        risk_level = json_obj['executive_summary'].get('risk_level', 'Unknown')
                        if risk_level.lower() in ['critical', 'high']:
                            print_error(f"Risk Level: {risk_level}")
                        elif risk_level.lower() == 'medium':
                            print_warning(f"Risk Level: {risk_level}")
                        else:
                            print_success(f"Risk Level: {risk_level}")
                            
                        key_findings = json_obj['executive_summary'].get('key_findings_count', {})
                        if key_findings:
                            print_info("\nKey Findings:")
                            if key_findings.get('critical', 0) > 0:
                                print_error(f"  Critical: {key_findings.get('critical', 0)}")
                            if key_findings.get('high', 0) > 0:
                                print_error(f"  High: {key_findings.get('high', 0)}")
                            if key_findings.get('medium', 0) > 0:
                                print_warning(f"  Medium: {key_findings.get('medium', 0)}")
                            if key_findings.get('low', 0) > 0:
                                print_success(f"  Low: {key_findings.get('low', 0)}")
                except (json.JSONDecodeError, AttributeError, TypeError):
                    print(f"\n{report[:500]}...")
            else:
                # For other formats, just print a preview
                print(f"\n{report[:500]}...")
                
            if report_path:
                print_success(f"\nFull report saved to: {report_path}")
                
        except ImportError as e:
            logger.error(f"Failed to import standard workflow: {e}")
            print_error(f"Could not load the {args.workflow} workflow. {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error during workflow execution: {e}")
            print_error(f"The workflow failed with error: {e}")
            sys.exit(1)
    
    # Add additional workflow options here in the future
    # elif args.workflow == "another_workflow":
    #     ...
    
    logger.info(f"Finished '{args.workflow}' reconnaissance workflow")
    print_success(f"\nReconnaissance workflow completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
