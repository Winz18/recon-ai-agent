# Hướng dẫn thêm công cụ mới vào AI Pentesting Assistant

Tài liệu này mô tả cách thêm công cụ reconnaissance mới vào hệ thống AI Pentesting Assistant. Dự án được thiết kế theo kiến trúc mô-đun, cho phép dễ dàng mở rộng với các công cụ mới.

## Tổng quan

Mỗi công cụ trong AI Pentesting Assistant là một hàm Python thực hiện một nhiệm vụ cụ thể trong quá trình reconnaissance, ví dụ như DNS lookup, port scanning, hay phát hiện công nghệ. Các công cụ này được tổ chức trong thư mục `tools/` và được đăng ký để có thể được gọi bởi các AI agent.

## Bước 1: Tạo hàm công cụ mới

Tạo một file Python mới trong thư mục `tools/` hoặc thêm hàm vào file hiện có nếu phù hợp về mặt chức năng. Ví dụ, để tạo công cụ phân tích SSL/TLS:

```python
# tools/ssl_analyzer.py
import ssl
import socket
import datetime
import OpenSSL
from typing import Dict, Any, List, Optional

from .tool_decorator import recon_tool

@recon_tool
def analyze_ssl_certificate(domain: str, port: int = 443) -> Dict[str, Any]:
    """
    Phân tích chứng chỉ SSL/TLS của một tên miền.
    
    Args:
        domain: Tên miền cần phân tích
        port: Cổng (mặc định là 443 cho HTTPS)
        
    Returns:
        Dict chứa thông tin về chứng chỉ SSL
    """
    try:
        # Tạo SSL connection
        context = ssl.create_default_context()
        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=domain
        )
        conn.connect((domain, port))
        
        # Lấy thông tin chứng chỉ
        cert = conn.getpeercert()
        
        # Phân tích thông tin
        result = {
            "subject": dict(x[0] for x in cert["subject"]),
            "issuer": dict(x[0] for x in cert["issuer"]),
            "version": cert["version"],
            "notBefore": cert["notBefore"],
            "notAfter": cert["notAfter"],
            "serialNumber": cert["serialNumber"],
            "protocol_version": conn.version(),
            "cipher": conn.cipher(),
        }
        
        # Kiểm tra thời hạn hết hạn
        expiry_date = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        current_date = datetime.datetime.utcnow()
        remaining_days = (expiry_date - current_date).days
        
        result["days_until_expiry"] = remaining_days
        result["is_expired"] = remaining_days <= 0
        
        conn.close()
        return result
    except Exception as e:
        return {
            "error": str(e),
            "ssl_info": None
        }

@recon_tool
def check_ssl_vulnerabilities(domain: str, port: int = 443) -> Dict[str, Any]:
    """
    Kiểm tra các lỗ hổng SSL/TLS phổ biến như POODLE, Heartbleed, FREAK, etc.
    
    Args:
        domain: Tên miền cần kiểm tra
        port: Cổng (mặc định là 443)
        
    Returns:
        Dict chứa thông tin về các lỗ hổng bảo mật tiềm tàng
    """
    # Triển khai kiểm tra lỗ hổng
    # ...
    
    return {
        "poodle_vulnerable": False,
        "heartbleed_vulnerable": False,
        "freak_vulnerable": False,
        "logjam_vulnerable": False,
        "beast_vulnerable": False,
        "supports_tls_1_3": True,
        "cipher_strengths": {
            "strong": ["TLS_AES_256_GCM_SHA384"],
            "medium": [],
            "weak": []
        }
    }
```

### Quy ước Quan trọng

1. **Sử dụng type hints:** Luôn khai báo kiểu dữ liệu cho tham số và giá trị trả về
2. **Cung cấp docstring:** Mô tả rõ ràng công cụ làm gì, tham số và kết quả trả về
3. **Xử lý lỗi:** Luôn bắt ngoại lệ để tránh làm sập ứng dụng
4. **Định dạng kết quả:** Trả về dict có cấu trúc nhất quán

## Bước 2: Thêm Decorator recon_tool

Mỗi công cụ phải được đánh dấu bằng decorator `@recon_tool`. Decorator này thêm các tính năng:

- Ghi log mỗi khi công cụ được sử dụng
- Đo thời gian thực thi
- Lưu trữ kết quả cho báo cáo
- Cung cấp khả năng gọi từ các AI Agent

```python
from .tool_decorator import recon_tool

@recon_tool
def my_new_tool(param1, param2):
    # Triển khai công cụ
    pass
```

## Bước 3: Đăng ký công cụ trong __init__.py

