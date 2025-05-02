import os
import sys
import logging
import autogen
from typing import Dict, List, Optional

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config import settings
from config.settings import get_ag2_config_list
from tools.network import dns_lookup, whois_lookup
from tools.web import get_http_headers, extract_security_headers
from tools.search import search_subdomains
from utils.logging_setup import setup_logging, get_logger

# Cài đặt logging
logger = get_logger(__name__)

def run_basic_recon(
    target_domain: str = settings.DEFAULT_TARGET_DOMAIN,
    model_id: str = "gemini-2.5-pro-preview-03-25",
    output_file: Optional[str] = None
) -> Dict:
    """
    Chạy quy trình reconnaissance cơ bản bằng AG2 framework.
    
    Args:
        target_domain: Tên miền mục tiêu
        model_id: ID của model Gemini trên Vertex AI
        output_file: Đường dẫn file để lưu kết quả (None nếu không lưu)
        
    Returns:
        Dictionary chứa kết quả thu thập được
    """
    logger.info(f"Starting basic reconnaissance workflow for domain: {target_domain}")
    
    # Lấy cấu hình LLM cho AG2
    config_list = get_ag2_config_list(model_id=model_id)
    if not config_list:
        logger.error("Failed to generate LLM configuration list.")
        return {"error": "Failed to generate LLM configuration"}
    
    # Định nghĩa các Agent
    assistant = autogen.AssistantAgent(
        name="Recon_Assistant",
        llm_config={
            "config_list": config_list,
            "cache_seed": 42,
            "temperature": 0.7,
        },
        system_message="""You are a helpful AI assistant specialized in reconnaissance for penetration testing.
        Your goal is to gather information about the target domain using the available tools.
        
        Available tools:
        - dns_lookup: Get DNS records (A, AAAA, MX, NS, TXT) for a domain
        - whois_lookup: Get WHOIS registration information for a domain
        - get_http_headers: Get HTTP headers from a web server
        - search_subdomains: Find subdomains using passive techniques
        
        Follow this workflow:
        1. Perform DNS lookups to understand basic infrastructure
        2. Check WHOIS information to understand registration details
        3. Find subdomains to expand attack surface
        4. Check HTTP headers for security configurations
        5. Summarize findings with potential security implications
        
        Ask to use one tool at a time.
        When you have gathered enough information, provide a clear summary of findings 
        with potential security implications and say TERMINATE."""
    )
    
    # User Proxy Agent đóng vai trò thực thi tool
    user_proxy = autogen.UserProxyAgent(
        name="Tool_Executor",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
        code_execution_config=False,
        llm_config=False
    )
    
    # Đăng ký tools với user proxy
    logger.info("Registering tools with User Proxy Agent...")
    user_proxy.register_function(
        function_map={
            "dns_lookup": dns_lookup,
            "whois_lookup": whois_lookup,
            "get_http_headers": get_http_headers,
            "search_subdomains": search_subdomains,
        }
    )
    
    # Tạo prompt khởi đầu
    initial_prompt = f"""Tiến hành thu thập thông tin (reconnaissance) cho tên miền: {target_domain}
    
    Hãy thực hiện các bước sau:
    1. Thu thập thông tin DNS records
    2. Tra cứu thông tin WHOIS
    3. Tìm kiếm các subdomain
    4. Kiểm tra HTTP headers của web server
    
    Sau khi thu thập đủ thông tin, hãy tổng hợp và phân tích kết quả từ góc độ bảo mật."""
    
    # Lưu trữ tin nhắn và kết quả
    collected_messages = []
    
    # Bắt đầu cuộc hội thoại
    logger.info(f"Starting chat with initial prompt: {initial_prompt[:100]}...")
    
    # Override phương thức receive để lưu lại tin nhắn
    original_receive = user_proxy.receive
    
    def receive_and_log(message, sender, **kwargs):
        collected_messages.append({"role": sender.name, "content": message.get("content", "")})
        return original_receive(message, sender, **kwargs)
    
    user_proxy.receive = receive_and_log
    
    # Bắt đầu trò chuyện
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=initial_prompt,
    )
    
    # Tổng hợp kết quả
    result = {
        "target_domain": target_domain,
        "model_id": model_id,
        "messages": collected_messages,
        "summary": collected_messages[-1]["content"] if collected_messages else "No summary available",
    }
    
    # Lưu kết quả nếu được yêu cầu
    if output_file:
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {e}")
    
    return result

# Cho phép chạy trực tiếp file này
if __name__ == "__main__":
    import argparse
    
    # Cài đặt logging cơ bản
    setup_logging(log_level=logging.INFO)
    
    # Cấu hình parser
    parser = argparse.ArgumentParser(description='Basic Reconnaissance Workflow')
    parser.add_argument('-d', '--domain', type=str, default=settings.DEFAULT_TARGET_DOMAIN,
                      help=f'Target domain to analyze (default: {settings.DEFAULT_TARGET_DOMAIN})')
    parser.add_argument('-m', '--model', type=str, default="gemini-2.5-pro-preview-03-25",
                      help='Gemini model ID to use')
    parser.add_argument('-o', '--output', type=str, help='Path to save output JSON file')
    
    args = parser.parse_args()
    
    # Chạy workflow
    run_basic_recon(
        target_domain=args.domain,
        model_id=args.model,
        output_file=args.output
    )