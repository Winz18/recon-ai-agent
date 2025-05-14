import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any, Annotated
from .tool_decorator import recon_tool

@recon_tool
def detect_technologies(
    url: Annotated[str, "URL of the website to analyze"],
    timeout: Annotated[int, "Request timeout in seconds"] = 10,
    user_agent: Annotated[Optional[str], "Custom user agent string"] = None,
    check_js: Annotated[bool, "Whether to analyze JavaScript files"] = False,
    follow_redirects: Annotated[bool, "Whether to follow HTTP redirects"] = True
) -> Dict[str, Any]:
    """
    Detect technologies used by a website based on HTTP headers, HTML content and other indicators.
    
    Args:
        url: URL of the website to analyze
        timeout: Request timeout in seconds
        user_agent: Custom user agent string
        check_js: Whether to analyze linked JavaScript files (more comprehensive but slower)
        follow_redirects: Whether to follow HTTP redirects
        
    Returns:
        Dictionary containing detected technologies by category
    """
    # Initialize results structure
    results = {
        "server": {},
        "cms": {},
        "javascript_frameworks": {},
        "analytics": {},
        "programming_languages": {},
        "web_frameworks": {},
        "headers": {},
        "other": {}
    }
    
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    # Set default User-Agent if none provided
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # Make the request
        response = requests.get(
            url, 
            headers=headers, 
            timeout=timeout,
            allow_redirects=follow_redirects
        )
        
        # Check if request was successful
        if response.status_code != 200:
            return {"error": f"Request failed with status code: {response.status_code}"}
        
        # Extract and analyze HTTP headers
        analyze_headers(response.headers, results)
        
        # Parse and analyze HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        analyze_html_content(soup, results)
        
        # Check for common JavaScript frameworks
        analyze_javascript(soup, results)
        
        # Optionally analyze linked JavaScript files (slower but more accurate)
        if check_js:
            analyze_js_files(soup, url, headers, timeout, results)
            
        # Clean up results by removing empty categories
        results = {k: v for k, v in results.items() if v}
        
        return results
        
    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Error detecting technologies: {str(e)}"}

def analyze_headers(headers, results):
    """Analyze HTTP headers for technology fingerprints"""
    
    # Map headers to their respective categories and technology identifiers
    header_tech_map = {
        "Server": {"category": "server", "name": "server"},
        "X-Powered-By": {"category": "programming_languages", "name": "powered_by"},
        "X-AspNet-Version": {"category": "web_frameworks", "name": "ASP.NET"},
        "X-Drupal-Cache": {"category": "cms", "name": "Drupal"},
        "X-Varnish": {"category": "server", "name": "Varnish"},
        "X-WP-Nonce": {"category": "cms", "name": "WordPress"},
        "X-Shopify-Stage": {"category": "cms", "name": "Shopify"},
        "X-Magento-Cache-Debug": {"category": "cms", "name": "Magento"},
        "X-Generator": {"category": "cms", "name": "generator"},
        "X-Joomla-Cache": {"category": "cms", "name": "Joomla"},
        "X-Litespeed-Cache": {"category": "server", "name": "LiteSpeed"},
        "CF-Cache-Status": {"category": "server", "name": "Cloudflare"},
        "Fastly-Debug-Digest": {"category": "server", "name": "Fastly"},
        "Set-Cookie": {"category": "other", "name": "cookies"},
    }
    
    # Store all headers for reference
    for header, value in headers.items():
        results["headers"][header] = value
    
    # Extract technology information from specific headers
    for header, value in headers.items():
        if header in header_tech_map:
            category = header_tech_map[header]["category"]
            name = header_tech_map[header]["name"]
            results[category][name] = value
    
    # Special cases
    if "Set-Cookie" in headers:
        cookies = headers["Set-Cookie"]
        if "PHPSESSID" in cookies:
            results["programming_languages"]["PHP"] = True
        if "JSESSIONID" in cookies:
            results["programming_languages"]["Java"] = True
        if "ASP.NET_SessionId" in cookies:
            results["web_frameworks"]["ASP.NET"] = True
        if "django" in cookies.lower():
            results["web_frameworks"]["Django"] = True
        if "laravel" in cookies.lower():
            results["web_frameworks"]["Laravel"] = True

