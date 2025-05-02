import requests
from typing import Annotated, Dict, Optional
from urllib.parse import urlparse

def get_http_headers(url: Annotated[str, "The URL to get HTTP headers from"]) -> Dict[str, str]:
    """
    Retrieves HTTP headers from a web server.
    
    Args:
        url: The URL to get HTTP headers from. If not starting with http, https will be prepended.
    
    Returns:
        A dictionary of HTTP response headers
    """
    # Make sure URL has scheme
    if not urlparse(url).scheme:
        url = f"https://{url}"
    
    try:
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        # Send HEAD request first (lighter than GET)
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        # If server doesn't support HEAD, try GET
        if response.status_code >= 400:
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Convert headers to dictionary (all keys to lowercase for consistency)
        result = {k.lower(): v for k, v in response.headers.items()}
        
        # Add status code and final URL (after redirects)
        result['status_code'] = str(response.status_code)
        result['url'] = response.url
        
        return result
    
    except Exception as e:
        return {"error": f"Failed to retrieve HTTP headers: {str(e)}"}

def extract_security_headers(headers: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Analyzes security headers from HTTP response.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        Dictionary with security analysis results
    """
    security_headers = {
        "analysis": {
            "missing_headers": [],
            "found_headers": {}
        }
    }
    
    # List of important security headers to check
    important_headers = [
        "strict-transport-security",
        "content-security-policy",
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "referrer-policy",
        "permissions-policy"
    ]
    
    for header in important_headers:
        if header in headers:
            security_headers["analysis"]["found_headers"][header] = headers[header]
        else:
            security_headers["analysis"]["missing_headers"].append(header)
    
    return security_headers