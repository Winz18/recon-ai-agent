import asyncio
import logging
from typing import Dict, Any
from .endpoint_crawler import crawl_endpoints as _async_crawl_endpoints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def crawl_endpoints(url: str, depth: int = 1, output_format: str = "json", 
                   use_wordlist: bool = True, use_wayback: bool = True, 
                   analyze_js: bool = True, max_js_files: int = 10, 
                   timeout: int = 10) -> Dict[str, Any]:
    """
    Synchronous wrapper for the async endpoint crawler to be used by the WebAppReconAgent.
    
    Args:
        url: The URL of the website to crawl
        depth: The depth of crawling (number of levels to follow links)
        output_format: The format for output data (json or simple)
        use_wordlist: Whether to try common endpoint paths
        use_wayback: Whether to query Wayback Machine for historical URLs
        analyze_js: Whether to analyze JavaScript files for endpoint paths
        max_js_files: Maximum number of JavaScript files to analyze
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with discovered endpoints
    """
    try:
        # Get or create an event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Call the async function with the converted parameters
        result = loop.run_until_complete(
            _async_crawl_endpoints(
                url=url,
                depth=depth,
                use_wordlist=use_wordlist,
                use_wayback=use_wayback,
                analyze_js=analyze_js,
                max_js_files=max_js_files,
                timeout=timeout,
                output_format=output_format
            )
        )
        
        return result
    except Exception as e:
        # Log the error but return a graceful response
        logging.error(f"Error crawling endpoints for {url}: {str(e)}")
        
        # Return a minimal valid response structure
        return {
            "target_url": url,
            "discovered_endpoints_count": 0,
            "endpoints_by_method": {
                "wordlist": [],
                "wayback": [],
                "js_analysis": [],
                "internal_links": [],
                "robots_sitemap": [],
            },
            "all_discovered_endpoints": [],
            "errors": [f"Crawler error: {str(e)}"]
        } 