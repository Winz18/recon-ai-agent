import httpx
import json
import logging
from typing import Dict, List, Any, Set, Optional
from urllib.parse import urlparse

from .tool_decorator import recon_tool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cors_checker")

@recon_tool
async def check_cors_config(url: str, test_origins: List[str] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Checks for Cross-Origin Resource Sharing (CORS) misconfigurations on a web server.
    
    Args:
        url: The URL to check for CORS misconfigurations
        test_origins: Custom origins to test (defaults to a predefined list)
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary with CORS configuration analysis
    """
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed_url = urlparse(url)
    target_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Default test origins if not provided
    if not test_origins:
        test_origins = [
            # Standard malicious cases
            'null',                                  # Null origin
            'https://evil.com',                      # Classic evil domain
            f"{target_origin}.evil.com",              # Target origin prefix
            f"evil{target_origin}",                   # Target origin suffix
            f"evil-{parsed_url.netloc}",              # Domain with hyphen prefix
            f"{parsed_url.netloc.split('.')[0]}.evil.com",  # Subdomain match
            
            # Wildcards and bypasses
            f"https://{parsed_url.netloc}evil.com",    # No dot after domain
            f"https://subdomain.{parsed_url.netloc}",  # Subdomain of legitimate domain
            f"https://{parsed_url.netloc.split('.')[0]}-evil.com",  # Hyphenated
            target_origin.replace('https://', 'http://'),  # HTTP instead of HTTPS
        ]
    
    results = {
        'target': url,
        'target_origin': target_origin,
        'has_cors_headers': False,
        'access_control_allow_origin': None,
        'access_control_allow_credentials': None,
        'access_control_allow_methods': None,
        'access_control_allow_headers': None,
        'is_vulnerable': False,
        'vulnerabilities': [],
        'normal_response_headers': {},
        'test_results': [],
        'recommendations': []
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # First request without Origin header to get normal behavior
            normal_resp = await client.get(url)
            results['normal_response_headers'] = dict(normal_resp.headers)
            
            # Check if CORS headers are present
            cors_headers = _extract_cors_headers(normal_resp.headers)
            results.update(cors_headers)
            
            # Test with different Origin headers
            for origin in test_origins:
                result = await _test_origin(client, url, origin, target_origin, results['access_control_allow_credentials'])
                
                if result['is_vulnerable']:
                    results['is_vulnerable'] = True
                    results['vulnerabilities'].append({
                        'type': result['vulnerability_type'],
                        'origin': origin,
                        'details': result['details']
                    })
                
                results['test_results'].append(result)
            
            # Generate recommendations
            results['recommendations'] = _generate_recommendations(results)
    
    except Exception as e:
        logger.error(f"Error checking CORS configuration: {str(e)}")
        results['error'] = str(e)
    
    return results

def _extract_cors_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """Extract and analyze CORS headers from response"""
    cors_headers = {
        'has_cors_headers': False,
        'access_control_allow_origin': None,
        'access_control_allow_credentials': None,
        'access_control_allow_methods': None,
        'access_control_allow_headers': None,
    }
    
    # Convert header names to lowercase for case-insensitive matching
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    # Check for CORS headers
    if 'access-control-allow-origin' in headers_lower:
        cors_headers['has_cors_headers'] = True
        cors_headers['access_control_allow_origin'] = headers_lower['access-control-allow-origin']
    
    if 'access-control-allow-credentials' in headers_lower:
        cors_headers['has_cors_headers'] = True
        acac = headers_lower['access-control-allow-credentials'].lower()
        cors_headers['access_control_allow_credentials'] = acac == 'true'
    
    if 'access-control-allow-methods' in headers_lower:
        cors_headers['has_cors_headers'] = True
        cors_headers['access_control_allow_methods'] = headers_lower['access-control-allow-methods'].split(',')
        cors_headers['access_control_allow_methods'] = [m.strip() for m in cors_headers['access_control_allow_methods']]
    
    if 'access-control-allow-headers' in headers_lower:
        cors_headers['has_cors_headers'] = True
        cors_headers['access_control_allow_headers'] = headers_lower['access-control-allow-headers'].split(',')
        cors_headers['access_control_allow_headers'] = [h.strip() for h in cors_headers['access_control_allow_headers']]
    
    return cors_headers

async def _test_origin(client: httpx.AsyncClient, url: str, test_origin: str, 
                      target_origin: str, allows_credentials: bool) -> Dict[str, Any]:
    """Test a specific origin for CORS misconfigurations"""
    result = {
        'origin': test_origin,
        'allowed': False,
        'is_vulnerable': False,
        'vulnerability_type': None,
        'headers': {},
        'details': None
    }
    
    # Make request with test origin
    try:
        headers = {
            'Origin': test_origin,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        resp = await client.get(url, headers=headers)
        cors_headers = _extract_cors_headers(resp.headers)
        result['headers'] = dict(resp.headers)
        
        # Process response
        if not cors_headers['has_cors_headers']:
            return result
        
        acao = cors_headers['access_control_allow_origin']
        if not acao:
            return result
        
        # Check if origin is allowed
        if acao == '*' or acao == test_origin:
            result['allowed'] = True
        
        # Detect vulnerabilities
        if acao == '*' and allows_credentials:
            result['is_vulnerable'] = True
            result['vulnerability_type'] = 'wildcard_with_credentials'
            result['details'] = "Allows wildcard origin (*) with credentials, which is rejected by browsers but indicates a dangerous misconfiguration"
        
        elif acao == test_origin and test_origin != target_origin:
            result['is_vulnerable'] = True
            
            if test_origin == 'null':
                result['vulnerability_type'] = 'null_origin_allowed'
                result['details'] = "Allows 'null' origin which can be spoofed in several ways"
            
            elif test_origin.endswith(target_origin) and test_origin != target_origin:
                result['vulnerability_type'] = 'origin_suffix_match'
                result['details'] = f"Validates using suffix matching (allowed {test_origin})"
            
            elif target_origin in test_origin and test_origin != target_origin:
                result['vulnerability_type'] = 'origin_substring_match'
                result['details'] = f"Validates using substring matching (allowed {test_origin})"
            
            elif allows_credentials:
                result['vulnerability_type'] = 'arbitrary_origin_with_credentials'
                result['details'] = f"Allows arbitrary origin ({test_origin}) with credentials"
            
            else:
                result['vulnerability_type'] = 'arbitrary_origin'
                result['details'] = f"Allows arbitrary origin ({test_origin})"
                
        elif acao.startswith(test_origin):
            result['is_vulnerable'] = True
            result['vulnerability_type'] = 'dynamic_acao'
            result['details'] = f"Dynamic ACAO reflects origin ({acao})"
                
    except Exception as e:
        logger.error(f"Error testing origin {test_origin}: {str(e)}")
        result['error'] = str(e)
    
    return result

def _generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on CORS configuration analysis"""
    recommendations = []
    
    # If no CORS headers found
    if not results['has_cors_headers']:
        recommendations.append("No CORS headers detected. If cross-origin requests are needed, implement proper CORS policies")
        return recommendations
    
    # If vulnerable, generate specific recommendations
    if results['is_vulnerable']:
        for vulnerability in results['vulnerabilities']:
            if vulnerability['type'] == 'wildcard_with_credentials':
                recommendations.append("Remove 'Access-Control-Allow-Credentials: true' when using wildcard origins (*)")
                recommendations.append("Explicitly enumerate allowed origins instead of using wildcards")
            
            elif vulnerability['type'] == 'null_origin_allowed':
                recommendations.append("Remove 'null' from allowed origins as it can be spoofed in various ways")
            
            elif vulnerability['type'] in ['origin_suffix_match', 'origin_substring_match', 'dynamic_acao']:
                recommendations.append("Use exact string matching for origin validation, not substring matching")
                recommendations.append("Maintain a whitelist of explicitly allowed origins")
            
            elif vulnerability['type'] == 'arbitrary_origin_with_credentials':
                recommendations.append("Do not allow arbitrary origins with credentials as this is a severe security risk")
                recommendations.append("Restrict allowed origins to specific trusted domains")
                
    # General CORS security recommendations
    if results['access_control_allow_origin'] == '*':
        recommendations.append("Restrict the 'Access-Control-Allow-Origin' header to specific trusted domains instead of using wildcard (*)")
    
    if results['access_control_allow_credentials']:
        recommendations.append("Use 'Access-Control-Allow-Credentials: true' only with specific origins, never with wildcards")
    
    if results['access_control_allow_methods'] and any(m in results['access_control_allow_methods'] for m in ['PUT', 'DELETE', 'PATCH']):
        recommendations.append("Restrict allowed HTTP methods to only those required by your application")
    
    # If no specific recommendations were added
    if not recommendations:
        recommendations.append("CORS configuration appears secure. Continue to monitor for changes")
    
    return recommendations

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_cors():
        results = await check_cors_config("example.com")
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_cors()) 