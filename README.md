# AI Pentesting Assistant - Footprinting & Reconnaissance

Công cụ hỗ trợ Pentester trong giai đoạn Footprinting và Reconnaissance sử dụng AI Agent (AutoGen Framework) và triển khai trên Google Cloud Vertex AI. Hệ thống này sử dụng các agent thông minh để tự động hóa quá trình thu thập thông tin từ nhiều nguồn, phân tích dữ liệu, và tạo báo cáo chi tiết.

## Tính năng hiện có

* **Thu thập thông tin DNS**: Tra cứu các bản ghi A, AAAA, MX, NS, TXT của tên miền
* **Tra cứu thông tin WHOIS**: Lấy thông tin đăng ký tên miền
* **Quét cổng cơ bản**: Kiểm tra các cổng thông dụng đang mở trên máy chủ đích
* **Thu thập thông tin HTTP Headers**: Phân tích các header của web server để xác định bảo mật
* **Tìm kiếm Subdomain**: Sử dụng nhiều kỹ thuật để tìm kiếm tên miền con
* **Google Dorking**: Tìm kiếm thông tin nhạy cảm qua Google Search
* **Phát hiện công nghệ**: Xác định các framework, CMS, và công nghệ được sử dụng trên website
* **Chụp ảnh website**: Tự động chụp ảnh màn hình của website mục tiêu
* **AI Agent tự động**: Khả năng lập kế hoạch và thực hiện reconnaissance tự động bằng AutoGen Framework
* **Tổng hợp báo cáo**: Tạo báo cáo tổng hợp về các phát hiện bảo mật (HTML & JSON)

## Công nghệ sử dụng

* **Python:** Ngôn ngữ lập trình chính
* **AutoGen Framework (AG2):** Framework xây dựng và điều phối AI Agent
* **Google Cloud Vertex AI:** Nền tảng để chạy và quản lý AI Agent
    * Vertex AI SDK for Python 
    * Gemini Models
* **Thư viện Network & Web:** `dnspython`, `python-whois`, `requests`, `beautifulsoup4` 
* **Thư viện Search:** `google-api-python-client`, `googlesearch-python`
* **Công nghệ UI:** `colorama`, `termcolor` cho giao diện CLI thân thiện

## Cài đặt

1.  **Clone repository:**

2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Trên Linux/macOS
    # venv\Scripts\activate  # Trên Windows
    ```

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Cấu hình môi trường:**
    * Tạo file `.env` với các thông tin sau:
        ```
        GOOGLE_PROJECT_ID=your-gcp-project-id
        GOOGLE_REGION=us-central1
        AG2_MODEL=gemini-1.5-pro-latest
        ```
    * Thiết lập Google Cloud Authentication:
        ```bash
        gcloud auth application-default login
        ```
    * Đảm bảo Vertex AI API đã được kích hoạt trên Google Cloud Console

## Sử dụng

### Chạy quy trình reconnaissance tự động

```bash
python main.py --domain example.com --workflow standard
```

Các tham số chính:
* `--domain`: Tên miền hoặc IP mục tiêu
* `--workflow`: Loại quy trình (standard, minimal, osint, webapp)
* `--output`: Định dạng báo cáo (json, html, text)
* `--no-agent`: Chỉ sử dụng các công cụ cơ bản

### Chạy công cụ riêng lẻ:

```bash
# Thông tin DNS
python -c "from tools import dns_lookup; print(dns_lookup('example.com'))"

# Thông tin WHOIS
python -c "from tools import whois_lookup; print(whois_lookup('example.com'))"

# Quét port
python -c "from tools import scan_ports; print(scan_ports('example.com', [80, 443, 22, 21, 3389]))"

# Chụp ảnh website
python -c "from tools import capture_website_screenshot; capture_website_screenshot('https://example.com')"

