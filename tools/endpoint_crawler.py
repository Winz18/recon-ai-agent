import asyncio
import json
import re
from typing import Dict, List, Set, Optional, Any, Annotated
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .tool_decorator import recon_tool

# Common endpoints/paths to check for during wordlist discovery
COMMON_WORDLIST = [
    "api", "admin", "login", "dashboard", "app", "main", "index", "robots.txt", "sitemap.xml",
    "config", "settings", "backup", "test", "dev", "staging", "prod", "user", "users",
    "account", "profile", "static", "assets", "js", "css", "img", "images", "files",
    "uploads", "downloads", "docs", "help", "support", "contact", "about", "blog",
    "news", "events", "careers", "jobs", "status", "health", "version", "api/v1", "api/v2",
    "swagger", "graphql", ".git", ".env", "wp-admin", "wp-login", "wp-content", "admin/login", 
    "administrator", "phpmyadmin", "phpinfo", "server-status", "server-info", "cpanel", "webmail"
]

@recon_tool
async def crawl_endpoints(
    url: Annotated[str, "URL of the website to crawl"],
    depth: Annotated[int, "Maximum depth for crawling (levels to follow links)"] = 1,
    use_wordlist: Annotated[bool, "Whether to use a common wordlist to discover endpoints"] = True,
    use_wayback: Annotated[bool, "Whether to query Wayback Machine for historical URLs"] = True,
    analyze_js: Annotated[bool, "Whether to analyze JavaScript files for endpoints"] = True,
    max_js_files: Annotated[int, "Maximum number of JavaScript files to analyze"] = 10,
    timeout: Annotated[int, "Request timeout in seconds"] = 10,
    output_format: Annotated[str, "Format for the output data (json or simple)"] = "json"
) -> Dict[str, Any]:
    """
    Crawls a website to discover accessible endpoints using various methods.
    
    Args:
        url: URL of the website to crawl
        depth: Maximum depth for internal link crawling (0 for homepage only)
        use_wordlist: Whether to try common endpoint paths
        use_wayback: Whether to query Wayback Machine for historical URLs
        analyze_js: Whether to analyze JavaScript files for endpoint paths
        max_js_files: Maximum number of JavaScript files to analyze
        timeout: Request timeout in seconds
        output_format: Output format (json or simple)
        
    Returns:
        Dictionary containing discovered endpoints categorized by discovery method
    """
    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    discovered_endpoints: Set[str] = set()
    results: Dict[str, List[str]] = {
        "wordlist": [],
        "wayback": [],
        "js_analysis": [],
        "internal_links": [],
        "robots_sitemap": [],
    }
    errors: List[str] = []
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # 1. Check robots.txt and sitemap.xml
        try:
            robots_url = urljoin(url, "/robots.txt")
            sitemap_url = urljoin(url, "/sitemap.xml")
            
            robots_resp = await client.get(robots_url)
            if robots_resp.status_code == 200:
                discovered_endpoints.add(robots_url)
                results["robots_sitemap"].append(robots_url)
                # Parse robots.txt for sitemaps and disallowed paths
                for line in robots_resp.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_path = line.split(":", 1)[1].strip()
                        sm_url = urljoin(url, sitemap_path)
                        await _check_url(client, sm_url, discovered_endpoints, results["robots_sitemap"])
                        await _process_sitemap(client, sm_url, discovered_endpoints, results["robots_sitemap"], url)
                    elif line.lower().startswith("disallow:"):
                        disallow_path = line.split(":", 1)[1].strip()
                        if disallow_path:
                            disallow_url = urljoin(url, disallow_path)
                            await _check_url(client, disallow_url, discovered_endpoints, results["robots_sitemap"])
            
            sitemap_resp = await client.get(sitemap_url)
            if sitemap_resp.status_code == 200:
                discovered_endpoints.add(sitemap_url)
                results["robots_sitemap"].append(sitemap_url)
                await _process_sitemap(client, sitemap_url, discovered_endpoints, results["robots_sitemap"], url)
                
        except httpx.RequestError as e:
            errors.append(f"Error fetching robots.txt/sitemap.xml: {str(e)}")
        
        # 2. Use wordlist-based discovery
        if use_wordlist:
            wordlist_tasks = []
            for path in COMMON_WORDLIST:
                full_url = urljoin(url, path)
                wordlist_tasks.append(_check_url(client, full_url, discovered_endpoints, results["wordlist"]))
            await asyncio.gather(*wordlist_tasks)
        
        # 3. Query Wayback Machine
        if use_wayback:
            try:
                wayback_url = f"https://web.archive.org/cdx/search/cdx?url={urlparse(url).netloc}/*&output=json&fl=original&collapse=urlkey"
                response = await client.get(wayback_url)
                if response.status_code == 200:
                    try:
                        wayback_data = response.json()
                        if wayback_data and len(wayback_data) > 1:  # Skip header row
                            for item_list in wayback_data[1:]:
                                if item_list and isinstance(item_list, list) and len(item_list) > 0:
                                    original_url = item_list[0]
                                    parsed_original_url = urlparse(original_url)
                                    parsed_target_url = urlparse(url)
                                    if parsed_original_url.netloc == parsed_target_url.netloc:
                                        await _check_url(client, original_url, discovered_endpoints, results["wayback"])
                    except ValueError as e:
                        errors.append(f"Error parsing Wayback Machine JSON: {str(e)}")
            except httpx.RequestError as e:
                errors.append(f"Error querying Wayback Machine: {str(e)}")
        
        # 4. Crawl internal links and analyze JS
        if depth > 0 or analyze_js:
            await _crawl_and_analyze_js(
                client, url, discovered_endpoints, results, 
                errors, max_js_files, analyze_js, depth, 0, url
            )
    
    # Prepare final results
    final_results = {
        "target_url": url,
        "discovered_endpoints_count": len(discovered_endpoints),
        "endpoints_by_method": results,
    }
    
    # Format according to output preference
    if output_format == "simple":
        final_results = {
            "target_url": url,
            "discovered_endpoints": sorted(list(discovered_endpoints))
        }
    else:
        final_results["all_discovered_endpoints"] = sorted(list(discovered_endpoints))
        
    if errors:
        final_results["errors"] = errors
    
    return final_results

