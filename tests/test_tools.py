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
from tools.port_scanner import scan_ports, get_top_ports
from tools.google_dorking import search_google_dorks, get_common_dorks
from tools.tech_detector import detect_technologies
from tools.screenshot import capture_website_screenshot, check_webdriver_requirements
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

def test_port_scanner(target="example.com"):
    """Kiểm thử công cụ quét cổng."""
    print(f"\n=== Quét cổng trên máy chủ: {target} ===")
    ports = [80, 443, 22]  # Chỉ quét một số cổng phổ biến để tiết kiệm thời gian
    results = scan_ports(target, ports=ports, timeout=1.0)
    
    if "error" not in results:
        print(f"\nĐã quét {len(ports)} cổng và tìm thấy {len(results)} cổng mở:")
        for port, info in results.items():
            print(f"- Cổng {port}: {info['service']}")
    else:
        print(f"Lỗi: {results['error']}")
        
    # Kiểm tra danh sách cổng phổ biến
    top_ports = get_top_ports(10)
    print(f"\nTop 10 cổng phổ biến: {top_ports}")

def test_google_dorking(domain="example.com"):
    """Kiểm thử công cụ Google dorking."""
    print(f"\n=== Thực hiện Google dorking cho tên miền: {domain} ===")
    
    # Chỉ dùng một số dork nhất định để kiểm thử
    dorks = [f"site:{domain}", f"site:{domain} filetype:pdf"]
    
    try:
        print("Thực hiện tìm kiếm với số lượng dork giới hạn...")
        results = search_google_dorks(domain, dorks=dorks, max_results=5, respect_rate_limits=True)
        
        if "error" not in results:
            print("\nKết quả Google dorking:")
            found_results = False
            
            for dork, links in results.items():
                if not dork.endswith('_error') and not dork.endswith('_skipped'):
                    found_results = True
                    print(f"\n== Dork: {dork} ==")
                    for i, item in enumerate(links[:3], 1):  # Chỉ hiển thị tối đa 3 kết quả
                        print(f"{i}. {item.get('link', 'N/A')}")
            
            if not found_results:
                print("Không tìm thấy kết quả nào cho các dork đã thử.")
        else:
            print(f"Lỗi: {results['error']}")
            print("Kiểm tra xem có bị giới hạn bởi Google không. Thử lại sau hoặc sử dụng ít dork hơn.")
    except Exception as e:
        print(f"Lỗi không mong đợi khi thực hiện Google dorking: {str(e)}")
        
    # Hiển thị các dork phổ biến
    print(f"\nCác Google dork phổ biến cho {domain}:")
    try:
        common_dorks = get_common_dorks(domain)
        for i, dork in enumerate(common_dorks[:5], 1):  # Chỉ hiển thị 5 dork đầu tiên
            print(f"{i}. {dork}")
    except Exception as e:
        print(f"Lỗi khi lấy danh sách dork phổ biến: {str(e)}")

def test_tech_detector(url="https://example.com"):
    """Kiểm thử công cụ phát hiện công nghệ web."""
    print(f"\n=== Phát hiện công nghệ web trên trang: {url} ===")
    results = detect_technologies(url, check_js=False)
    
    if "error" not in results:
        print("\nCông nghệ được phát hiện:")
        for category, technologies in results.items():
            if category not in ["headers"] and technologies:  # Bỏ qua headers vì quá dài
                print(f"\n== {category.upper()} ==")
                for tech, value in technologies.items():
                    print(f"- {tech}: {value}")
    else:
        print(f"Lỗi: {results['error']}")

def test_screenshot(url="https://example.com"):
    """Kiểm thử công cụ chụp ảnh website."""
    print(f"\n=== Chụp ảnh website: {url} ===")
    
    # Kiểm tra yêu cầu trước
    print("\nKiểm tra yêu cầu webdriver:")
    requirements = check_webdriver_requirements()
    for req, available in requirements.items():
        print(f"- {req}: {'Có sẵn' if available else 'Không có sẵn'}")
    
    # Thực hiện chụp ảnh
    output_dir = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
    result = capture_website_screenshot(url, output_dir)
    
    if "error" not in result:
        print(f"\nĐã chụp ảnh thành công với phương thức {result.get('method', 'unknown')}:")
        print(f"- Đường dẫn file: {result.get('screenshot_path', 'unknown')}")
    else:
        print(f"Lỗi: {result['error']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Kiểm thử các công cụ reconnaissance")
    parser.add_argument("--domain", "-d", default="example.com", 
                       help="Tên miền để kiểm thử (mặc định: example.com)")
    parser.add_argument("--url", "-u", default="https://example.com",
                       help="URL đầy đủ để kiểm thử (mặc định: https://example.com)")
    parser.add_argument("--all", "-a", action="store_true", 
                       help="Chạy tất cả các kiểm thử")
    parser.add_argument("--network", "-n", action="store_true", 
                       help="Chạy kiểm thử công cụ network")
    parser.add_argument("--web", "-w", action="store_true", 
                       help="Chạy kiểm thử công cụ web")
    parser.add_argument("--search", "-s", action="store_true", 
                       help="Chạy kiểm thử công cụ tìm kiếm")
    parser.add_argument("--ports", "-p", action="store_true",
                       help="Chạy kiểm thử công cụ quét cổng")
    parser.add_argument("--dorking", "-g", action="store_true",
                       help="Chạy kiểm thử công cụ Google dorking")
    parser.add_argument("--tech", "-t", action="store_true",
                       help="Chạy kiểm thử công cụ phát hiện công nghệ web")
    parser.add_argument("--screenshot", "-c", action="store_true",
                       help="Chạy kiểm thử công cụ chụp ảnh website")
    parser.add_argument("--unittest", action="store_true",
                       help="Chạy các unit test cho tất cả các công cụ mới")
    
    args = parser.parse_args()
    
    # Nếu không có đối số cụ thể nào, chạy tất cả
    run_all = args.all or not (args.network or args.web or args.search or 
                              args.ports or args.dorking or args.tech or
                              args.screenshot or args.unittest)
    
    print(f"Kiểm thử với tên miền: {args.domain}")
    print(f"Kiểm thử với URL: {args.url}")
    
    if args.unittest:
        print("\n=== Chạy unit tests cho các công cụ mới ===")
        sys.path.insert(0, os.path.join(project_root, 'tests'))
        from tests.test_new_tools import run_tests
        run_tests()
        sys.exit(0)
    
    if run_all or args.network:
        test_network_tools(args.domain)
    
    if run_all or args.web:
        test_web_tools(args.domain)
        
    if run_all or args.search:
        test_search_tools(args.domain)
        
    if run_all or args.ports:
        test_port_scanner(args.domain)
        
    if run_all or args.dorking:
        test_google_dorking(args.domain)
        
    if run_all or args.tech:
        test_tech_detector(args.url)
        
    if run_all or args.screenshot:
        test_screenshot(args.url)
    
    if run_all or args.search:
        test_search_tools(args.domain)