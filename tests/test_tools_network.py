import os
import sys
import unittest

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.network import dns_lookup, whois_lookup

class TestNetworkTools(unittest.TestCase):
    """Kiểm thử các công cụ liên quan đến mạng."""
    
    def test_dns_lookup_exists(self):
        """Kiểm tra DNS lookup với tên miền tồn tại."""
        result = dns_lookup("google.com")
        
        # Kiểm tra kết quả có phải là dict
        self.assertIsInstance(result, dict)
        
        # Kiểm tra ít nhất một loại record được trả về
        self.assertGreater(len(result), 0)
        
        # Kiểm tra một số loại record phổ biến
        for record_type in ["A", "AAAA", "MX", "NS", "TXT"]:
            if record_type in result:
                # Nếu record type có trong kết quả, kiểm tra nó là list và không rỗng
                self.assertIsInstance(result[record_type], list)
                self.assertGreater(len(result[record_type]), 0)
    
    def test_dns_lookup_nonexistent(self):
        """Kiểm tra DNS lookup với tên miền không tồn tại."""
        result = dns_lookup("thiswillnotexistforevertruemeqwerty123.com")
        
        # Tên miền không tồn tại có thể trả về dict rỗng hoặc có một số record
        self.assertIsInstance(result, dict)
    
    def test_whois_lookup(self):
        """Kiểm tra WHOIS lookup."""
        result = whois_lookup("google.com")
        
        # Kiểm tra kết quả có phải là string
        self.assertIsInstance(result, str)
        
        # Kiểm tra kết quả không rỗng
        self.assertGreater(len(result), 0)
        
        # Kiểm tra một số từ khóa phổ biến trong kết quả WHOIS
        # (Nội dung cụ thể có thể thay đổi theo registrar và TLD)
        common_terms = ["Domain Name", "Registrar", "Updated Date", "Creation Date"]
        found_terms = 0
        for term in common_terms:
            if term.lower() in result.lower():
                found_terms += 1
        
        # Ít nhất một số thuật ngữ phổ biến phải xuất hiện
        self.assertGreater(found_terms, 0)

if __name__ == "__main__":
    unittest.main()