async def _process_sitemap(client: httpx.AsyncClient, sitemap_url: str, discovered_endpoints: Set[str], 
                           result_list: List[str], base_url: str):
    """Process a sitemap file to extract URLs for checking."""
    try:
        sitemap_resp = await client.get(sitemap_url)
        if sitemap_resp.status_code == 200:
            # Try to parse with xml parser first, fall back to html.parser if not available
            try:
                soup = BeautifulSoup(sitemap_resp.text, "xml")
            except Exception as e:
                # Fallback to html.parser which is always available
                soup = BeautifulSoup(sitemap_resp.text, "html.parser")
                
            # Find URLs in sitemap - look for both XML and HTML formats
            # For XML format (standard sitemaps)
            loc_tags = soup.find_all("loc")
            # For HTML format or non-standard formats
            if not loc_tags:
                # Try to extract URLs with regex as a last resort
                import re
                urls = re.findall(r'<loc>(.*?)</loc>', sitemap_resp.text)
                for url in urls:
                    if url:
                        await _check_url(client, url, discovered_endpoints, result_list)
                return
                
            for loc in loc_tags:
                if loc.text:
                    url = loc.text
                    await _check_url(client, url, discovered_endpoints, result_list)
    except httpx.RequestError:
        pass  # Error already handled in the calling function
    except Exception as e:
        # Log the error but continue execution
        print(f"Error processing sitemap {sitemap_url}: {str(e)}")
        pass

async def _check_url(client: httpx.AsyncClient, url: str, discovered_set: Set[str], 
                    result_list: List[str], method: str = "HEAD"):
    """Check if a URL is accessible and add to results if it is."""
    try:
        if method == "HEAD":
            response = await client.head(url)
        else:  # GET
            response = await client.get(url)
            
        # Consider 2xx or 3xx status codes as valid endpoints
        if 200 <= response.status_code < 400:
            if url not in discovered_set:
                discovered_set.add(url)
                result_list.append(url)
            return True
    except httpx.RequestError:
        pass  # Ignore connection errors, timeouts, etc.
    except Exception:
        pass
    return False

