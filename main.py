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
from workflows import WORKFLOW_TYPES

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

def print_workflow_help():
    """Print detailed help information about available workflows."""
    print_section("AVAILABLE WORKFLOWS")
    
    workflows = {
        "standard": "Balanced reconnaissance with most tools enabled. Good for general security assessment.",
        "quick": "Fast reconnaissance with limited scope. Good for initial discovery.",
        "deep": "Thorough reconnaissance with all tools enabled and maximum data collection. Takes longer to complete.",
        "targeted": "Focused reconnaissance on specific security aspects. Use with --target-type option.",
        "stealth": "Stealthy reconnaissance using only passive techniques to minimize detection. Avoids active scans.",
        "comprehensive": "Complete reconnaissance using all available tools with parallel execution for faster results."
    }
    
    target_types = {
        "web": "Focus on web application security issues",
        "api": "Focus on API security issues",
        "ssl": "Focus on SSL/TLS security issues",
        "waf": "Focus on WAF detection and analysis",
        "cms": "Focus on CMS detection and security"
    }
    
    for name, desc in workflows.items():
        print(f"{Fore.GREEN}{name}{Style.RESET_ALL}: {desc}")
    
    print()
    print_info("For targeted workflow, specify a target type with --target-type:")
    for name, desc in target_types.items():
        print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}: {desc}")
    
    print()
    print_info("Example commands:")
    print(f"  {Fore.YELLOW}python main.py -d example.com -w standard{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py -d example.com -w quick --disable-ports{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py -d example.com -w targeted --target-type ssl{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py -d example.com -w comprehensive --parallelism 4{Style.RESET_ALL}")

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
    basic_group.add_argument('-w', '--workflow', type=str, 
                      choices=list(WORKFLOW_TYPES.keys()), 
                      default="standard",
                      help='Workflow type to run')
    basic_group.add_argument('-o', '--output', type=str, choices=["markdown", "html", "json"], default="markdown",
                      help='Output format for the report')
    basic_group.add_argument('--no-save', action='store_true',
                      help='Do not save the report to a file')
    basic_group.add_argument('--no-raw-data', action='store_true',
                      help='Do not save raw data to a file')
    basic_group.add_argument('--help-workflows', action='store_true',
                      help='Show detailed information about available workflows and exit')
    
    # Workflow specific settings
    workflow_group = parser.add_argument_group('Workflow Settings')
    workflow_group.add_argument('--target-type', type=str, 
                         choices=["web", "api", "ssl", "waf", "cms"],
                         default="web",
                         help='Target type for targeted workflow')
    workflow_group.add_argument('--parallelism', type=int, default=2,
                         help='Number of parallel tasks for comprehensive workflow')
    workflow_group.add_argument('--delay', type=float, default=2.0,
                         help='Delay between requests for stealth workflow')
    workflow_group.add_argument('--jitter', type=float, default=0.5,
                         help='Random jitter for stealth workflow')
    
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
    tools_group.add_argument('--enable-crawler', action='store_true', default=True,
                      help='Enable endpoint crawling')
    tools_group.add_argument('--disable-crawler', action='store_true',
                      help='Disable endpoint crawling')
    tools_group.add_argument('--enable-ssl', action='store_true', default=True,
                      help='Enable SSL/TLS analysis')
    tools_group.add_argument('--disable-ssl', action='store_true',
                      help='Disable SSL/TLS analysis')
    tools_group.add_argument('--enable-waf', action='store_true', default=True,
                      help='Enable WAF detection')
    tools_group.add_argument('--disable-waf', action='store_true',
                      help='Disable WAF detection')
    tools_group.add_argument('--enable-cors', action='store_true', default=True,
                      help='Enable CORS checks')
    tools_group.add_argument('--disable-cors', action='store_true',
                      help='Disable CORS checks')
    tools_group.add_argument('--enable-cms', action='store_true', default=True,
                      help='Enable CMS detection')
    tools_group.add_argument('--disable-cms', action='store_true',
                      help='Disable CMS detection')
    
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
    
    # Crawler options
    crawler_group = parser.add_argument_group('Crawler Options')
    crawler_group.add_argument('--crawler-depth', type=int, default=1,
                         help='Crawling depth (number of links to follow)')
    crawler_group.add_argument('--crawler-timeout', type=int, default=10,
                         help='Crawler timeout in seconds')
    
    # SSL/TLS options
    ssl_group = parser.add_argument_group('SSL/TLS Analysis Options')
    ssl_group.add_argument('--ssl-timeout', type=int, default=10,
                      help='SSL/TLS analysis timeout in seconds')
    ssl_group.add_argument('--no-check-ciphers', action='store_true',
                      help='Skip cipher strength check in SSL/TLS analysis')
    
    args = parser.parse_args()
    
    # Show workflow help if requested
    if args.help_workflows:
        print_workflow_help()
        return 0
    
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
    if args.disable_crawler:
        args.enable_crawler = False
    if args.disable_ssl:
        args.enable_ssl = False
    if args.disable_waf:
        args.enable_waf = False
    if args.disable_cors:
        args.enable_cors = False
    if args.disable_cms:
        args.enable_cms = False
    
    # Parse port range if provided
    port_list = parse_port_range(args.ports) if args.ports else None
    
    # Display the configuration
    print_section("CONFIGURATION")
    print_info(f"Target Domain: {args.domain}")
    print_info(f"Workflow: {args.workflow}")
    if args.workflow == "targeted":
        print_info(f"Target Type: {args.target_type}")
    if args.workflow == "comprehensive":
        print_info(f"Parallelism: {args.parallelism}")
    if args.workflow == "stealth":
        print_info(f"Delay: {args.delay}s, Jitter: {args.jitter}s")
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
    if args.enable_crawler:
        print_info("✓ Endpoint Crawling")
        print_info(f"  └─ Depth: {args.crawler_depth}")
    if args.enable_ssl:
        print_info("✓ SSL/TLS Analysis")
    if args.enable_waf:
        print_info("✓ WAF Detection")
    if args.enable_cors:
        print_info("✓ CORS Configuration Checks")
    if args.enable_cms:
        print_info("✓ CMS Detection")
    
    print_section(f"STARTING RECONNAISSANCE ON {args.domain}")
    logger.info(f"Starting '{args.workflow}' reconnaissance workflow for: {args.domain}")
    
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
        "enable_crawler": args.enable_crawler,
        "enable_ssl_analysis": args.enable_ssl,
        "enable_waf_detection": args.enable_waf,
        "enable_cors_checks": args.enable_cors,
        "enable_cms_detection": args.enable_cms,
        
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
        
        # Crawler parameters
        "crawler_depth": args.crawler_depth,
        "crawler_timeout": args.crawler_timeout,
        
        # SSL/TLS parameters
        "ssl_timeout": args.ssl_timeout,
        "ssl_check_ciphers": not args.no_check_ciphers,
        
        # Workflow intensity - adjust parameters based on workflow type
        "workflow_type": args.workflow
    }
    
    # Run the selected workflow with the specified parameters
    workflow_func = WORKFLOW_TYPES.get(args.workflow)
    
    if not workflow_func:
        print_error(f"Unknown workflow: {args.workflow}")
        return 1
    
    try:
        # Pass additional parameters based on workflow type
        workflow_kwargs = {
            "target_domain": args.domain,
            "model_id": args.model,
            "output_format": args.output,
            "save_report": not args.no_save,
            "save_raw_data": not args.no_raw_data,
            "tool_config": tool_config
        }
        
        # Add workflow-specific parameters
        if args.workflow == "targeted":
            workflow_kwargs["target_type"] = args.target_type
        elif args.workflow == "comprehensive":
            workflow_kwargs["parallelism"] = args.parallelism
        elif args.workflow == "stealth":
            workflow_kwargs["delay_between_requests"] = args.delay
            workflow_kwargs["jitter"] = args.jitter
        
        # Run the workflow
        report, report_path = workflow_func(**workflow_kwargs)
        
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
        logger.error(f"Failed to import {args.workflow} workflow: {e}")
        print_error(f"Could not load the {args.workflow} workflow. {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        print_error(f"The workflow failed with error: {e}")
        return 1
    
    logger.info(f"Finished '{args.workflow}' reconnaissance workflow")
    print_success(f"\nReconnaissance workflow completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
