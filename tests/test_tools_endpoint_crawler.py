import sys
import os

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from tools.endpoint_crawler import crawl_endpoints, _check_url, _analyze_single_js, _crawl_and_analyze_js

# Test target for most tests
TEST_TARGET_DOMAIN = "ntopng.org"
TEST_TARGET_URL = f"http://{TEST_TARGET_DOMAIN}"

@pytest.fixture
def mock_async_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.head = AsyncMock()
    client.get = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_crawl_endpoints_basic_success(mock_async_client):
    """Test basic successful crawl with all options disabled initially."""
    mock_async_client.get.return_value = AsyncMock(status_code=404) # Default to 404 for robots/sitemap

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(
            target_url=TEST_TARGET_DOMAIN, 
            use_wordlist=False, 
            use_wayback=False, 
            analyze_js=False,
            max_depth=0
        )
    
    assert results["target_url"] == TEST_TARGET_URL
    assert results["discovered_endpoints_count"] == 0
    assert not results["endpoints_by_method"]["wordlist"]
    assert not results["endpoints_by_method"]["wayback"]
    assert not results["endpoints_by_method"]["js_analysis"]
    assert not results["endpoints_by_method"]["internal_links"]
    assert "errors" not in results

@pytest.mark.asyncio
async def test_crawl_endpoints_with_robots_and_sitemap(mock_async_client):
    robots_content = "User-agent: *\nDisallow: /private\nSitemap: /sitemap.xml"
    sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url><loc>http://example.com/page1</loc></url>
   <url><loc>http://example.com/page2</loc></url>
