#!/usr/bin/env python
"""
Script để kiểm thử các công cụ network, web và search.
Chạy script này để xác minh các công cụ hoạt động bình thường.
"""

import os
import sys
import json
from pprint import pprint

# Thêm đường dẫn gốc vào sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import các công cụ
from tools.network import dns_lookup, whois_lookup
from tools.web import get_http_headers, extract_security_headers
from tools.search import search_subdomains
from utils.logging_setup import setup_logging, get_logger

# Cài đặt logging
setup_logging()
logger = get_logger(__name__)

def test_network_tools(domain="google.com"):
    """Kiểm thử các công cụ network."""
    print(f"\n=== Kiểm thử công cụ DNS lookup với tên miền: {domain} ===")
    dns_results = dns_lookup(domain)
    
    if isinstance(dns_results, dict):
        print("\nĐã nhận được kết quả DNS:")
        for record_type, records in dns_results.items():
            print(f"- {record_type}: {records}")
    else:
        print(f"Lỗi: {dns_results}")
    
    print(f"\n=== Kiểm thử công cụ WHOIS lookup với tên miền: {domain} ===")
    whois_results = whois_lookup(domain)
    print(f"Đã nhận được {len(whois_results)} ký tự trong kết quả WHOIS")
    print(f"Vài dòng đầu tiên:\n{whois_results[:300]}...")

def test_web_tools(domain="google.com"):
    """Kiểm thử các công cụ web."""
    print(f"\n=== Kiểm thử công cụ HTTP Headers với tên miền: {domain} ===")
    headers = get_http_headers(domain)
    
    if "error" not in headers:
        print("\nĐã nhận được HTTP headers:")
        for name, value in headers.items():
            if name.lower() in ["content-security-policy", "strict-transport-security"]:
                print(f"- {name}: {value}")
            
        # Phân tích security headers
        print("\n=== Phân tích Security Headers ===")
        security_analysis = extract_security_headers(headers)
        
        print("\nCác security headers đã tìm thấy:")
        for header in security_analysis["analysis"]["found_headers"]:
            print(f"- {header}")
            
        print("\nCác security headers bị thiếu:")
        for header in security_analysis["analysis"]["missing_headers"]:
            print(f"- {header}")
    else:
        print(f"Lỗi: {headers['error']}")

def test_search_tools(domain="google.com"):
    """Kiểm thử công cụ tìm kiếm subdomain."""
    print(f"\n=== Tìm kiếm subdomain cho tên miền: {domain} ===")
    subdomains = search_subdomains(domain, use_apis=True)
    
    if subdomains:
        print(f"\nĐã tìm thấy {len(subdomains)} subdomains:")
        for subdomain in subdomains:
            print(f"- {subdomain}")
    else:
        print("Không tìm thấy subdomain nào.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Kiểm thử các công cụ reconnaissance")
    parser.add_argument("--domain", "-d", default="example.com", 
                       help="Tên miền để kiểm thử (mặc định: example.com)")
    parser.add_argument("--all", "-a", action="store_true", 
                       help="Chạy tất cả các kiểm thử")
    parser.add_argument("--network", "-n", action="store_true", 
                       help="Chạy kiểm thử công cụ network")
    parser.add_argument("--web", "-w", action="store_true", 
                       help="Chạy kiểm thử công cụ web")
    parser.add_argument("--search", "-s", action="store_true", 
                       help="Chạy kiểm thử công cụ tìm kiếm")
    
    args = parser.parse_args()
    
    # Nếu không có đối số cụ thể nào, chạy tất cả
    run_all = args.all or not (args.network or args.web or args.search)
    
    print(f"Kiểm thử với tên miền: {args.domain}")
    
    if run_all or args.network:
        test_network_tools(args.domain)
    
    if run_all or args.web:
        test_web_tools(args.domain)
    
    if run_all or args.search:
        test_search_tools(args.domain)