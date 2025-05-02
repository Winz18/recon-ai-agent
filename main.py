# scripts/run_recon.py
import sys
import os
import autogen
from typing import Dict, List, Optional, Union

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import config và tools
from config import settings
from config.settings import get_ag2_config_list
from tools.network import dns_lookup, whois_lookup
# Import các tools khác
from tools.web import get_http_headers, extract_security_headers
from tools.search import search_subdomains

def main(target_domain: str = settings.DEFAULT_TARGET_DOMAIN):
    """Chạy quy trình reconnaissance cơ bản sử dụng AG2 gốc."""

    print(f"\n--- Starting Native AG2 Reconnaissance Workflow for: {target_domain} ---")

    # --- 1. Lấy cấu hình LLM cho AG2 ---
    # Sử dụng Gemini model mặc định hoặc có thể truyền vào từ tham số dòng lệnh
    gemini_model_id = "gemini-2.5-pro-preview-03-25" # Hoặc model bạn muốn
    config_list = get_ag2_config_list(model_id=gemini_model_id)

    if not config_list:
        print("ERROR: Could not generate LLM configuration list. Exiting.")
        return

    # --- 2. Định nghĩa các Agent AG2 ---

    # Assistant Agent: Đóng vai trò lập kế hoạch, yêu cầu thông tin, tổng hợp
    assistant = autogen.AssistantAgent(
        name="Recon_Assistant",
        llm_config={
            "config_list": config_list,
            "cache_seed": 42, # Giúp kết quả ổn định hơn khi test
            "temperature": 0.7, # Có thể điều chỉnh độ sáng tạo của LLM
        },
        system_message="""You are a helpful AI assistant specialized in reconnaissance for penetration testing.
        Your goal is to gather information about the target domain using the available tools.
        Plan the steps, request tool execution from the user proxy, and summarize the findings.
        
        Available tools:
        - dns_lookup: Get DNS records (A, AAAA, MX, NS, TXT) for a domain
        - whois_lookup: Get WHOIS registration information for a domain
        - get_http_headers: Get HTTP headers from a web server
        - search_subdomains: Find subdomains using passive techniques
        
        Example workflow:
        1. Perform DNS lookups to understand basic infrastructure
        2. Check WHOIS information to understand registration details
        3. Find subdomains to expand attack surface
        4. Check HTTP headers for security configurations
        5. Summarize findings with potential security implications
        
        Ask to use one tool at a time.
        When you have gathered enough information, provide a clear summary of findings 
        with potential security implications and say TERMINATE."""
    )

    # User Proxy Agent: Đóng vai trò thực thi tool và nhận/gửi tin nhắn từ người dùng (nếu cần)
    user_proxy = autogen.UserProxyAgent(
        name="Tool_Executor_Proxy",
        human_input_mode="NEVER", # Chạy tự động, không hỏi người dùng
        max_consecutive_auto_reply=5, # Giới hạn số lần tự động trả lời liên tiếp
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
        code_execution_config=False, # Quan trọng: Đặt là False nếu chỉ gọi hàm Python (tools)
                                     # Đặt là {"use_docker": True/False} nếu cần thực thi code block (vd: Python script)
        llm_config=False # Không cần LLM cho agent này vì nó chỉ thực thi tool
    )

    # --- 3. Đăng ký Tools với User Proxy Agent ---
    # Các hàm tool sẽ được gọi bởi User Proxy khi Assistant yêu cầu
    print("Registering tools with User Proxy Agent...")
    user_proxy.register_function(
        function_map={
            "dns_lookup": dns_lookup,
            "whois_lookup": whois_lookup,
            # Thêm các tool khác ở đây
            "get_http_headers": get_http_headers,
            "search_subdomains": search_subdomains,
        }
    )
    print(f"Registered functions: {list(user_proxy.function_map.keys())}")

    # --- 4. Bắt đầu cuộc hội thoại ---
    initial_prompt = f"""Tiến hành thu thập thông tin (reconnaissance) cho tên miền: {target_domain}
    
    Hãy thực hiện các bước sau:
    1. Thu thập thông tin DNS records
    2. Tra cứu thông tin WHOIS
    3. Tìm kiếm các subdomain
    4. Kiểm tra HTTP headers của web server
    
    Sau khi thu thập đủ thông tin, hãy tổng hợp và phân tích kết quả từ góc độ bảo mật."""
    print(f"\nInitiating chat with prompt: '{initial_prompt}'")

    # User Proxy bắt đầu cuộc trò chuyện với Assistant
    user_proxy.initiate_chat(
        assistant,
        message=initial_prompt,
    )

    print("\n--- Reconnaissance Workflow Finished ---")

if __name__ == "__main__":
    import argparse
    
    # Cấu hình parser tham số dòng lệnh
    parser = argparse.ArgumentParser(description='AI-powered Reconnaissance for Penetration Testing')
    parser.add_argument('-d', '--domain', type=str, default=settings.DEFAULT_TARGET_DOMAIN,
                      help=f'Target domain to analyze (default: {settings.DEFAULT_TARGET_DOMAIN})')
    parser.add_argument('-m', '--model', type=str, default="gemini-2.5-pro-preview-03-25",
                      help='Google Vertex AI model ID to use')
    args = parser.parse_args()
    
    # Chạy quy trình reconnaissance với tham số từ dòng lệnh
    main(target_domain=args.domain)  # Sử dụng tên miền từ tham số dòng lệnh