async def _crawl_and_analyze_js(client: httpx.AsyncClient, current_url: str, 
                               discovered_endpoints: Set[str], results: Dict[str, List[str]], 
                               errors: List[str], max_js_files: int, perform_js_analysis: bool,
                               max_depth: int, current_depth: int, base_target_url: str):
    """Recursively crawl pages, extract links, and analyze JS files for endpoints."""
    if current_depth > max_depth:
        return

    # Skip URLs with common file extensions that aren't HTML
    parsed_url = urlparse(current_url)
    if any(parsed_url.path.lower().endswith(ext) for ext in ['.css', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp4']):
        return

    try:
        # Use a specific user-agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = await client.get(current_url, headers=headers)
        
        # Handle redirects
        if 300 <= response.status_code < 400 and "location" in response.headers:
            redirect_url = urljoin(current_url, response.headers["location"])
            parsed_redirect = urlparse(redirect_url)
            # Only follow redirects to the same domain
            if parsed_redirect.netloc == urlparse(base_target_url).netloc:
                if redirect_url not in discovered_endpoints:
                    discovered_endpoints.add(redirect_url)
                    results["internal_links"].append(redirect_url)
                    # Follow the redirect
                    await _crawl_and_analyze_js(
                        client, redirect_url, discovered_endpoints, results,
                        errors, max_js_files, perform_js_analysis, 
                        max_depth, current_depth, base_target_url
                    )
            return
        
        if response.status_code != 200:
            return
        
        # Check content type to ensure we're dealing with HTML
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower() and "application/xhtml" not in content_type.lower():
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract metadata for API endpoints (often in meta tags or comments)
        meta_api_locations = soup.find_all("meta", {"name": ["api-base", "api-root", "api-endpoint"]})
        for meta in meta_api_locations:
            if "content" in meta.attrs:
                api_url = urljoin(current_url, meta["content"])
                if urlparse(api_url).netloc == urlparse(base_target_url).netloc and api_url not in discovered_endpoints:
                    discovered_endpoints.add(api_url)
                    results["js_analysis"].append(api_url)
        
        # Extract AJAX/fetch/axios calls from inline scripts
        if perform_js_analysis:
            for script in soup.find_all("script"):
                if script.string:  # Only process if the script has content
                    await _analyze_js_content(
                        script.string, current_url, discovered_endpoints, 
                        results["js_analysis"], errors, base_target_url
                    )
        
        # Extract and analyze external JS files
        if perform_js_analysis:
            js_urls_found = set()
            
            # Find all script tags with src attribute
            for script_tag in soup.find_all("script", src=True):
                js_url = urljoin(current_url, script_tag["src"])
                if urlparse(js_url).netloc == urlparse(base_target_url).netloc:
                    js_urls_found.add(js_url)
            
            # Find additional JS files in link tags (sometimes used for preloading)
            for link_tag in soup.find_all("link", {"rel": "preload", "as": "script"}):
                if "href" in link_tag.attrs:
                    js_url = urljoin(current_url, link_tag["href"])
                    if urlparse(js_url).netloc == urlparse(base_target_url).netloc:
                        js_urls_found.add(js_url)
            
            # Priority for app.js, main.js, index.js, bundle.js files which often contain routes
            priority_js = []
            normal_js = []
            
            for js_url in js_urls_found:
                js_filename = urlparse(js_url).path.lower()
                if any(pattern in js_filename for pattern in [
                    '/app.js', '/main.js', '/index.js', '/bundle.js', 
                    '/router', '/routes', '/api', '/endpoints', '/config'
                ]):
                    priority_js.append(js_url)
                else:
                    normal_js.append(js_url)
            
            # Sort by priority and limit to max_js_files
            sorted_js_urls = priority_js + normal_js
            
            js_analysis_tasks = []
            for i, js_url in enumerate(sorted_js_urls[:max_js_files]):  # Limit to max_js_files
                js_analysis_tasks.append(_analyze_single_js(
                    client, js_url, discovered_endpoints, 
                    results["js_analysis"], errors, base_target_url
                ))
            
            if js_analysis_tasks:
                await asyncio.gather(*js_analysis_tasks)

        # Extract and follow internal links if not at max depth
        if current_depth < max_depth:
            internal_links_to_crawl = set()
            
            # Process regular links
            for link_tag in soup.find_all("a", href=True):
                href = link_tag["href"]
                # Skip anchor links and javascript: links
                if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                    continue
                    
                abs_url = urljoin(current_url, href)
                parsed_abs = urlparse(abs_url)
                
                # Skip common file extensions that don't contain valuable endpoint info
                if any(parsed_abs.path.lower().endswith(ext) for ext in [
                    '.css', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp4', '.mp3',
                    '.wav', '.avi', '.mov', '.wmv', '.flv', '.woff', '.ttf', '.eot', '.svg'
                ]):
                    continue
                
                # Only consider internal URLs on the same domain
                if parsed_abs.netloc == urlparse(base_target_url).netloc:
                    # Normalize URL by removing fragments and default queries
                    clean_url = f"{parsed_abs.scheme}://{parsed_abs.netloc}{parsed_abs.path}"
                    if parsed_abs.query:
                        clean_url += f"?{parsed_abs.query}"
                    
                    if clean_url not in discovered_endpoints:
                        discovered_endpoints.add(clean_url)
                        results["internal_links"].append(clean_url)
                        internal_links_to_crawl.add(clean_url)
            
            # Also check other potential navigation elements
            nav_elements = soup.select('nav a, .menu a, .navigation a, .navbar a, .sidebar a, header a, footer a')
            for nav_link in nav_elements:
                if nav_link.has_attr('href'):
                    href = nav_link['href']
                    if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                        continue
                        
                    abs_url = urljoin(current_url, href)
                    parsed_abs = urlparse(abs_url)
                    
                    if parsed_abs.netloc == urlparse(base_target_url).netloc:
                        clean_url = f"{parsed_abs.scheme}://{parsed_abs.netloc}{parsed_abs.path}"
                        if parsed_abs.query:
                            clean_url += f"?{parsed_abs.query}"
                        
                        if clean_url not in discovered_endpoints:
                            discovered_endpoints.add(clean_url)
                            results["internal_links"].append(clean_url)
                            internal_links_to_crawl.add(clean_url)
            
            # Prioritize interesting URLs for crawling (admin, dashboard, api, etc.)
            priority_links = []
            normal_links = []
            
            interesting_patterns = ['admin', 'dashboard', 'console', 'api', 'portal', 'account', 'profile',
                                   'settings', 'config', 'manage', 'login', 'user', 'control']
            
            for link in internal_links_to_crawl:
                if any(pattern in link.lower() for pattern in interesting_patterns):
                    priority_links.append(link)
                else:
                    normal_links.append(link)
            
            # Sort by priority and limit number of concurrent tasks to avoid overloading
            sorted_links = priority_links + normal_links
            max_concurrent = min(25, len(sorted_links))  # Limit concurrent requests
            
            crawl_tasks = []
            for link_to_crawl in sorted_links[:max_concurrent]:
                crawl_tasks.append(
                    _crawl_and_analyze_js(
                        client, link_to_crawl, discovered_endpoints, results, 
                        errors, max_js_files, perform_js_analysis, 
                        max_depth, current_depth + 1, base_target_url
                    )
                )
            
            if crawl_tasks:
                await asyncio.gather(*crawl_tasks)

    except httpx.RequestError as e:
        errors.append(f"Request error crawling {current_url}: {str(e)}")
    except Exception as e:
        errors.append(f"Error crawling or analyzing JS at {current_url}: {str(e)}")

async def _analyze_js_content(js_content: str, source_url: str, discovered_endpoints: Set[str],
                             result_list: List[str], errors: List[str], base_target_url: str):
    """Analyze JavaScript content (inline or external) for potential endpoints."""
    try:
        # Find potential endpoint paths in JavaScript
        potential_paths = []
        
        # URL patterns in fetch/XHR calls 
        # Match fetch('URL'), axios.get('URL'), $.ajax({url: 'URL'}), etc.
        potential_paths.extend(re.findall(r'(?:fetch|get|post|put|delete|ajax)\s*\(\s*[\'\"]([^\'\"]+)[\'\" ]', js_content))
        potential_paths.extend(re.findall(r'url\s*:\s*[\'\"]([^\'\"]+)[\'\" ]', js_content))
        
        # Absolute paths
        potential_paths.extend(re.findall(r'[\'\"](/[^\'\"\\s?#]+(?:/[^\'\"\\s?#]+)*)[\'\" ]', js_content))
        
        # API paths - expanded to catch more variations
        potential_paths.extend(re.findall(r'[\'\"](?:api|v1|v2|v3|rest|graphql|service)/[^\'\"\\s?#]+[\'\" ]', js_content))
        
        # Relative paths that might be endpoints
        potential_paths.extend(re.findall(r'[\'\"](?:../)?(?:data|endpoints|services|controllers)/[^\'\"\\s?#]+[\'\" ]', js_content))
        
        # Route definitions in modern JS frameworks
        potential_paths.extend(re.findall(r'path\s*:\s*[\'\"]([^\'\"]+)[\'\" ]', js_content))
        potential_paths.extend(re.findall(r'route\s*:\s*[\'\"]([^\'\"]+)[\'\" ]', js_content))
        
        # Process discovered paths
        for path in potential_paths:
            path = path.strip("'\" ")
            
            # Skip empty paths
            if not path or len(path) < 2:
                continue
                
            # Skip URLs with specific patterns that are likely not endpoints
            if any(pattern in path.lower() for pattern in [
                '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.woff', '.ttf', 'jquery', 'bootstrap',
                'font-awesome', 'googleapis.com', 'gstatic.com', 'facebook.com', 'twitter.com'
            ]):
                continue
            
            # Convert to absolute URL
            if path.startswith("//"): 
                endpoint = "http:" + path
            elif path.startswith("/"):
                endpoint = urljoin(base_target_url, path)
            elif path.startswith(("http://", "https://")):
                if urlparse(path).netloc == urlparse(base_target_url).netloc:
                    endpoint = path
                else:
                    continue  # Skip external domains
            else:  # Relative path
                endpoint = urljoin(source_url, path)
            
            # Normalize endpoint URL
            parsed_endpoint = urlparse(endpoint)
            normalized_endpoint = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}{parsed_endpoint.path}"
            if parsed_endpoint.query:
                normalized_endpoint += f"?{parsed_endpoint.query}"
            
            # Add to discovered endpoints
            if urlparse(normalized_endpoint).netloc == urlparse(base_target_url).netloc and normalized_endpoint not in discovered_endpoints:
                discovered_endpoints.add(normalized_endpoint)
                result_list.append(normalized_endpoint)
    
    except Exception as e:
        errors.append(f"Error analyzing JS content from {source_url}: {str(e)}")

async def _analyze_single_js(client: httpx.AsyncClient, js_url: str, discovered_endpoints: Set[str], 
                            result_list: List[str], errors: List[str], base_target_url: str):
    """Analyze a JavaScript file for potential endpoints."""
    try:
        # Skip URLs with common non-JS extensions
        if not js_url.lower().endswith('.js') and '.js?' not in js_url.lower():
            return
            
        # Use a browser-like user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Referer": base_target_url
        }
        
        js_response = await client.get(js_url, headers=headers)
        if js_response.status_code == 200:
            content = js_response.text
            
            # Use the common analysis function for JS content
            await _analyze_js_content(content, js_url, discovered_endpoints, result_list, errors, base_target_url)

    except httpx.RequestError as e:
        errors.append(f"Error fetching JS file {js_url}: {str(e)}")
    except Exception as e:
        errors.append(f"Error analyzing JS file {js_url}: {str(e)}")

# Example of how to run (for testing purposes)
async def main_test():
    test_url = "http://testphp.vulnweb.com/"
    
    print(f"Crawling endpoints for {test_url}...")
    results = await crawl_endpoints(
        url=test_url, 
        depth=1,  # Set to 0 to disable internal link crawling, 1 for one level deep
        use_wordlist=True, 
        use_wayback=True, 
        analyze_js=True,
        max_js_files=5,
        timeout=10  # Set to 10 seconds
    )
    
    print("\n--- Results ---")
    print(f"Target URL: {results.get('target_url')}")
    print(f"Total Discovered Endpoints: {results.get('discovered_endpoints_count')}")
    
    print("\nEndpoints by Method:")
    for method, endpoints in results.get("endpoints_by_method", {}).items():
        if endpoints:
            print(f"  {method.capitalize()}:")
            for endpoint in endpoints[:10]:  # Print first 10 for brevity
                print(f"    - {endpoint}")
            if len(endpoints) > 10:
                print(f"    ... and {len(endpoints) - 10} more.")
                
    if results.get("errors"):
        print("\nErrors Encountered:")
        for error in results.get("errors", []):
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(main_test())
