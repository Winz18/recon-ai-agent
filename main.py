# main.py
import sys
import os
import argparse
import json
import logging
from typing import Dict, List, Optional, Union

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import config
from config import settings
from utils.cli import cli, set_verbosity
from utils.logging_setup import setup_logging
from workflows import WORKFLOW_TYPES

# Set up logging via our new CLI utility
logger = setup_logging()

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
    cli.header("AVAILABLE WORKFLOWS")
    
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
        cli.info(f"{name}: {desc}")
    
    cli.divider()
    cli.subheader("For targeted workflow, specify a target type with --target-type:")
    for name, desc in target_types.items():
        cli.verbose(f"  {name}: {desc}")
    
    cli.divider()
    cli.subheader("Example commands:")
    cli.info("python main.py -d example.com -w standard")
    cli.info("python main.py -d example.com -w quick --disable-ports")
    cli.info("python main.py -d example.com -w targeted --target-type ssl")
    cli.info("python main.py -d example.com -w comprehensive --parallelism 4")

def main():
    """
    Entry point for reconnaissance workflows.
    Parses command line arguments and runs the selected workflow.
    """
    # Display a nice banner
    cli.header("RECON AI-AGENT")
    cli.subheader("AI-Powered Reconnaissance for Network Security Testing")
    
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
    basic_group.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2, 3], default=1,
                      help='Set output verbosity (0=quiet, 1=normal, 2=verbose, 3=debug)')
    
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
    
    args = parser.parse_args()
    
    # Set verbosity level
    set_verbosity(args.verbosity)
    
    # Show workflow help and exit if requested
    if args.help_workflows:
        print_workflow_help()
        return
    
    # Check if target domain is specified
    if not args.domain:
        cli.error("No target domain specified.")
        parser.print_help()
        return
        
    cli.subheader(f"Target: {args.domain}")
    cli.subheader(f"Workflow: {args.workflow}")
    
    # Prepare tool configuration dictionary
    tool_config = {
        # Enable/disable tools based on command line arguments
        "enable_dns": args.enable_dns and not args.disable_dns,
        "enable_whois": args.enable_whois and not args.disable_whois,
        "enable_headers": args.enable_headers and not args.disable_headers,
        "enable_subdomains": args.enable_subdomains and not args.disable_subdomains,
        "enable_ports": args.enable_ports and not args.disable_ports,
        "enable_osint": args.enable_osint and not args.disable_osint,
        "enable_tech": args.enable_tech and not args.disable_tech,
        "enable_screenshot": args.enable_screenshot and not args.disable_screenshot,
        "enable_crawler": args.enable_crawler and not args.disable_crawler,
        "enable_ssl_analysis": args.enable_ssl and not args.disable_ssl,
        "enable_waf_detection": args.enable_waf and not args.disable_waf,
        "enable_cors_checks": args.enable_cors and not args.disable_cors,
        "enable_cms_detection": args.enable_cms and not args.disable_cms,
        
        # Tool parameters
        "port_list": parse_port_range(args.ports),
        "port_timeout": args.port_timeout,
        "port_threads": args.port_threads,
        "port_scan_type": args.port_scan_type,
        
        "use_subdomain_apis": args.use_apis,
        "max_subdomains": args.max_subdomains,
        
        "http_timeout": args.http_timeout,
        "user_agent": args.user_agent,
        
        "dorks_limit": args.dorks_limit,
        
        "crawler_depth": args.crawler_depth,
        "crawler_timeout": args.crawler_timeout,
        
        "ssl_timeout": args.ssl_timeout,
        
        "workflow_type": args.workflow,
        "target_type": args.target_type
    }
    
    # Get workflow function
    workflow_func = WORKFLOW_TYPES.get(args.workflow)
    if not workflow_func:
        cli.error(f"Unknown workflow type: {args.workflow}")
        parser.print_help()
        return
    
    try:
        # Log enabled tool groups
        cli.info("Enabled tool groups:")
        for tool_group in [
            ("DNS lookup", tool_config["enable_dns"]),
            ("WHOIS lookup", tool_config["enable_whois"]),
            ("HTTP headers", tool_config["enable_headers"]),
            ("Subdomain enumeration", tool_config["enable_subdomains"]),
            ("Port scanning", tool_config["enable_ports"]),
            ("OSINT gathering", tool_config["enable_osint"]),
            ("Technology detection", tool_config["enable_tech"]),
            ("Website screenshots", tool_config["enable_screenshot"]),
            ("Endpoint crawling", tool_config["enable_crawler"]),
            ("SSL/TLS analysis", tool_config["enable_ssl_analysis"]),
            ("WAF detection", tool_config["enable_waf_detection"]),
            ("CORS checks", tool_config["enable_cors_checks"]),
            ("CMS detection", tool_config["enable_cms_detection"])
        ]:
            if tool_group[1]:
                cli.verbose(f"  ✓ {tool_group[0]}")
            else:
                cli.verbose(f"  ✗ {tool_group[0]}")
        
        # Execute workflow with parameters
        cli.header("Starting Reconnaissance")
        
        if args.workflow == "comprehensive":
            report, report_path = workflow_func(
                target_domain=args.domain, 
                model_id=args.model,
                output_format=args.output,
                save_report=not args.no_save,
                save_raw_data=not args.no_raw_data,
                parallelism=args.parallelism,
                tool_config=tool_config
            )
        elif args.workflow == "stealth":
            report, report_path = workflow_func(
                target_domain=args.domain, 
                model_id=args.model,
                output_format=args.output,
                save_report=not args.no_save,
                save_raw_data=not args.no_raw_data,
                delay_between_requests=args.delay,
                jitter=args.jitter,
                tool_config=tool_config
            )
        elif args.workflow == "targeted":
            # Targeted workflow requires target_type
            report, report_path = workflow_func(
                target_domain=args.domain, 
                model_id=args.model,
                output_format=args.output,
                save_report=not args.no_save,
                save_raw_data=not args.no_raw_data,
                target_type=args.target_type,
                tool_config=tool_config
            )
        else:
            # Standard, quick, and deep workflows
            report, report_path = workflow_func(
                target_domain=args.domain, 
                model_id=args.model,
                output_format=args.output,
                save_report=not args.no_save,
                save_raw_data=not args.no_raw_data,
                tool_config=tool_config
            )
        
        # Display report summary
        cli.success(f"Reconnaissance workflow completed successfully!")
        
        if report_path:
            cli.success(f"Report saved to: {report_path}")
            
        # Print report summary from workflow output
        summary_lines = report.split("\n")[:20]  # Just grab the first few lines
        if len(summary_lines) > 5:
            cli.divider()
            cli.subheader("Report Preview:")
            for line in summary_lines[:5]:  # Show only first 5 lines
                cli.info(line)
            cli.info("... (see full report for details)")
            
    except Exception as e:
        cli.error(f"Error during reconnaissance: {str(e)}")
        if args.verbosity >= 3:  # Debug mode
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
