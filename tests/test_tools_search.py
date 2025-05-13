import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add root project directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.search import search_subdomains, related_domains_search

class TestSearchTools(unittest.TestCase):
    """Test the search tools functionality"""
    
    @patch('tools.search.dns.resolver.Resolver')
    @patch('tools.search.requests.get')
    def test_search_subdomains_basic(self, mock_get, mock_resolver):
        """Test basic subdomain search without APIs"""
        # Setup mock resolver
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        
        # Make first subdomain exist, second one not exist
        def mock_resolve(domain, record_type):
            if domain == "www.example.com":
                return ["example.com"]
            elif domain == "api.example.com":
                # Simulate DNS failure for this domain
                raise Exception("NXDOMAIN")
            return ["example.com"]  # Default for any other domain
            
        resolver_instance.resolve.side_effect = mock_resolve
        
        # Call the function without using external APIs
        result = search_subdomains("example.com", use_apis=False, max_threads=2)
        
        # Should be a list with at least some subdomains (mocked ones)
        self.assertIsInstance(result, list)
        
        # Verify DNS resolver was called with the expected parameters
        resolver_instance.resolve.assert_called()
        
        # Verify no API calls were made
        mock_get.assert_not_called()
    
    @patch('tools.search.dns.resolver.Resolver')
    @patch('tools.search.requests.get')
    def test_search_subdomains_with_apis(self, mock_get, mock_resolver):
        """Test subdomain search with API calls"""
        # Setup mock resolver
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        
        # Setup mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"dns_names": ["api.example.com", "dev.example.com"]}
        ]
        mock_get.return_value = mock_response
        
        # Call the function with API enabled
        result = search_subdomains("example.com", use_apis=True, max_threads=2)
        
        # Should return list of subdomains
        self.assertIsInstance(result, list)
        
        # Verify API was called
        mock_get.assert_called()
        
    @patch('tools.search.dns.resolver.Resolver')
    def test_search_subdomains_error_handling(self, mock_resolver):
        """Test error handling in subdomain search"""
        # Setup mock resolver
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        
        # Make resolver throw an exception
        resolver_instance.resolve.side_effect = Exception("DNS server error")
        
        # Call the function
        result = search_subdomains("example.com", use_apis=False, max_threads=2)
        
        # Should return message about no subdomains found
        self.assertIsInstance(result, dict)
        self.assertIn("message", result)
    
    @patch('tools.search.dns.resolver.Resolver')
    def test_related_domains_search_basic(self, mock_resolver):
        """Test basic related domains search"""
        # Setup mock resolver
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        
        # Make some domains exist in DNS
        def mock_resolve(domain, record_type):
            if domain in ["example.net", "example-cdn.com"]:
                return ["192.0.2.1"]
            # All other domains don't resolve
            raise Exception("NXDOMAIN")
            
        resolver_instance.resolve.side_effect = mock_resolve
        
        # Call the function with specific parameters
        result = related_domains_search(
            "example.com",
            patterns=["{keyword}-cdn"],
            tlds=["com", "net"],
            check_existence=True
        )
        
        # Should return list of related domains that "exist"
        self.assertIsInstance(result, list)
        self.assertIn("example.net", result)
        self.assertIn("example-cdn.com", result)
        
    def test_related_domains_search_no_check(self):
        """Test related domains search without DNS checks"""
        # Call the function without checking existence
        result = related_domains_search(
            "example.com",
            patterns=["{keyword}-test", "{keyword}-dev"],
            tlds=["com", "org"],
            check_existence=False
        )
        
        # Should return all possible domains without checking existence
        self.assertIsInstance(result, list)
        self.assertIn("example-test.com", result)
        self.assertIn("example-dev.org", result)
        
    def test_related_domains_invalid_input(self):
        """Test related domains search with invalid input"""
        # Call with invalid domain
        result = related_domains_search("invalid")
        
        # Should return error
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