def analyze_html_content(soup, results):
    """Analyze HTML content for technology fingerprints"""
    
    # Check meta tags
    for meta in soup.find_all("meta"):
        # Generator meta tag often reveals CMS
        if meta.get("name", "").lower() == "generator":
            content = meta.get("content", "").lower()
            results["cms"]["generator"] = content
            
            # Check for common CMS in generator tag
            cms_patterns = {
                "wordpress": "WordPress",
                "drupal": "Drupal",
                "joomla": "Joomla",
                "shopify": "Shopify",
                "wix": "Wix",
                "squarespace": "Squarespace",
                "ghost": "Ghost",
                "typo3": "TYPO3",
                "concrete": "Concrete CMS"
            }
            
            for pattern, cms_name in cms_patterns.items():
                if pattern in content:
                    results["cms"][cms_name] = True
    
    # Check for common CMS indicators in HTML
    if soup.select("link[href*=wp-content], script[src*=wp-content]"):
        results["cms"]["WordPress"] = True
        
    if soup.select("link[href*=drupal], script[src*=drupal]"):
        results["cms"]["Drupal"] = True
        
    if soup.find(class_=lambda c: c and "joomla" in c.lower() if c else False):
        results["cms"]["Joomla"] = True
    
    if soup.select("link[href*=magento], script[src*=magento]"):
        results["cms"]["Magento"] = True
        
    # Check for web framework indicators
    if soup.select("meta[name*=django]"):
        results["web_frameworks"]["Django"] = True
        
    if soup.select("meta[name*=rails]"):
        results["web_frameworks"]["Ruby on Rails"] = True
        
    if soup.select("link[href*=laravel], script[src*=laravel]"):
        results["web_frameworks"]["Laravel"] = True
    
    # Check for programming language indicators in comments or text
    html_str = str(soup).lower()
    if "<%@" in html_str or "<%=" in html_str:
        results["programming_languages"]["JSP"] = True
        
    if "<?php" in html_str:
        results["programming_languages"]["PHP"] = True
        
    if "<asp:" in html_str:
        results["programming_languages"]["ASP.NET"] = True
        
    # Analytics
    if "google-analytics.com" in html_str:
        results["analytics"]["Google Analytics"] = True
        
    if "gtag" in html_str:
        results["analytics"]["Google Tag Manager"] = True
        
    if "hotjar" in html_str:
        results["analytics"]["Hotjar"] = True
        
    if "matomo" in html_str or "piwik" in html_str:
        results["analytics"]["Matomo/Piwik"] = True

def analyze_javascript(soup, results):
    """Analyze JavaScript tags and references"""
    
    # Check for common JS frameworks
    js_framework_patterns = {
        "jquery": "jQuery",
        "react": "React",
        "vue.js": "Vue.js",
        "angular": "Angular",
        "backbone": "Backbone.js",
        "ember": "Ember.js",
        "knockout": "Knockout.js",
        "mootools": "MooTools",
        "dojo": "Dojo",
        "polymer": "Polymer",
        "bootstrap": "Bootstrap",
        "tailwind": "TailwindCSS",
        "bulma": "Bulma",
        "materialize": "Materialize CSS",
        "foundation": "Foundation"
    }
    
    # Check script tags
    for script in soup.find_all("script"):
        # Check src attribute for frameworks
        src = script.get("src", "").lower()
        if src:
            for pattern, framework in js_framework_patterns.items():
                if pattern in src:
                    results["javascript_frameworks"][framework] = True
                    
        # Check inline scripts
        if script.string:
            script_content = script.string.lower()
            for pattern, framework in js_framework_patterns.items():
                if pattern in script_content:
                    results["javascript_frameworks"][framework] = True
                
            # Additional checks for SPA frameworks
            if "react" in script_content and "createelement" in script_content:
                results["javascript_frameworks"]["React"] = True
                
            if "angular" in script_content and "module" in script_content:
                results["javascript_frameworks"]["Angular"] = True
                
            if "vue" in script_content and ("component" in script_content or "createapp" in script_content):
                results["javascript_frameworks"]["Vue.js"] = True
                
    # Check for CSS frameworks
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "").lower()
        for pattern, framework in js_framework_patterns.items():
            if pattern in href and framework.endswith("CSS"):
                results["javascript_frameworks"][framework] = True
                
    # Check if there's global window objects for frameworks
    html_str = str(soup).lower()
    # Look for common global objects
    if "jquery" in html_str or "$(" in html_str:
        results["javascript_frameworks"]["jQuery"] = True
        
    if "react" in html_str and "reactdom" in html_str:
        results["javascript_frameworks"]["React"] = True
        
    if "new vue" in html_str:
        results["javascript_frameworks"]["Vue.js"] = True

def analyze_js_files(soup, base_url, headers, timeout, results):
    """Analyze external JavaScript files for more clues"""
    # Limited implementation as full JS analysis can be complex
    # This function could be expanded for more comprehensive analysis
    js_files = []
    
    for script in soup.find_all("script", src=True):
        src = script["src"]
        # Handle relative URLs
        if src.startswith("//"):
            src = "https:" + src
        elif not src.startswith(("http://", "https://")):
            # Handle relative paths
            if src.startswith("/"):
                base = base_url.split("//")[0] + "//" + base_url.split("//")[1].split("/")[0]
                src = base + src
            else:
                # Simplistic approach - might not work for all cases
                base = base_url
                if not base.endswith("/"):
                    base += "/"
                src = base + src
                
        js_files.append(src)
    
    # Limit to first few files to prevent excessive requests
    for js_url in js_files[:3]:
        try:
            response = requests.get(js_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for framework signatures
                if "jquery" in content:
                    results["javascript_frameworks"]["jQuery"] = True
                    # Try to extract version
                    version_match = re.search(r'jquery v([\d.]+)', content)
                    if version_match:
                        results["javascript_frameworks"]["jQuery"] = f"v{version_match.group(1)}"
                
                if "react" in content and "reactdom" in content:
                    results["javascript_frameworks"]["React"] = True
                    
                if "vue" in content and ("definecomponent" in content or "createapp" in content):
                    results["javascript_frameworks"]["Vue.js"] = True
                    
                # Check for analytics
                if "google-analytics" in content or "gtag" in content:
                    results["analytics"]["Google Analytics"] = True
                    
                if "function gtag" in content:
                    results["analytics"]["Google Tag Manager"] = True
        
        except Exception:
            # Skip errors in JS analysis
            continue
