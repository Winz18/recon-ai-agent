# Hướng dẫn định nghĩa Workflow mới

Tài liệu này mô tả cách tạo một quy trình (workflow) mới trong AI Pentesting Assistant để tự động hóa các bước reconnaissance khác nhau.

## Tổng quan về Workflows

Một workflow trong AI Pentesting Assistant là một quy trình hoàn chỉnh về thu thập thông tin, bao gồm:

1. **Lập kế hoạch** - Xác định mục tiêu và phương pháp
2. **Thu thập dữ liệu** - Sử dụng nhiều công cụ khác nhau
3. **Phân tích dữ liệu** - Xử lý và tổng hợp thông tin
4. **Tạo báo cáo** - Tổng hợp các phát hiện

Các workflow được lưu trữ trong thư mục `workflows/` và có thể được gọi từ giao diện dòng lệnh chính.

## Bước 1: Tạo File Workflow Mới

Tạo một file Python mới trong thư mục `workflows/`. Ví dụ, để tạo một workflow tập trung vào phân tích web:

```python
# workflows/webapp_workflow.py

import logging
import autogen
from typing import Dict, List, Optional, Tuple, Union, Any

# Import các agents cần thiết
from agents import (
    DomainIntelAgent,
    WebAppReconAgent, 
    ReconReporter
)

# Import các công cụ
from tools import (
    dns_lookup,
    get_http_headers,
    extract_security_headers,
    detect_technologies,
    capture_website_screenshot
)

# Import cấu hình
from config.settings import get_ag2_config_list

# Thiết lập logging
logger = logging.getLogger(__name__)

def run_webapp_recon(
    target_domain: str,
    use_ai_agents: bool = True,
    ag2_config: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Thực hiện quy trình phân tích ứng dụng web.
    
    Args:
        target_domain: Tên miền mục tiêu
        use_ai_agents: Sử dụng AI agents hay chỉ chạy các công cụ cơ bản
        ag2_config: Cấu hình AutoGen (nếu sử dụng AI agents)
        verbose: Hiển thị thông tin chi tiết
        
    Returns:
        Dict chứa kết quả phân tích
    """
    
    results = {}
    
    if verbose:
        logger.info(f"Bắt đầu phân tích ứng dụng web cho {target_domain}")
    
    # Thực hiện phân tích cơ bản nếu không sử dụng AI Agents
    if not use_ai_agents:
        # Kiểm tra DNS để xác nhận tồn tại
        dns_results = dns_lookup(target_domain)
        results["dns_info"] = dns_results
        
        # Phân tích HTTP Headers
        headers_results = get_http_headers(f"https://{target_domain}")
        results["http_headers"] = headers_results
        
        # Phân tích Security Headers
        security_headers = extract_security_headers(headers_results)
        results["security_headers"] = security_headers
        
        # Phát hiện công nghệ
        tech_results = detect_technologies(f"https://{target_domain}")
        results["technologies"] = tech_results
        
        # Chụp ảnh website
        screenshot_path = capture_website_screenshot(f"https://{target_domain}")
        results["screenshot"] = screenshot_path
        
        return results
    
    # Sử dụng AI Agents để phân tích
    else:
        if ag2_config is None:
            ag2_config = get_ag2_config_list()[0]
        
        # Khởi tạo các agents
        domain_agent = DomainIntelAgent(config_list=ag2_config)
        webapp_agent = WebAppReconAgent(config_list=ag2_config)
        reporter = ReconReporter(config_list=ag2_config)
        
        # Cấu hình các thông điệp giao tiếp giữa agents
        domain_agent.register_message_handler(webapp_agent.handle_message)
        webapp_agent.register_message_handler(reporter.handle_message)
        
        # Bắt đầu quá trình phân tích
        analysis_plan = {
            "target": target_domain,
            "actions": [
                "DNS Lookup",
                "HTTP Headers Analysis",
                "Technology Detection",
                "Security Headers Evaluation",
                "Website Screenshot"
            ]
        }
        
        # Thực hiện phân tích
        domain_agent.start_analysis(target_domain)
        webapp_agent.analyze_webapp(target_domain, analysis_plan)
        
        # Tạo báo cáo
        final_report = reporter.generate_report()
        
        # Trả về kết quả
        return final_report
```

## Bước 2: Đăng ký Workflow trong __init__.py

Cập nhật file `workflows/__init__.py` để đăng ký workflow mới:

