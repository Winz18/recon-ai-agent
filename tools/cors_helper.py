# tools/cors_helper.py
import asyncio
from .cors_checker import check_cors_config as check_cors_config_async

def check_cors_config_sync(url, test_origins=None, timeout=10):
    """
    Synchronous wrapper for the asynchronous check_cors_config function.
    
    Args:
        url: The URL to check for CORS misconfigurations
        test_origins: Custom origins to test (defaults to a predefined list)
        timeout: Connection timeout in seconds
        
    Returns:
        CORS configuration analysis results as dictionary
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            check_cors_config_async(url, test_origins, timeout)
        )
        return result
    finally:
        loop.close() 