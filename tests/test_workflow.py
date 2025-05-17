#!/usr/bin/env python
"""
Test script to verify the integration of new security tools in the standard workflow.
"""
from workflows.standard_recon_workflow import run_standard_recon_workflow

def main():
    """Run a quick workflow with all new tools enabled to test integration."""
    # Set up a minimal configuration for quick testing
    tool_config = {
        "workflow_type": "quick",
        
        # Enable only the web tools for faster testing
        "enable_dns": False,
        "enable_whois": False,
        "enable_headers": True,
        "enable_subdomains": False,
        "enable_ports": False,
        "enable_osint": False,
        "enable_tech": True,
        "enable_screenshot": False,
        "enable_crawler": True,
        
        # Enable the new tools
        "enable_ssl_analysis": True,
        "enable_waf_detection": True,
        "enable_cors_checks": True,
        "enable_cms_detection": True,
        
        # Use shorter timeouts for quicker testing
        "crawler_depth": 1,
        "crawler_timeout": 5,
        "ssl_timeout": 5,
        "waf_timeout": 5,
        "cors_timeout": 5,
        "cms_timeout": 5,
        
        # Disable payload testing for WAF detection to avoid triggering actual WAFs
        "waf_test_payloads": False
    }
    
    print("Starting test workflow with new security tools...")
    # Use a public domain for testing
    report, report_path = run_standard_recon_workflow(
        target_domain="ntop.org",
        tool_config=tool_config,
        save_report=True
    )
    
    print(f"Workflow completed. Report saved to: {report_path}")
    
    # Check if the new tools were executed by looking for keywords in the report
    new_tool_keywords = [
        "SSL/TLS", "certificate", "protocol", "cipher",
        "WAF", "firewall", "protection",
        "CORS", "cross-origin",
        "CMS", "content management system"
    ]
    
    found_keywords = []
    for keyword in new_tool_keywords:
        if keyword.lower() in report.lower():
            found_keywords.append(keyword)
    
    if found_keywords:
        print(f"Successfully found evidence of new tools in report: {', '.join(found_keywords)}")
    else:
        print("WARNING: Could not find evidence of new tools in the report")

if __name__ == "__main__":
    main() 