Để công cụ mới có thể được nhập từ module `tools`, cần thêm nó vào file `tools/__init__.py`:

```python
# tools/__init__.py
from .network import dns_lookup, whois_lookup
from .web import get_http_headers, extract_security_headers
from .search import search_subdomains
from .tool_decorator import recon_tool
from .port_scanner import scan_ports
from .google_dorking import search_google_dorks
from .tech_detector import detect_technologies
from .screenshot import capture_website_screenshot
# Thêm import mới
from .ssl_analyzer import analyze_ssl_certificate, check_ssl_vulnerabilities
```

## Bước 4: Thêm Dependency (nếu cần)

Nếu công cụ mới yêu cầu các thư viện bên ngoài, thêm chúng vào `requirements.txt`:

```
# Thêm vào cuối file requirements.txt
pyOpenSSL==23.1.1
```

## Bước 5: Thêm Unit Test

Tạo một file test mới trong thư mục `tests/` để kiểm tra công cụ:

```python
# tests/test_tools_ssl_analyzer.py
import unittest
from unittest.mock import patch, MagicMock
from tools import analyze_ssl_certificate, check_ssl_vulnerabilities

class TestSSLAnalyzer(unittest.TestCase):
    
    @patch('tools.ssl_analyzer.ssl.create_default_context')
    def test_analyze_ssl_certificate(self, mock_context):
        # Thiết lập mock
        mock_conn = MagicMock()
        mock_context.return_value.wrap_socket.return_value = mock_conn
        mock_conn.getpeercert.return_value = {
            "subject": ((("commonName", "example.com"),),),
            "issuer": ((("commonName", "Let's Encrypt Authority X3"),),),
            "version": 3,
            "notBefore": "Jan 1 00:00:00 2023 GMT",
            "notAfter": "Dec 31 23:59:59 2023 GMT",
            "serialNumber": "1234567890",
        }
        mock_conn.version.return_value = "TLSv1.3"
        mock_conn.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
        
        # Chạy test
        result = analyze_ssl_certificate("example.com")
        
        # Kiểm tra kết quả
        self.assertIn("subject", result)
        self.assertIn("issuer", result)
        self.assertIn("protocol_version", result)
        
    def test_check_ssl_vulnerabilities(self):
        result = check_ssl_vulnerabilities("example.com")
        self.assertIn("poodle_vulnerable", result)
        self.assertIn("heartbleed_vulnerable", result)
        
if __name__ == "__main__":
    unittest.main()
```

## Bước 6: Sử dụng trong Workflow

Cập nhật workflow để sử dụng công cụ mới:

```python
# workflows/standard_recon_workflow.py

# Thêm import
from tools import analyze_ssl_certificate, check_ssl_vulnerabilities

# Trong phần định nghĩa workflow, thêm logic để sử dụng công cụ mới
ssl_info = analyze_ssl_certificate(domain)
ssl_vulns = check_ssl_vulnerabilities(domain)

# Thêm dữ liệu vào kết quả
results["ssl_analysis"] = {
    "certificate_info": ssl_info,
    "vulnerabilities": ssl_vulns
}
```

## Bước 7: Cập nhật Tài liệu

Cập nhật file README.md để thêm thông tin về công cụ mới:

```markdown
## Tính năng hiện có

* **Thu thập thông tin DNS**: Tra cứu các bản ghi DNS
* ... (các tính năng khác)
* **Phân tích SSL/TLS**: Kiểm tra cấu hình và lỗ hổng SSL/TLS
```

## Các Loại Công Cụ Phổ biến

Dưới đây là các loại công cụ phổ biến trong recon:

1. **Network Tools**: Phân tích các thông tin mạng
2. **Web Tools**: Phân tích ứng dụng web
3. **OSINT Tools**: Thu thập thông tin từ nguồn mở
4. **Infrastructure Tools**: Phân tích cơ sở hạ tầng
5. **Content Tools**: Phân tích nội dung 

## Thực hành tốt khi phát triển Tool mới

1. **Giới hạn Rate**: Thêm tùy chọn `delay` cho các công cụ gọi API
2. **Xử lý ngoại lệ**: Luôn bắt ngoại lệ và trả về thông tin lỗi có ý nghĩa
3. **Tham số tùy chọn**: Sử dụng tham số tùy chọn có giá trị mặc định
4. **Kiểm tra tính hợp lệ**: Kiểm tra các tham số đầu vào trước khi thực hiện
5. **Dữ liệu có cấu trúc**: Trả về kết quả dưới dạng dict có cấu trúc rõ ràng và nhất quán