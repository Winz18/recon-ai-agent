# main.py
import sys
import os
import autogen
from typing import Dict, List, Optional, Union

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__))) # Giả sử main.py nằm trong thư mục gốc dự án
# Nếu main.py nằm trong thư mục con (ví dụ: scripts), bạn cần điều chỉnh lại:
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import config và tools
from config import settings
from config.settings import get_ag2_config_list
from tools.network import dns_lookup, whois_lookup
# Import các tools khác
from tools.web import get_http_headers, extract_security_headers
from tools.search import search_subdomains
from utils.logging_setup import setup_logging, get_logger # Thêm import logger

# Cài đặt logging (Thêm vào đầu nếu chưa có)
logger = setup_logging()


def main(target_domain: str = settings.DEFAULT_TARGET_DOMAIN, model_id: str = "gemini-2.5-pro-preview-05-06"): # Thay model mặc định nếu cần
    """Chạy quy trình reconnaissance cơ bản sử dụng AG2."""

    logger.info(f"--- Starting Native AG2 Reconnaissance Workflow for: {target_domain} using model: {model_id} ---")

    # --- 1. Lấy cấu hình LLM cho AG2 ---
    config_list = get_ag2_config_list(model_id=model_id)

    if not config_list:
        logger.error("ERROR: Could not generate LLM configuration list. Exiting.")
        return

    # --- Định nghĩa các tool schemas cho AssistantAgent ---
    tools_schemas = [
        {
            "type": "function",
            "function": {
                "name": "dns_lookup",
                "description": "Performs DNS lookups (A, AAAA, MX, NS, TXT records) for a given domain.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The domain name to lookup."
                        }
                    },
                    "required": ["domain"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "whois_lookup",
                "description": "Performs a WHOIS lookup for the given domain.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The domain name to perform WHOIS lookup."
                        }
                    },
                    "required": ["domain"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_http_headers",
                "description": "Retrieves HTTP headers from a web server.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to get HTTP headers from. If not starting with http, https will be prepended."
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_subdomains",
                "description": "Searches for subdomains of a given domain using passive techniques.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The base domain to find subdomains for."
                        },
                        "use_apis": {
                            "type": "boolean",
                            "description": "Whether to use online services (can be slower but more comprehensive). Default: True",
                            "default": True
                        }
                    },
                    "required": ["domain"]
                }
            }
        }
    ]

    # --- 2. Định nghĩa các Agent AG2 ---

    # Assistant Agent: Đóng vai trò lập kế hoạch, yêu cầu thông tin, tổng hợp
    assistant = autogen.AssistantAgent(
        name="Recon_Assistant",
        llm_config={
            "config_list": config_list,
            "cache_seed": 42,
            "temperature": 0.7,
            "tools": tools_schemas, # Cung cấp schema của tools cho LLM
        },
        system_message="""You are a helpful AI assistant specialized in reconnaissance for penetration testing.
        Your goal is to gather information about the target domain by calling the available tools.
        You must use the provided tools to answer questions.
        When you need to use a tool, respond with a tool_call for that tool.
        Do not ask the user to execute the tool for you. You must generate the tool_call yourself.

        Available tools:
        - dns_lookup: Get DNS records (A, AAAA, MX, NS, TXT) for a domain
        - whois_lookup: Get WHOIS registration information for a domain
        - get_http_headers: Get HTTP headers from a web server
        - search_subdomains: Find subdomains using passive techniques

        Workflow:
        1. Perform DNS lookups for the target domain.
        2. Check WHOIS information for the target domain.
        3. Find subdomains for the target domain.
        4. Check HTTP headers for the target domain's web server.
        5. After gathering all information, provide a clear summary of findings with potential security implications and then say TERMINATE.

        Always call one tool at a time. Ensure you provide the correct parameters for each tool.
        For 'get_http_headers' and 'search_subdomains', the parameter is 'url' or 'domain' respectively, not 'target_domain'.
        For 'dns_lookup' and 'whois_lookup', the parameter is 'domain'.
        """
    )

    # User Proxy Agent: Đóng vai trò thực thi tool
    user_proxy = autogen.UserProxyAgent(
        name="Tool_Executor_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10, # Tăng lên một chút để cho phép chuỗi tool call và response
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
        code_execution_config=False,
        llm_config=False
    )

    # --- 3. Đăng ký Tools với User Proxy Agent ---
    logger.info("Registering tools with User Proxy Agent...")
    user_proxy.register_function(
        function_map={
            "dns_lookup": dns_lookup,
            "whois_lookup": whois_lookup,
            "get_http_headers": get_http_headers,
            "search_subdomains": search_subdomains,
        }
    )
    logger.info(f"Registered functions: {list(user_proxy.function_map.keys())}")

    # --- 4. Bắt đầu cuộc hội thoại ---
    initial_prompt = f"Tiến hành thu thập thông tin (reconnaissance) cho tên miền: {target_domain}"
    logger.info(f"\nInitiating chat with prompt: '{initial_prompt}'")

    # User Proxy bắt đầu cuộc trò chuyện với Assistant
    user_proxy.initiate_chat(
        assistant,
        message=initial_prompt,
    )

    logger.info("\n--- Reconnaissance Workflow Finished ---")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AI-powered Reconnaissance for Penetration Testing')
    parser.add_argument('-d', '--domain', type=str, default=settings.DEFAULT_TARGET_DOMAIN,
                      help=f'Target domain to analyze (default: {settings.DEFAULT_TARGET_DOMAIN})')
    parser.add_argument('-m', '--model', type=str, default="gemini-2.5-pro-preview-05-06", # Cập nhật model nếu cần
                      help='Google Vertex AI model ID to use')
    args = parser.parse_args()

    main(target_domain=args.domain, model_id=args.model)