# Phát hiện công nghệ
python -c "from tools import detect_technologies; print(detect_technologies('https://example.com'))"
```

### Các workflows có sẵn:

1. **standard**: Quy trình đầy đủ, thực hiện tất cả các bước reconnaissance
2. **minimal**: Quy trình nhanh, chỉ thực hiện các bước cơ bản
3. **osint**: Tập trung vào thu thập thông tin từ nguồn mở
4. **webapp**: Tập trung vào phân tích ứng dụng web

## Cấu trúc thư mục

```
.
├── agents/                     # AI Agents sử dụng AutoGen Framework
│   ├── domain_intel_agent.py   # Agent phân tích thông tin tên miền
│   ├── network_recon_agent.py  # Agent tìm kiếm thông tin mạng
│   ├── osint_agent.py          # Agent thu thập thông tin từ nguồn mở
│   ├── recon_planner.py        # Agent lập kế hoạch recon
│   ├── reporter.py             # Agent tạo báo cáo kết quả
│   └── webapp_recon_agent.py   # Agent phân tích ứng dụng web
│
├── config/                     # Cấu hình ứng dụng
│   └── settings.py             # Cài đặt Vertex AI và AutoGen
│
├── docs/                       # Tài liệu hướng dẫn
│   ├── adding_tools.md         # Hướng dẫn thêm công cụ mới
│   └── architecture.md         # Mô tả kiến trúc hệ thống
│
├── examples/                   # Ví dụ sử dụng
│   └── standard_workflow_example.py  # Ví dụ workflow chuẩn
│
├── reports/                    # Thư mục chứa các báo cáo
│   └── raw_data/               # Dữ liệu gốc từ các công cụ
│
├── tests/                      # Unit tests
│
├── tools/                      # Các công cụ reconnaissance
│   ├── google_dorking.py       # Tìm kiếm thông tin qua Google
│   ├── network.py              # Công cụ phân tích mạng
│   ├── port_scanner.py         # Quét cổng
│   ├── screenshot.py           # Chụp ảnh website
│   ├── search.py               # Tìm kiếm thông tin
│   ├── tech_detector.py        # Phát hiện công nghệ
│   ├── tool_decorator.py       # Decorator cho các công cụ
│   └── web.py                  # Công cụ phân tích web
│
├── utils/                      # Tiện ích và hàm hỗ trợ
│   └── logging_setup.py        # Cấu hình logging
│
├── workflows/                  # Các quy trình reconnaissance
│   └── standard_recon_workflow.py  # Quy trình chuẩn
│
├── main.py                     # Chương trình chính
├── requirements.txt            # Thư viện cần thiết
└── README.md                   # Tài liệu tổng quan
```

## Các tính năng sắp có

* **Passive Subdomain Enumeration**: Sử dụng các dịch vụ OSINT như Shodan, SecurityTrails
* **SSL/TLS Analysis**: Kiểm tra cấu hình và lỗ hỏng trên TLS/SSL
* **Email Harvesting**: Thu thập địa chỉ email liên quan đến tên miền
* **Dark Web Monitoring**: Tìm kiếm thông tin rò rỉ trên dark web
* **Social Media OSINT**: Phân tích thông tin từ mạng xã hội
* **Vulnerability Scanner Integration**: Kết nối với các scanner như Nuclei, Nmap NSE
* **Cloud Resources Discovery**: Tìm kiếm tài nguyên cloud liên quan (S3, Azure, etc.)

## Giấy phép sử dụng

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Đóng góp

Chúng tôi luôn hoan nghênh các đóng góp! Vui lòng mở issue hoặc pull request để chia sẻ ý tưởng, báo lỗi hoặc cải tiến mã nguồn.

## Lưu ý về Bảo mật và Pháp lý

* **API Keys & Bảo mật**: Không bao giờ commit API keys hoặc thông tin nhạy cảm vào Git. Sử dụng file `.env` và `.gitignore`.
* **Giới hạn yêu cầu**: Các công cụ tìm kiếm, API có giới hạn về số lượng request. Điều chỉnh tham số `--delay` nếu cần.
* **Tài nguyên Vertex AI**: Một số tính năng có thể phát sinh chi phí trên Google Cloud Platform. Kiểm tra quotas và billing của bạn.
* **Pháp lý**: Công cụ này chỉ được sử dụng trên các hệ thống mà bạn có quyền hợp pháp để kiểm thử. Người dùng hoàn toàn chịu trách nhiệm về mọi hành động.