#!/usr/bin/env python
"""
Script để kiểm thử Reporter agent.
"""

import os
import sys
import json
import datetime

# Thêm đường dẫn gốc vào sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config import settings
from config.settings import get_ag2_config_list
from agents.reporter import ReconReporter
from utils.logging_setup import setup_logging, get_logger
from tools.network import dns_lookup, whois_lookup
from tools.web import get_http_headers, extract_security_headers
from tools.search import search_subdomains

# Cài đặt logging
setup_logging()
logger = get_logger(__name__)

def test_reporter(domain="example.com", output_format="markdown"):
    """Kiểm thử Reporter agent.
    
    Args:
        domain: Tên miền để tạo báo cáo (mặc định: example.com)
        output_format: Định dạng báo cáo ("markdown", "html", "json")
    """
    print(f"=== Kiểm thử Reporter với tên miền: {domain} ===\n")
    
    # Lấy cấu hình LLM
    config_list = get_ag2_config_list()
    if not config_list:
        print("ERROR: Không thể lấy cấu hình LLM.")
        return
    
    llm_config = {
        "config_list": config_list,
        "cache_seed": 42,
        "temperature": 0.7,
    }
    
    # Thu thập dữ liệu từ công cụ
    print("Đang thu thập dữ liệu...\n")
    collected_data = {}
    
    # DNS
    print("- Thu thập thông tin DNS...")
    collected_data["dns"] = dns_lookup(domain)
    
    # WHOIS
    print("- Thu thập thông tin WHOIS...")
    collected_data["whois"] = whois_lookup(domain)
    
    # HTTP Headers
    print("- Thu thập HTTP Headers...")
    headers = get_http_headers(domain)
    collected_data["http_headers"] = headers
    
    # Security Headers
    if "error" not in headers:
        collected_data["security_headers"] = extract_security_headers(headers)
    
    # Subdomains
    print("- Tìm kiếm subdomain...")
    collected_data["subdomains"] = search_subdomains(domain, use_apis=True)
    
    # Tạo Reporter agent
    reporter = ReconReporter(llm_config=llm_config)
    
    # Yêu cầu tạo báo cáo
    print("\nĐang yêu cầu AI tạo báo cáo...\n")
    report, report_path = reporter.generate_report(
        target_domain=domain, 
        collected_data=collected_data, 
        output_format=output_format,
        save_report=True,
        save_raw_data=True
    )
    
    print(f"Đã lưu báo cáo vào file: {report_path}")
    
    # Tạo tóm tắt
    print("\nĐang yêu cầu AI tạo tóm tắt...\n")
    summary = reporter.summarize_findings(
        collected_data=collected_data, 
        max_length=500,
        include_risk_assessment=True
    )
    
    print("=== Tóm Tắt Kết Quả ===\n")
    print(summary)
    
    return report_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Kiểm thử Reporter agent")
    parser.add_argument("--domain", "-d", default="example.com", 
                       help="Tên miền để tạo báo cáo (mặc định: example.com)")
    parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "html", "json"],
                       help="Định dạng báo cáo (mặc định: markdown)")
    
    args = parser.parse_args()
    test_reporter(args.domain, args.format)