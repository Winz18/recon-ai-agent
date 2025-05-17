#!/usr/bin/env python
"""
Test script to demonstrate the use of the new web security tools.
"""
import asyncio
import json
from tools import analyze_ssl_tls, detect_waf, check_cors_config, detect_cms

async def test_all_tools():
    """Test all new security tools and print their results."""
    test_url = "hcmute.edu.vn"  # Use a public website for testing
    
    print("=== Testing SSL/TLS Analyzer ===")
    ssl_results = analyze_ssl_tls(test_url)
    print(f"SSL/TLS Grade: {ssl_results.get('summary', {}).get('grade', 'Unknown')}")
    print(f"Issues Found: {len(ssl_results.get('issues', []))}")
    if ssl_results.get('issues'):
        print("Top issues:")
        for issue in ssl_results.get('issues')[:3]:
            print(f"  - {issue}")
    print(f"Recommendations: {ssl_results.get('summary', {}).get('recommendations', ['None'])[:2]}")
    print()
    
    print("=== Testing WAF Detector ===")
    waf_results = await detect_waf(test_url, test_payloads=False)  # Disable payloads for safe testing
    print(f"WAF Detected: {waf_results.get('waf_detected', False)}")
    if waf_results.get('identified_wafs'):
        print(f"Identified WAFs: {', '.join(waf_results.get('identified_wafs', []))}")
    print(f"Confidence Level: {waf_results.get('confidence_level', 'None')}")
    if waf_results.get('bypass_suggestions'):
        print("Bypass Suggestions:")
        for suggestion in waf_results.get('bypass_suggestions')[:2]:
            print(f"  - {suggestion}")
    print()
    
    print("=== Testing CORS Checker ===")
    cors_results = await check_cors_config(test_url)
    print(f"Has CORS Headers: {cors_results.get('has_cors_headers', False)}")
    print(f"CORS Misconfiguration Detected: {cors_results.get('is_vulnerable', False)}")
    if cors_results.get('vulnerabilities'):
        print("Vulnerabilities:")
        for vuln in cors_results.get('vulnerabilities', []):
            print(f"  - {vuln.get('type')}: {vuln.get('details')}")
    if cors_results.get('recommendations'):
        print("Recommendations:")
        for rec in cors_results.get('recommendations')[:2]:
            print(f"  - {rec}")
    print()
    
    print("=== Testing CMS Detector ===")
    cms_results = await detect_cms(test_url)
    print(f"Detected CMS: {cms_results.get('detected_cms', 'None')}")
    print(f"Confidence: {cms_results.get('confidence', 0)}%")
    print(f"Version: {cms_results.get('version', 'Unknown')}")
    if cms_results.get('detected_plugins'):
        print(f"Plugins: {', '.join([p.get('name') for p in cms_results.get('detected_plugins', [])][:3])}")
    if cms_results.get('additional_info', {}).get('common_security_issues'):
        print("Common Security Issues:")
        for issue in cms_results.get('additional_info', {}).get('common_security_issues', [])[:3]:
            print(f"  - {issue}")

if __name__ == "__main__":
    asyncio.run(test_all_tools()) 