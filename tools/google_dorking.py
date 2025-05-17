import time
from typing import Dict, List, Optional, Union, Annotated
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .tool_decorator import recon_tool

@recon_tool(cache_ttl_seconds=3600, max_retries=1, retry_delay_seconds=5)
def search_google_dorks(
    domain: Annotated[str, "Target domain to perform dorking on"],
    dorks: Annotated[Optional[List[str]], "List of specific dork queries. If None, uses common dorks"] = None,
    api_key: Annotated[Optional[str], "Google Custom Search API key"] = None,
    cse_id: Annotated[Optional[str], "Google Custom Search Engine ID"] = None,
    max_results: Annotated[int, "Maximum number of results per dork"] = 10,
    respect_rate_limits: Annotated[bool, "Whether to add delay between queries to respect Google's rate limits"] = True
) -> Dict[str, List[Dict[str, str]]]:
    """
    Perform Google dorking on a domain using predefined or custom dorks.
    
    Args:
        domain: Target domain to perform dorking on
        dorks: List of dork queries to use. If None, uses common dorks for the domain
        api_key: Google Custom Search API key (required for API use)
        cse_id: Google Custom Search Engine ID (required for API use)
        max_results: Maximum number of results per dork to return
        respect_rate_limits: Whether to add delay between queries
        
    Returns:
        Dictionary with dorks as keys and lists of results as values
    """
    # Use default dorks if none provided
    if dorks is None:
        dorks = get_common_dorks(domain)
    else:
        # Make sure domain is included in each dork if not already
        dorks = [(f"site:{domain} {dork}" if "site:" not in dork else dork) for dork in dorks]
    
    results = {}
    
    # Check if API is available or fall back to alternative method
    if api_key and cse_id:
        results = _search_with_api(dorks, api_key, cse_id, max_results, respect_rate_limits)
    else:
        try:
            # Try using googlesearch-python if available
            results = _search_with_googlesearch(dorks, max_results, respect_rate_limits)
        except ImportError:
            return {"error": "Either Google API credentials or googlesearch-python is required"}
    
    return results

def _search_with_api(dorks, api_key, cse_id, max_results, respect_rate_limits):
    """Use Google Custom Search API to perform searches"""
    results = {}
    quota_error_encountered = False
    
    try:
        # Build the service
        service = build("customsearch", "v1", developerKey=api_key)
        
        for dork in dorks:
            # Nếu đã gặp lỗi quota, không thực hiện thêm tìm kiếm
            if quota_error_encountered:
                results[f"{dork}_skipped"] = "Skipped due to previous API quota limit"
                continue
                
            dork_results = []
            
            # API can return a maximum of 10 results per query, so paginate if needed
            for i in range(0, min(max_results, 100), 10):
                try:
                    # Execute the search
                    result = service.cse().list(
                        q=dork,
                        cx=cse_id,
                        start=i + 1,
                        num=min(10, max_results - i)
                    ).execute()
                    
                    # Process results
                    if "items" in result:
                        for item in result["items"]:
                            dork_results.append({
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "snippet": item.get("snippet", "")
                            })
                    
                    # Respect rate limits if requested
                    if respect_rate_limits:
                        time.sleep(1)  # 1 second delay between API calls
                        
                except HttpError as e:
                    error_message = str(e).lower()
                    # Handle API errors
                    if "quota" in error_message or "limit" in error_message or "429" in error_message:
                        quota_error_encountered = True
                        return {"error": "Google API quota exceeded. Please try again later."}
                    else:
                        results[f"{dork}_error"] = f"API error: {str(e)}"
                        break
            
            # Store results for this dork
            if dork_results:
                results[dork] = dork_results
            
    except Exception as e:
        return {"error": f"Google API search failed: {str(e)}"}
    
    # Kiểm tra nếu không có kết quả hợp lệ nào và tất cả đều là lỗi
    if not any(k for k in results.keys() if not (k.endswith('_error') or k.endswith('_skipped'))):
        return {"error": "All Google dork searches failed. Please check API credentials or try again later."}
    
    return results

def _search_with_googlesearch(dorks, max_results, respect_rate_limits):
    """Use googlesearch-python library as a fallback"""
    results = {}
    rate_limit_count = 0
    max_rate_limit_errors = 3  # Giới hạn số lượng lỗi rate limit trước khi từ bỏ
    
    try:
        from googlesearch import search
        
        for dork in dorks:
            dork_results = []
            
            try:
                # Execute the search with googlesearch
                for url in search(dork, num_results=max_results, lang="en"):
                    dork_results.append({
                        "title": "",  # No title available with this method
                        "link": url,
                        "snippet": ""  # No snippet available
                    })
                    
                    # Respect rate limits
                    if respect_rate_limits:
                        time.sleep(2)  # More conservative delay for free method
            
            except Exception as e:
                error_message = str(e).lower()
                
                # Phát hiện lỗi rate limit (có thể điều chỉnh các chuỗi tùy thuộc vào thông báo lỗi thực tế)
                if any(keyword in error_message for keyword in ["rate", "limit", "429", "too many requests", "blocked"]):
                    rate_limit_count += 1
                    if rate_limit_count >= max_rate_limit_errors:
                        return {"error": f"Google search rate limit exceeded after {rate_limit_count} attempts. Please try again later."}
                    
                # Ghi lại lỗi và tiếp tục với dork tiếp theo
                results[f"{dork}_error"] = f"Search error: {str(e)}"
                continue
            
            # Store results for this dork
            if dork_results:
                results[dork] = dork_results
        
        # Nếu tất cả các dork đều không có kết quả (có thể do rate limit)
        if not any(k for k in results.keys() if not k.endswith('_error')):
            # Kiểm tra xem có phải tất cả đều là lỗi rate limit không
            rate_limit_errors = [k for k in results.keys() if k.endswith('_error') and any(
                keyword in results[k].lower() for keyword in ["rate", "limit", "429", "too many requests", "blocked"]
            )]
            
            if len(rate_limit_errors) > 0:
                return {"error": "Multiple Google dork searches failed due to rate limiting. Please try again later."}
            
    except ImportError:
        return {"error": "googlesearch-python library is required when API key is not provided"}
    except Exception as e:
        return {"error": f"Google search failed: {str(e)}"}
    
    return results

def get_common_dorks(domain: str) -> List[str]:
    """
    Returns a list of common Google dorks for a domain.
    
    Args:
        domain: Target domain
        
    Returns:
        List of dork queries
    """
    return [
        f"site:{domain}",
        f"site:{domain} inurl:login OR inurl:admin OR inurl:password",
        f"site:{domain} filetype:pdf",
        f"site:{domain} filetype:doc OR filetype:docx OR filetype:xls OR filetype:xlsx",
        f"site:{domain} intitle:\"index of\"",
        f"site:{domain} inurl:wp-content OR inurl:wp-includes",
        f"site:{domain} inurl:config OR inurl:conf",
        f"site:{domain} \"confidential\" OR \"not for distribution\"",
        f"site:{domain} \"powered by\" OR \"created by\"",
        f"site:{domain} inurl:backup OR inurl:old OR inurl:dev"
    ]
