# tools/waf_helper.py
import asyncio
from .waf_detector import detect_waf as detect_waf_async

def detect_waf_sync(url, timeout=10, user_agent=None, test_payloads=True):
    """
    Synchronous wrapper for the asynchronous detect_waf function.
    
    Args:
        url: The URL to check for WAF protection
        timeout: Connection timeout in seconds
        user_agent: Custom User-Agent string to use
        test_payloads: Whether to use test payloads to trigger WAF responses
        
    Returns:
        WAF detection results as dictionary
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            detect_waf_async(url, timeout, user_agent, test_payloads)
        )
        return result
    finally:
        loop.close() 