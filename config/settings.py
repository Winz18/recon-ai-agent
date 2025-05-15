# config/settings.py
import os
import logging
from dotenv import load_dotenv

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logger.info("Loaded environment variables from .env file.")
else:
    logger.info(".env file not found, relying on system environment variables.")

# --- Google Cloud Configuration (Required for AG2 Vertex AI integration) ---
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_REGION = os.getenv("GOOGLE_REGION")

if not GOOGLE_PROJECT_ID or not GOOGLE_REGION:
    # AG2 cần thông tin này để biết gọi Vertex AI endpoint nào
    logger.error("FATAL: GOOGLE_PROJECT_ID and GOOGLE_REGION must be set in environment variables for Vertex AI integration.")
    raise ValueError("Missing required Google Cloud configuration (Project ID or Region).")
else:
     logger.info(f"Targeting Google Cloud Project: {GOOGLE_PROJECT_ID}, Region: {GOOGLE_REGION}")
     logger.info("Authentication relies on Application Default Credentials (ADC).")


# --- Application Specific Configuration ---
DEFAULT_TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "google.com")
logger.info(f"Default target domain set to: {DEFAULT_TARGET_DOMAIN}")

# --- AG2 LLM Configuration List ---

def get_ag2_config_list(model_id: str = "gemini-2.5-pro-preview-03-25") -> list:
    """
    Tạo danh sách cấu hình LLM cho AG2 để sử dụng model Gemini trên Vertex AI với ADC.
    """
    if not GOOGLE_PROJECT_ID or not GOOGLE_REGION:
         logger.error("Cannot generate AG2 config list without GOOGLE_PROJECT_ID and GOOGLE_REGION.")
         return [] # Trả về rỗng để tránh lỗi khi khởi tạo agent

    # Cấu hình cho Vertex AI Gemini sử dụng ADC
    # AG2 cần biết project và location để tạo request đúng endpoint.
    # ADC sẽ xử lý phần token xác thực.
    config_list_gemini = [
        {
            "model": model_id, # Model ID trên Vertex AI (ví dụ: gemini-1.5-flash-001)
            "api_type": "google",
            "project_id": GOOGLE_PROJECT_ID,
            "location": GOOGLE_REGION,
            # "api_key": None # Không cần API key khi dùng ADC
            # Có thể thêm các tham số khác như "temperature", "max_output_tokens", "safety_settings" nếu cần
            # "safety_settings": [
            #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            #     # ... các cài đặt an toàn khác
            # ]
        }
    ]
    logger.info(f"Generated AG2 config list for Vertex AI model: {model_id}")
    return config_list_gemini

# --- Xuất các biến cấu hình ---
logger.debug("Configuration loaded.")

# --- Thêm các hằng số hoặc cấu hình khác nếu cần ---

# --- Caching TTL settings (in seconds) ---
CACHE_TTL_WHOIS = 24 * 60 * 60      # 24 hours
CACHE_TTL_DNS = 2 * 60 * 60         # 2 hours
CACHE_TTL_HTTP_HEADERS = 60 * 60    # 1 hour