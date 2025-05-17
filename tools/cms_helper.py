# tools/cms_helper.py
import asyncio
from .cms_detector import detect_cms as detect_cms_async

def detect_cms_sync(url, deep_scan=False, timeout=10):
    """
    Synchronous wrapper for the asynchronous detect_cms function.
    
    Args:
        url: The URL of the website to scan
        deep_scan: Whether to perform a deeper scan for version information
        timeout: Connection timeout in seconds
        
    Returns:
        CMS detection results as dictionary
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            detect_cms_async(url, deep_scan, timeout)
        )
        return result
    finally:
        loop.close() 