```python
# workflows/__init__.py
from .standard_recon_workflow import run_standard_recon
from .webapp_workflow import run_webapp_recon

__all__ = ['run_standard_recon', 'run_webapp_recon']
```

## Bước 3: Thêm Logic cho AI Agents (nếu sử dụng)

Nếu workflow sử dụng AI Agents, cần đảm bảo các agents có khả năng thực hiện các nhiệm vụ mới. Ví dụ, thêm phương thức mới vào `WebAppReconAgent`:

```python
# agents/webapp_recon_agent.py

def analyze_webapp(self, target_domain: str, analysis_plan: Dict[str, Any]) -> None:
    """
    Phân tích ứng dụng web dựa trên kế hoạch
    
    Args:
        target_domain: Tên miền mục tiêu
        analysis_plan: Kế hoạch phân tích
    """
    self.logger.info(f"WebAppReconAgent bắt đầu phân tích {target_domain}")
    
    # Thực hiện các bước phân tích theo kế hoạch
    results = {}
    
    # Phân tích HTTP Headers
    if "HTTP Headers Analysis" in analysis_plan["actions"]:
        self.logger.info("Phân tích HTTP Headers")
        headers = get_http_headers(f"https://{target_domain}")
        results["http_headers"] = headers
    
    # Phát hiện công nghệ
    if "Technology Detection" in analysis_plan["actions"]:
        self.logger.info("Phát hiện công nghệ")
        tech = detect_technologies(f"https://{target_domain}")
        results["technologies"] = tech
    
    # Đánh giá Security Headers
    if "Security Headers Evaluation" in analysis_plan["actions"]:
        self.logger.info("Đánh giá Security Headers")
        sec_headers = extract_security_headers(results.get("http_headers", {}))
        results["security_headers"] = sec_headers
        
        # Phân tích sâu hơn bởi AI
        security_analysis = self._analyze_security_posture(sec_headers)
        results["security_analysis"] = security_analysis
    
    # Chụp ảnh website
    if "Website Screenshot" in analysis_plan["actions"]:
        self.logger.info("Chụp ảnh website")
        screenshot = capture_website_screenshot(f"https://{target_domain}")
        results["screenshot"] = screenshot
    
    # Gửi kết quả đến Reporter Agent
    self.send_message({
        "type": "webapp_analysis_results",
        "target": target_domain,
        "results": results
    })
    
def _analyze_security_posture(self, security_headers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích mức độ bảo mật dựa trên các security headers
    
    Args:
        security_headers: Headers bảo mật đã phát hiện
        
    Returns:
        Phân tích về mức độ bảo mật
    """
    # Logic phân tích bảo mật
    # ...
    
    return {
        "overall_score": 75,  # 0-100
        "findings": [
            {
                "header": "Content-Security-Policy",
                "status": "missing",
                "risk": "high",
                "description": "Missing CSP header allows XSS attacks"
            },
            # Các phát hiện khác...
        ],
        "recommendations": [
            "Implement proper Content-Security-Policy header",
            "Enable HTTP Strict Transport Security"
        ]
    }
```

## Bước 4: Tích hợp vào CLI chính

Cập nhật file `main.py` để thêm tùy chọn chạy workflow mới:

```python
# main.py (thêm vào phần xử lý tham số)

parser.add_argument(
    '--workflow', 
    choices=['standard', 'webapp', 'minimal', 'osint'],
    default='standard',
    help='Chọn quy trình reconnaissance'
)

# ...

# Phần xử lý workflow
if args.workflow == 'standard':
    from workflows import run_standard_recon
    results = run_standard_recon(
        target_domain=args.domain,
        use_ai_agents=not args.no_agent,
        ag2_config=ag2_config,
        verbose=args.verbose
    )
elif args.workflow == 'webapp':
    from workflows import run_webapp_recon
    results = run_webapp_recon(
        target_domain=args.domain,
        use_ai_agents=not args.no_agent,
        ag2_config=ag2_config,
        verbose=args.verbose
    )
# ...
```

## Bước 5: Tạo Unit Tests

Tạo unit tests trong thư mục `tests/`:

```python
# tests/test_webapp_workflow.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Thêm đường dẫn gốc vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workflows.webapp_workflow import run_webapp_recon

class TestWebAppWorkflow(unittest.TestCase):
    
    @patch('workflows.webapp_workflow.dns_lookup')
    @patch('workflows.webapp_workflow.get_http_headers')
    @patch('workflows.webapp_workflow.extract_security_headers')
    @patch('workflows.webapp_workflow.detect_technologies')
    @patch('workflows.webapp_workflow.capture_website_screenshot')
    def test_run_webapp_recon_without_agents(self, mock_screenshot, mock_tech, 
                                           mock_sec_headers, mock_headers, mock_dns):
        # Thiết lập mock data
        mock_dns.return_value = {"A": ["192.168.1.1"]}
        mock_headers.return_value = {"Server": "nginx"}
        mock_sec_headers.return_value = {"HSTS": "enabled"}
        mock_tech.return_value = {"web_server": "nginx", "frameworks": ["React"]}
        mock_screenshot.return_value = "example.png"
        
        # Chạy workflow
        results = run_webapp_recon("example.com", use_ai_agents=False)
        
        # Kiểm tra kết quả
        self.assertIn("dns_info", results)
        self.assertIn("http_headers", results)
        self.assertIn("security_headers", results)
        self.assertIn("technologies", results)
        self.assertIn("screenshot", results)
        
        # Kiểm tra các phương thức mock được gọi
        mock_dns.assert_called_once_with("example.com")
        mock_headers.assert_called_once_with("https://example.com")
        
if __name__ == "__main__":
    unittest.main()
```

## Bước 6: Tạo Ví dụ Sử dụng

Tạo một file ví dụ trong thư mục `examples/`:

```python
# examples/webapp_workflow_example.py
#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

# Thêm đường dẫn gốc vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from workflows.webapp_workflow import run_webapp_recon

def main():
    # Phân tích website example.com
    print("[+] Phân tích ứng dụng web cho example.com")
    
    results = run_webapp_recon(
        target_domain="example.com",
        use_ai_agents=False,
        verbose=True
    )
    
    # Lưu kết quả
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(project_root, 'reports', f"webapp_example_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
        
    print(f"[+] Kết quả đã được lưu vào: {output_file}")
    
    # Hiển thị một số thông tin quan trọng
    print("\n=== Thông tin công nghệ ===")
    for tech_type, tech_list in results.get('technologies', {}).items():
        if isinstance(tech_list, list):
            print(f"{tech_type}: {', '.join(tech_list)}")
        elif isinstance(tech_list, str):
            print(f"{tech_type}: {tech_list}")
    
    print("\n=== Thông tin security headers ===")
    for header, value in results.get('security_headers', {}).items():
        print(f"{header}: {value}")

if __name__ == "__main__":
    main()
```

## Bước 7: Cập nhật Tài liệu

Cập nhật file `README.md` để thêm thông tin về workflow mới:

```markdown
### Các workflows có sẵn:

1. **standard**: Quy trình đầy đủ, thực hiện tất cả các bước reconnaissance
2. **webapp**: Tập trung vào phân tích ứng dụng web và các vấn đề bảo mật
3. **minimal**: Quy trình nhanh, chỉ thực hiện các bước cơ bản
4. **osint**: Tập trung vào thu thập thông tin từ nguồn mở
```

## Một số loại Workflow phổ biến

1. **Full Reconnaissance**: Thực hiện tất cả các bước
2. **Quick Scan**: Chỉ thực hiện các kiểm tra cơ bản, nhanh chóng
3. **Passive Only**: Chỉ thu thập thông tin mà không tương tác trực tiếp với mục tiêu
4. **Web Application Focus**: Tập trung vào phân tích ứng dụng web
5. **Infrastructure Focus**: Tập trung vào cơ sở hạ tầng mạng
6. **OSINT Only**: Chỉ thu thập thông tin từ nguồn mở
7. **Custom**: Tùy chỉnh theo yêu cầu cụ thể

## Thực hành tốt khi phát triển Workflow

1. **Modular Design**: Thiết kế các module nhỏ, dễ tái sử dụng
2. **Error Handling**: Xử lý lỗi một cách chi tiết, không để crash
3. **Logging**: Ghi log đầy đủ để debug và theo dõi
4. **Progress Feedback**: Cung cấp thông tin về tiến độ xử lý
5. **Rate Limiting**: Thêm delay giữa các request để tránh bị chặn
6. **Configuration Options**: Cho phép người dùng tùy chỉnh workflow
7. **Documentation**: Tài liệu rõ ràng về cách workflow hoạt động