</urlset>'''

    from unittest.mock import AsyncMock
    mock_robots_resp = AsyncMock()
    mock_robots_resp.status_code = 200
    mock_robots_resp.text = robots_content
    mock_sitemap_resp = AsyncMock()
    mock_sitemap_resp.status_code = 200
    mock_sitemap_resp.text = sitemap_content
    mock_other_resp = AsyncMock()
    mock_other_resp.status_code = 404

    async def side_effect_get(url, **kwargs):
        if url == f"{TEST_TARGET_URL}/robots.txt":
            return mock_robots_resp
        elif url == f"{TEST_TARGET_URL}/sitemap.xml":
            return mock_sitemap_resp
        elif url == f"{TEST_TARGET_URL}/page1":
            resp = AsyncMock()
            resp.status_code = 200
            return resp
        elif url == f"{TEST_TARGET_URL}/page2":
            resp = AsyncMock()
            resp.status_code = 200
            return resp
        return mock_other_resp

    mock_async_client.get.side_effect = side_effect_get
    mock_head_resp = AsyncMock()
    mock_head_resp.status_code = 200
    mock_async_client.head.return_value = mock_head_resp

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(
            target_url=TEST_TARGET_DOMAIN,
            use_wordlist=False,
            use_wayback=False,
            analyze_js=False,
            max_depth=0
        )

    assert f"{TEST_TARGET_URL}/robots.txt" in results["endpoints_by_method"]["robots_sitemap"]
    assert f"{TEST_TARGET_URL}/sitemap.xml" in results["endpoints_by_method"]["robots_sitemap"]
    assert f"{TEST_TARGET_URL}/page1" in results["all_discovered_endpoints"]
    assert f"{TEST_TARGET_URL}/page2" in results["all_discovered_endpoints"]
    assert results["discovered_endpoints_count"] >= 2

@pytest.mark.asyncio
async def test_crawl_endpoints_wordlist(mock_async_client):
    from unittest.mock import AsyncMock
    async def side_effect_head(url, **kwargs):
        resp = AsyncMock()
        if url == f"{TEST_TARGET_URL}/api":
            resp.status_code = 200
        else:
            resp.status_code = 404
        return resp

    mock_async_client.head.side_effect = side_effect_head
    mock_get_resp = AsyncMock()
    mock_get_resp.status_code = 404
    mock_async_client.get.return_value = mock_get_resp

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        with patch('tools.endpoint_crawler.COMMON_WORDLIST', ['api', 'admin']):
            results = await crawl_endpoints(target_url=TEST_TARGET_DOMAIN, use_wordlist=True, use_wayback=False, analyze_js=False, max_depth=0)

    assert f"{TEST_TARGET_URL}/api" in results["endpoints_by_method"]["wordlist"]
    assert f"{TEST_TARGET_URL}/api" in results["all_discovered_endpoints"]
    assert f"{TEST_TARGET_URL}/admin" not in results["all_discovered_endpoints"]
    assert results["discovered_endpoints_count"] == 1

@pytest.mark.asyncio
async def test_crawl_endpoints_wayback(mock_async_client):
    from unittest.mock import AsyncMock
    wayback_response_data = [
        ["original"],
        [f"{TEST_TARGET_URL}/archived_page"],
        ["http://external.com/other_page"]
    ]
    mock_wayback_api_resp = AsyncMock()
    mock_wayback_api_resp.status_code = 200
    mock_wayback_api_resp.json = AsyncMock(return_value=wayback_response_data)

    async def side_effect_head(url, **kwargs):
        resp = AsyncMock()
        if url == f"{TEST_TARGET_URL}/archived_page":
            resp.status_code = 200
        else:
            resp.status_code = 404
        return resp

    mock_async_client.head.side_effect = side_effect_head

    async def side_effect_get(url, **kwargs):
        if "web.archive.org" in url:
            return mock_wayback_api_resp
        resp = AsyncMock()
        resp.status_code = 404
        return resp

    mock_async_client.get.side_effect = side_effect_get

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(target_url=TEST_TARGET_DOMAIN, use_wordlist=False, use_wayback=True, analyze_js=False, max_depth=0)

    assert f"{TEST_TARGET_URL}/archived_page" in results["endpoints_by_method"]["wayback"]
    assert f"{TEST_TARGET_URL}/archived_page" in results["all_discovered_endpoints"]
    assert "http://external.com/other_page" not in results["all_discovered_endpoints"]
    assert results["discovered_endpoints_count"] == 1

@pytest.mark.asyncio
async def test_crawl_and_analyze_js_internal_links(mock_async_client):
    page_content = '''
    <html><body>
        <a href="/page1">Page 1</a>
        <a href="http://example.com/page2">Page 2</a>
        <a href="http://otherexample.com/page3">External Page</a>
        <script src="/main.js"></script>
    </body></html>
    '''
    js_content = '''var x = "/api/data";'''

    mock_initial_page_resp = AsyncMock(status_code=200, text=page_content)
    mock_page1_resp = AsyncMock(status_code=200, text="Page 1 content")
    mock_page2_resp = AsyncMock(status_code=200, text="Page 2 content")
    mock_js_resp = AsyncMock(status_code=200, text=js_content)
    mock_api_data_head_resp = AsyncMock(status_code=200)

    async def side_effect_get(url, **kwargs):
        if url == TEST_TARGET_URL:
            return mock_initial_page_resp
        elif url == f"{TEST_TARGET_URL}/page1":
            return mock_page1_resp
        elif url == f"{TEST_TARGET_URL}/page2":
            return mock_page2_resp
        elif url == f"{TEST_TARGET_URL}/main.js":
            return mock_js_resp
        return AsyncMock(status_code=404)

    async def side_effect_head(url, **kwargs):
        if url == f"{TEST_TARGET_URL}/api/data":
            return mock_api_data_head_resp
        return AsyncMock(status_code=200)

    mock_async_client.get.side_effect = side_effect_get
    mock_async_client.head.side_effect = side_effect_head

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(
            target_url=TEST_TARGET_DOMAIN,
            use_wordlist=False,
            use_wayback=False,
            analyze_js=True,
            max_js_files=1,
            max_depth=1
        )

    assert f"{TEST_TARGET_URL}/page1" in results["endpoints_by_method"]["internal_links"]
    assert f"{TEST_TARGET_URL}/page2" in results["endpoints_by_method"]["internal_links"]
    assert f"http://otherexample.com/page3" not in results["all_discovered_endpoints"]
    assert f"{TEST_TARGET_URL}/api/data" in results["endpoints_by_method"]["js_analysis"]
    assert results["discovered_endpoints_count"] >= 3
    assert mock_initial_page_resp.call_count == 1
    assert mock_page1_resp.call_count == 1
    assert mock_page2_resp.call_count == 1
    assert mock_js_resp.call_count == 1

@pytest.mark.asyncio
async def test_analyze_single_js_file(mock_async_client):
    js_content = '''
    const API_BASE = "/api/v1";
    fetch(API_BASE + "/users");
    fetch("/absolute/path");
    fetch("relative/path");
    fetch("http://example.com/full/path");
    fetch("http://external.com/api");
    let path1 = '/data/items';
    let path2 = `assets/config.json`;
    let img = "/img/logo.png";
    let css = "/css/style.css";
    '''
    js_url = f"{TEST_TARGET_URL}/scripts/main.js"
    mock_js_resp = AsyncMock(status_code=200, text=js_content)
    mock_async_client.get.return_value = mock_js_resp
    mock_async_client.head.return_value = AsyncMock(status_code=200)

    discovered_endpoints = set()
    result_list = []
    errors = []

    await _analyze_single_js(mock_async_client, js_url, discovered_endpoints, result_list, errors, TEST_TARGET_URL)

    assert not errors
    # Only string-literal endpoints are found by the current regex:
    expected_endpoints = {
        f"{TEST_TARGET_URL}/absolute/path",
        f"{TEST_TARGET_URL}/data/items",
        f"{TEST_TARGET_URL}/assets/config.json"
    }
    assert expected_endpoints.issubset(discovered_endpoints)
    assert all(ep in result_list for ep in expected_endpoints)
    assert f"{TEST_TARGET_URL}/img/logo.png" not in discovered_endpoints
    assert f"{TEST_TARGET_URL}/css/style.css" not in discovered_endpoints

@pytest.mark.asyncio
async def test_check_url_accessibility(mock_async_client):
    """Test the _check_url helper for accessibility."""
    discovered_set = set()
    result_list = []
    accessible_url = f"{TEST_TARGET_URL}/accessible"
    inaccessible_url = f"{TEST_TARGET_URL}/inaccessible"

    # Mock HEAD responses
    mock_async_client.head.side_effect = lambda url, **kwargs: \
        AsyncMock(status_code=200) if url == accessible_url else \
        AsyncMock(status_code=404) if url == inaccessible_url else \
        AsyncMock(side_effect=httpx.RequestError("Network error")) # For other error cases

    # Test accessible URL (HEAD)
    assert await _check_url(mock_async_client, accessible_url, discovered_set, result_list, method="HEAD")
    assert accessible_url in discovered_set
    assert accessible_url in result_list

    # Test inaccessible URL (HEAD)
    discovered_set.clear()
    result_list.clear()
    assert not await _check_url(mock_async_client, inaccessible_url, discovered_set, result_list, method="HEAD")
    assert inaccessible_url not in discovered_set

    # Test network error (HEAD)
    discovered_set.clear()
    result_list.clear()
    assert not await _check_url(mock_async_client, f"{TEST_TARGET_URL}/error_url", discovered_set, result_list, method="HEAD")
    assert f"{TEST_TARGET_URL}/error_url" not in discovered_set

    # Mock GET responses for GET method test
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        AsyncMock(status_code=302) if url == accessible_url else \
        AsyncMock(status_code=500)
    
    # Test accessible URL (GET, e.g. 302 redirect is considered accessible here)
    discovered_set.clear()
    result_list.clear()
    assert await _check_url(mock_async_client, accessible_url, discovered_set, result_list, method="GET")
    assert accessible_url in discovered_set

    # Test server error (GET)
    discovered_set.clear()
    result_list.clear()
    assert not await _check_url(mock_async_client, f"{TEST_TARGET_URL}/server_error", discovered_set, result_list, method="GET")
    assert f"{TEST_TARGET_URL}/server_error" not in discovered_set

@pytest.mark.asyncio
async def test_crawl_endpoints_http_prefix():
    """Test that http:// is prefixed if not present."""
    with patch('tools.endpoint_crawler.httpx.AsyncClient') as mock_ac:
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = AsyncMock(status_code=404)
        mock_ac.return_value = mock_client_instance
        
        results = await crawl_endpoints("no_protocol_domain.com", use_wordlist=False, use_wayback=False, analyze_js=False, max_depth=0)
        assert results["target_url"] == "http://no_protocol_domain.com"

        results_https = await crawl_endpoints("https://secure_domain.com", use_wordlist=False, use_wayback=False, analyze_js=False, max_depth=0)
        assert results_https["target_url"] == "https://secure_domain.com"

@pytest.mark.asyncio
async def test_crawl_endpoints_max_js_files_limit(mock_async_client):
    page_content = '''
    <html><body>
        <script src="/script1.js"></script>
        <script src="/script2.js"></script>
        <script src="/script3.js"></script>
    </body></html>
    '''
    mock_initial_page_resp = AsyncMock(status_code=200, text=page_content)
    
    # Mock GET to return the initial page, and then 200 for JS files
    def side_effect_get(url, **kwargs):
        if url == TEST_TARGET_URL:
            return mock_initial_page_resp
        elif url.startswith(f"{TEST_TARGET_URL}/script"):
            return AsyncMock(status_code=200, text="// js content")
        return AsyncMock(status_code=404) # For robots/sitemap
    
    mock_async_client.get.side_effect = side_effect_get
    mock_async_client.head.return_value = AsyncMock(status_code=404) # No endpoints from JS for this test

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        await crawl_endpoints(target_url=TEST_TARGET_DOMAIN, analyze_js=True, max_js_files=2, max_depth=0)
    
    # Check how many times JS files were fetched (GET requests for .js files)
    js_fetch_count = 0
    for call_args in mock_async_client.get.call_args_list:
        if call_args[0][0].endswith(".js"):
            js_fetch_count += 1
    assert js_fetch_count == 2 # Limited by max_js_files

@pytest.mark.asyncio
async def test_crawl_endpoints_max_depth_respected(mock_async_client):
    """Test that max_depth is respected for internal link crawling."""
    # Page 0 links to Page 1, Page 1 links to Page 2
    page0_content = f'<a href="/page1">Page 1</a>'
    page1_content = f'<a href="/page2">Page 2</a>'
    page2_content = f'No more links'

    mock_page0_resp = AsyncMock(status_code=200, text=page0_content)
    mock_page1_resp = AsyncMock(status_code=200, text=page1_content)
    mock_page2_resp = AsyncMock(status_code=200, text=page2_content)

    # GET side effect for page fetching
    def get_side_effect(url, **kwargs):
        if url == TEST_TARGET_URL:
            return mock_page0_resp
        elif url == f"{TEST_TARGET_URL}/page1":
            return mock_page1_resp
        elif url == f"{TEST_TARGET_URL}/page2":
            return mock_page2_resp
        return AsyncMock(status_code=404) # For robots/sitemap
    mock_async_client.get.side_effect = get_side_effect
    mock_async_client.head.return_value = AsyncMock(status_code=404) # No other discoveries

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        # Test max_depth = 0 (only initial page, no internal links followed)
        results_depth0 = await crawl_endpoints(TEST_TARGET_DOMAIN, max_depth=0, analyze_js=False)
        assert f"{TEST_TARGET_URL}/page1" not in results_depth0["all_discovered_endpoints"]
        assert f"{TEST_TARGET_URL}/page2" not in results_depth0["all_discovered_endpoints"]
        assert mock_page0_resp.call_count == 1
        assert mock_page1_resp.call_count == 0
        assert mock_page2_resp.call_count == 0

        # Reset mocks for next call
        mock_page0_resp.reset_mock()
        mock_page1_resp.reset_mock()
        mock_page2_resp.reset_mock()
        mock_async_client.get.reset_mock(side_effect=True) # Reset call counts but keep side_effect
        mock_async_client.get.side_effect = get_side_effect # Re-assign side effect

        # Test max_depth = 1 (initial page + page1)
        results_depth1 = await crawl_endpoints(TEST_TARGET_DOMAIN, max_depth=1, analyze_js=False)
        assert f"{TEST_TARGET_URL}/page1" in results_depth1["all_discovered_endpoints"]
        assert f"{TEST_TARGET_URL}/page2" not in results_depth1["all_discovered_endpoints"]
        assert mock_page0_resp.call_count == 1
        assert mock_page1_resp.call_count == 1
        assert mock_page2_resp.call_count == 0

        # Reset mocks for next call
        mock_page0_resp.reset_mock()
        mock_page1_resp.reset_mock()
        mock_page2_resp.reset_mock()
        mock_async_client.get.reset_mock(side_effect=True)
        mock_async_client.get.side_effect = get_side_effect

        # Test max_depth = 2 (initial page + page1 + page2)
        results_depth2 = await crawl_endpoints(TEST_TARGET_DOMAIN, max_depth=2, analyze_js=False)
        assert f"{TEST_TARGET_URL}/page1" in results_depth2["all_discovered_endpoints"]
        assert f"{TEST_TARGET_URL}/page2" in results_depth2["all_discovered_endpoints"]
        assert mock_page0_resp.call_count == 1
        assert mock_page1_resp.call_count == 1
        assert mock_page2_resp.call_count == 1

@pytest.mark.asyncio
async def test_wayback_error_handling(mock_async_client):
    """Test error handling for Wayback Machine query failures."""
    # Simulate API error
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        AsyncMock(status_code=503) if "web.archive.org" in url else \
        AsyncMock(status_code=404) # For robots/sitemap

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(TEST_TARGET_DOMAIN, use_wayback=True, analyze_js=False, max_depth=0)
    
    assert "errors" in results
    assert any("Wayback Machine query failed with status: 503" in e for e in results["errors"])
    assert not results["endpoints_by_method"]["wayback"]

    # Simulate JSON parsing error
    mock_bad_json_resp = AsyncMock(status_code=200)
    mock_bad_json_resp.json = AsyncMock(side_effect=ValueError("Bad JSON"))
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        mock_bad_json_resp if "web.archive.org" in url else \
        AsyncMock(status_code=404)
    
    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results_json_error = await crawl_endpoints(TEST_TARGET_DOMAIN, use_wayback=True, analyze_js=False, max_depth=0)

    assert "errors" in results_json_error
    assert any("Error querying Wayback Machine: Bad JSON" in e for e in results_json_error["errors"])
    assert not results_json_error["endpoints_by_method"]["wayback"]

@pytest.mark.asyncio
async def test_js_analysis_error_handling(mock_async_client):
    """Test error handling during JS file fetching and analysis."""
    page_content = '<script src="/failing_script.js"></script>'
    mock_initial_page_resp = AsyncMock(status_code=200, text=page_content)
    
    # JS fetch fails
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        mock_initial_page_resp if url == TEST_TARGET_URL else \
        AsyncMock(status_code=500) if url.endswith("failing_script.js") else \
        AsyncMock(status_code=404) # For robots/sitemap
    mock_async_client.head.return_value = AsyncMock(status_code=404)

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(TEST_TARGET_DOMAIN, analyze_js=True, max_js_files=1, max_depth=0)

    assert "errors" in results
    assert any(f"Failed to fetch JS file {TEST_TARGET_URL}/failing_script.js: Status 500" in e for e in results["errors"])
    assert not results["endpoints_by_method"]["js_analysis"]

    # JS analysis itself raises an unexpected error (e.g., regex error, though less likely with current simple regex)
    # We can simulate this by patching re.findall inside _analyze_single_js if needed, 
    # but for now, let's assume the httpx error is sufficient for this test case.

@pytest.mark.asyncio
async def test_robots_sitemap_fetch_errors(mock_async_client):
    """Test error handling when fetching robots.txt or sitemap.xml fails."""
    mock_async_client.get.side_effect = httpx.RequestError("Connection failed")

    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results = await crawl_endpoints(TEST_TARGET_DOMAIN, max_depth=0)
    
    assert "errors" in results
    assert len(results["errors"]) > 0
    assert any("Error fetching robots.txt/sitemap.xml: Connection failed" in e for e in results["errors"])

@pytest.mark.asyncio
async def test_empty_wayback_response(mock_async_client):
    """Test handling of an empty or minimal (header-only) Wayback response."""
    # Header only
    wayback_response_data_header_only = [["original"]]
    mock_wayback_api_resp_header = AsyncMock(status_code=200)
    mock_wayback_api_resp_header.json = AsyncMock(return_value=wayback_response_data_header_only)

    # Empty list
    wayback_response_data_empty = []
    mock_wayback_api_resp_empty = AsyncMock(status_code=200)
    mock_wayback_api_resp_empty.json = AsyncMock(return_value=wayback_response_data_empty)

    mock_async_client.head.return_value = AsyncMock(status_code=404) # No other discoveries

    # Test header-only response
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        mock_wayback_api_resp_header if "web.archive.org" in url else \
        AsyncMock(status_code=404)
    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results_header = await crawl_endpoints(TEST_TARGET_DOMAIN, use_wayback=True, analyze_js=False, max_depth=0)
    assert not results_header["endpoints_by_method"]["wayback"]
    assert "errors" not in results_header # Not an error, just no data

    # Test empty list response
    mock_async_client.get.side_effect = lambda url, **kwargs: \
        mock_wayback_api_resp_empty if "web.archive.org" in url else \
        AsyncMock(status_code=404)
    with patch('tools.endpoint_crawler.httpx.AsyncClient', return_value=mock_async_client):
        results_empty = await crawl_endpoints(TEST_TARGET_DOMAIN, use_wayback=True, analyze_js=False, max_depth=0)
    assert not results_empty["endpoints_by_method"]["wayback"]
    assert "errors" not in results_empty

