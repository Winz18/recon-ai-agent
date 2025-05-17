#!/usr/bin/env python
"""
Script để kiểm thử ReconPlanner agent.
"""

import os
import sys
import json

# Thêm đường dẫn gốc vào sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config import settings
from config.settings import get_ag2_config_list
from agents.recon_planner import ReconPlanner
from utils.logging_setup import setup_logging, get_logger

# Cài đặt logging
setup_logging()
logger = get_logger(__name__)

def test_recon_planner(domain="example.com"):
    """Kiểm thử ReconPlanner agent."""
    print(f"=== Kiểm thử ReconPlanner với tên miền: {domain} ===\n")
    
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
    
    # Danh sách công cụ có sẵn
    available_tools = [
        "dns_lookup", 
        "whois_lookup", 
        "get_http_headers", 
        "search_subdomains"
    ]
    
    # Tạo planner agent
    planner = ReconPlanner(llm_config=llm_config)
    
    # Yêu cầu tạo kế hoạch
    print("Đang yêu cầu AI tạo kế hoạch...\n")
    plan = planner.create_plan(target_domain=domain, available_tools=available_tools)
    
    # In kế hoạch
    print("=== Kế Hoạch Thu Thập Thông Tin ===\n")
    print(plan["plan"])
    
    # Lưu kế hoạch vào file
    output_file = f"plan_{domain.replace('.', '_')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print(f"\nĐã lưu kế hoạch vào file: {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Kiểm thử ReconPlanner agent")
    parser.add_argument("--domain", "-d", default="example.com", 
                       help="Tên miền để tạo kế hoạch (mặc định: example.com)")
    
    args = parser.parse_args()
    test_recon_planner(args.domain)