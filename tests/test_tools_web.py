import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.web import get_http_headers, extract_security_headers

class TestWebTools(unittest.TestCase):
    """Kiểm thử các công cụ liên quan đến web."""
    
    def test_get_http_headers(self):
        """Kiểm tra lấy HTTP headers từ trang web."""
        result = get_http_headers("google.com")
        
        # Kiểm tra kết quả là dictionary
        self.assertIsInstance(result, dict)
        
        # Kiểm tra có các trường quan trọng
        self.assertIn("status_code", result)
        self.assertIn("url", result)
        
        # Kiểm tra status code thành công
        self.assertEqual(result["status_code"], "200")
    
    def test_get_http_headers_with_method(self):
        """Test getting HTTP headers with specific method."""
        # Test with HEAD method
        result_head = get_http_headers("google.com", method="HEAD")
        self.assertIsInstance(result_head, dict)
        self.assertIn("status_code", result_head)
        
        # Test with GET method
        result_get = get_http_headers("google.com", method="GET")
        self.assertIsInstance(result_get, dict)
        self.assertIn("status_code", result_get)
    
    def test_get_http_headers_with_timeout(self):
        """Test getting HTTP headers with custom timeout."""
        result = get_http_headers("google.com", timeout=5)
        self.assertIsInstance(result, dict)
        self.assertIn("status_code", result)
    
    def test_get_http_headers_with_user_agent(self):
        """Test getting HTTP headers with custom user agent."""
        custom_ua = "Mozilla/5.0 Test Agent"
        result = get_http_headers("google.com", user_agent=custom_ua)
        self.assertIsInstance(result, dict)
        self.assertIn("status_code", result)
    
    def test_get_http_headers_non_existent_domain(self):
        """Test getting HTTP headers from non-existent domain."""
        result = get_http_headers("thissitedoesnotexistforever12345.com")
        
        # Should return an error dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
    
    @patch('requests.head')
    @patch('requests.get')
    def test_get_http_headers_connection_error(self, mock_get, mock_head):
        """Test handling of connection errors."""
        # Setup mocks to raise connection error
        import requests
        mock_head.side_effect = requests.exceptions.ConnectionError("Connection refused")
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Call function
        result = get_http_headers("example.com")
        
        # Check error is handled correctly
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Connection", result["error"])
    
    @patch('requests.head')
    @patch('requests.get')
    def test_get_http_headers_timeout(self, mock_get, mock_head):
        """Test handling of timeout errors."""
        # Setup mocks to raise timeout
        import requests
        mock_head.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Call function
        result = get_http_headers("example.com")
        
        # Check error is handled correctly
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("timed out", result["error"])
    
    def test_extract_security_headers(self):
        """Kiểm tra phân tích security headers."""
        # Tạo một dictionary headers giả định
        mock_headers = {
            "strict-transport-security": "max-age=31536000",
            "content-security-policy": "default-src 'self'",
            "status_code": "200",
            "server": "nginx"
        }
        
        result = extract_security_headers(mock_headers)
        
        # Kiểm tra kết quả là dictionary
        self.assertIsInstance(result, dict)
        
        # Kiểm tra có phần tích các headers bảo mật
        self.assertIn("analysis", result)
        self.assertIn("found_headers", result["analysis"])
        self.assertIn("missing_headers", result["analysis"])
        
        # Kiểm tra phát hiện đúng các headers đã có
        self.assertIn("strict-transport-security", result["analysis"]["found_headers"])
        self.assertIn("content-security-policy", result["analysis"]["found_headers"])
        
        # Kiểm tra có một số headers bảo mật bị thiếu
        self.assertTrue(len(result["analysis"]["missing_headers"]) > 0)
    
    def test_extract_security_headers_with_recommendations(self):
        """Test security headers analysis with recommendations."""
        # Create mock headers
        mock_headers = {
            "strict-transport-security": "max-age=31536000",
            "content-security-policy": "default-src 'self'"
        }
        
        result = extract_security_headers(mock_headers, include_recommendations=True)
        
        # Check recommendations are included
        self.assertIn("recommendations", result)
        self.assertTrue(len(result["recommendations"]) > 0)
        
        # Check score is calculated
        self.assertIn("score", result["analysis"])
        self.assertIn("max_score", result["analysis"])
        self.assertIn("score_percentage", result["analysis"])
        
        # Check rating is provided
        self.assertIn("rating", result["analysis"])
    
    def test_extract_security_headers_without_recommendations(self):
        """Test security headers analysis without recommendations."""
        # Create mock headers
        mock_headers = {
            "strict-transport-security": "max-age=31536000"
        }
        
        result = extract_security_headers(mock_headers, include_recommendations=False)
        
        # Check recommendations are not included
        self.assertNotIn("recommendations", result)
        
        # Still should have analysis
        self.assertIn("analysis", result)
        self.assertIn("score", result["analysis"])

if __name__ == "__main__":
    unittest.main()