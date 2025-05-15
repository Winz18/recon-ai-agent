#!/usr/bin/env python3
# examples/standard_workflow_example.py
"""
Ví dụ sử dụng standard_recon_workflow để thực hiện các bước reconnaissance 
cơ bản trên một tên miền. File này minh họa cách sử dụng workflow chuẩn,
với và không có sự tham gia của AI Agents.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Thêm đường dẫn gốc vào sys.path để import các module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import workflow
from workflows.standard_recon_workflow import run_standard_recon
from config.settings import get_ag2_config_list

def main():
    """
    Hàm chính thực thi quy trình Reconnaissance chuẩn
    """
    # Phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(description='Ví dụ sử dụng Standard Recon Workflow')
    parser.add_argument('--domain', required=True, help='Tên miền mục tiêu để phân tích')
    parser.add_argument('--output', default='json', choices=['json', 'text', 'html'], 
                       help='Định dạng đầu ra')
    parser.add_argument('--no-agent', action='store_true', 
                       help='Chỉ chạy công cụ cơ bản, không sử dụng AI Agent')
    parser.add_argument('--verbose', action='store_true', help='Hiển thị thông tin chi tiết')
    
    args = parser.parse_args()
    
    print(f"[+] Bắt đầu quá trình reconnaissance cho tên miền: {args.domain}")
    start_time = datetime.now()
    
    # Cấu hình AutoGen nếu sử dụng AI Agent
    ag2_config = None
    if not args.no_agent:
        print("[+] Khởi tạo AI Agents...")
        ag2_config = get_ag2_config_list()[0]  # Lấy cấu hình đầu tiên
    
    # Thực thi workflow
    try:
        results = run_standard_recon(
            target_domain=args.domain,
            use_ai_agents=not args.no_agent,
            ag2_config=ag2_config,
            verbose=args.verbose
        )
        
        # Hiển thị và lưu kết quả
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n[+] Reconnaissance hoàn thành trong {duration:.2f} giây")
        
        # Tạo tên file báo cáo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{args.domain.replace('.', '_')}_{timestamp}"
        
        # Lưu báo cáo theo định dạng yêu cầu
        if args.output == 'json':
            output_file = os.path.join(project_root, 'reports', f"{filename}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            print(f"[+] Báo cáo JSON đã được lưu vào: {output_file}")
            
            # In tóm tắt kết quả
            print("\n=== Tóm tắt kết quả ===")
            print(f"Tên miền: {args.domain}")
            print(f"Địa chỉ IP: {results.get('dns_info', {}).get('A', ['N/A'])[0]}")
            print(f"Số lượng subdomain tìm thấy: {len(results.get('subdomains', []))}")
            print(f"Các cổng mở: {', '.join(str(p) for p in results.get('open_ports', []))}")
            
        elif args.output == 'html':
            # Logic tạo báo cáo HTML ở đây
            # (thường sẽ sử dụng một template engine như Jinja2)
            output_file = os.path.join(project_root, 'reports', f"{filename}.html")
            print(f"[+] Báo cáo HTML đã được lưu vào: {output_file}")
            
        else:  # text
            output_file = os.path.join(project_root, 'reports', f"{filename}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Báo cáo Reconnaissance cho {args.domain} ===\n")
                f.write(f"Thời gian: {start_time}\n\n")
                
                # Ghi các phần kết quả
                f.write("== Thông tin DNS ==\n")
                for record_type, records in results.get('dns_info', {}).items():
                    f.write(f"{record_type}: {', '.join(records)}\n")
                
                f.write("\n== Thông tin WHOIS ==\n")
                for key, value in results.get('whois_info', {}).items():
                    f.write(f"{key}: {value}\n")
                
                # Ghi thêm các thông tin khác...
                
            print(f"[+] Báo cáo Text đã được lưu vào: {output_file}")
    
    except Exception as e:
        print(f"[!] Lỗi: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())