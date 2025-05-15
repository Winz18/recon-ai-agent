import requests
from typing import Annotated, Dict, Optional
from urllib.parse import urlparse
from .tool_decorator import recon_tool
from config.settings import CACHE_TTL_HTTP_HEADERS

@recon_tool(
    cache_ttl_seconds=CACHE_TTL_HTTP_HEADERS,
    max_retries=2,
    retry_delay_seconds=2,
    retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout)
)
def get_http_headers(
    url: Annotated[str, "The URL to get HTTP headers from"],
    method: Annotated[str, "HTTP method to use (HEAD, GET)"] = "AUTO",
    timeout: Annotated[int, "Request timeout in seconds"] = 10,
    user_agent: Annotated[str, "Custom user agent string"] = None
) -> Dict[str, str]:
    """
    Retrieves HTTP headers from a web server.
    
    Args:
        url: The URL to get HTTP headers from. If not starting with http, https will be prepended.
        method: HTTP method to use (AUTO, HEAD, GET). AUTO will try HEAD first, then GET if needed.
        timeout: Request timeout in seconds.
        user_agent: Custom user agent string to use for the request.
    
    Returns:
        A dictionary of HTTP response headers
    """
    # Make sure URL has scheme
    if not urlparse(url).scheme:
        url = f"https://{url}"
    
    try:
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        method = method.upper() if method else "AUTO"
        
        if method == "HEAD" or method == "AUTO":
            try:
                # Send HEAD request first (lighter than GET)
                response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
                
                # If method is HEAD or if AUTO and HEAD worked well, return the result
                if method == "HEAD" or (method == "AUTO" and response.status_code < 400):
                    # Convert headers to dictionary (all keys to lowercase for consistency)
                    result = {k.lower(): v for k, v in response.headers.items()}
                    
                    # Add status code and final URL (after redirects)
                    result['status_code'] = str(response.status_code)
                    result['url'] = response.url
                    return result
            except requests.exceptions.RequestException as e:
                if method == "HEAD":
                    return {"error": f"HEAD request failed: {str(e)}"}
                # If AUTO, we'll continue with GET
        
        if method == "GET" or method == "AUTO":
            # Try GET if HEAD failed or was not selected
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            # Convert headers to dictionary (all keys to lowercase for consistency)
            result = {k.lower(): v for k, v in response.headers.items()}
            
            # Add status code and final URL (after redirects)
            result['status_code'] = str(response.status_code)
            result['url'] = response.url
            
            return result
        
        return {"error": f"Invalid method specified: {method}. Use AUTO, HEAD, or GET."}
    
    except requests.exceptions.ConnectionError:
        return {"error": f"Connection error when connecting to {url}. The server may be down or unreachable."}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout} seconds when connecting to {url}."}
    except requests.exceptions.TooManyRedirects:
        return {"error": f"Too many redirects when connecting to {url}. Check if the URL is correct."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to retrieve HTTP headers: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@recon_tool
def extract_security_headers(
    url: Annotated[str, "The URL to fetch HTTP headers from"],
    include_recommendations: Annotated[bool, "Include security recommendations"] = True
) -> Dict[str, Dict[str, str]]:
    """
    Fetches HTTP headers from a URL and analyzes security headers.

    Args:
        url: The URL to fetch HTTP headers from.
        include_recommendations: Whether to include security recommendations in the output.

    Returns:
        Dictionary with security analysis results.
    """
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    try:
        # Fetch headers using a HEAD request
        response = requests.head(url, timeout=10, allow_redirects=True)
        headers = {k.lower(): v for k, v in response.headers.items()}
    except requests.RequestException as e:
        return {"error": f"Failed to fetch headers: {str(e)}"}

    # Analyze headers
    security_headers = {
        "analysis": {
            "missing_headers": [],
            "found_headers": {},
            "score": 0,
            "max_score": 0
        }
    }

    if include_recommendations:
        security_headers["recommendations"] = {}

    # List of important security headers to check with their weights and recommendations
    important_headers = [
        {
            "name": "strict-transport-security",
            "weight": 3,
            "recommendation": "Add 'Strict-Transport-Security' header with a long max-age value (e.g., max-age=31536000)."
        },
        {
            "name": "content-security-policy",
            "weight": 3,
            "recommendation": "Implement a Content Security Policy to prevent XSS and data injection attacks."
        },
        {
            "name": "x-content-type-options",
            "weight": 2,
            "recommendation": "Add 'X-Content-Type-Options: nosniff' to prevent MIME type sniffing."
        },
        {
            "name": "x-frame-options",
            "weight": 2,
            "recommendation": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' to prevent clickjacking."
        },
        {
            "name": "x-xss-protection",
            "weight": 2,
            "recommendation": "Add 'X-XSS-Protection: 1; mode=block' to enable browser's XSS filtering."
        },
        {
            "name": "referrer-policy",
            "weight": 1,
            "recommendation": "Add 'Referrer-Policy' header to control how much referrer information is included with requests."
        },
        {
            "name": "permissions-policy",
            "weight": 1,
            "recommendation": "Use 'Permissions-Policy' header to control which browser features and APIs can be used."
        },
        {
            "name": "cross-origin-embedder-policy",
            "weight": 1,
            "recommendation": "Add 'Cross-Origin-Embedder-Policy' header for resource isolation."
        },
        {
            "name": "cross-origin-opener-policy",
            "weight": 1,
            "recommendation": "Add 'Cross-Origin-Opener-Policy' header to control window references."
        },
        {
            "name": "cross-origin-resource-policy",
            "weight": 1,
            "recommendation": "Add 'Cross-Origin-Resource-Policy' header to prevent resource access from other origins."
        }
    ]
    
    # Analyze headers
    for header in important_headers:
        name = header["name"].lower()
        if name in headers:
            security_headers["analysis"]["found_headers"][name] = headers[name]
            security_headers["analysis"]["score"] += header["weight"]
        else:
            security_headers["analysis"]["missing_headers"].append(name)
            if include_recommendations:
                security_headers["recommendations"][name] = header["recommendation"]

    security_headers["analysis"]["max_score"] = sum(h["weight"] for h in important_headers)

    return security_headers