import os
import sys
import unittest

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

if __name__ == "__main__":
    unittest.main()