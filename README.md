# AI Pentesting Assistant - Footprinting & Reconnaissance

Công cụ hỗ trợ Pentester trong giai đoạn Footprinting và Reconnaissance sử dụng AI Agent (AutoGen Framework) và triển khai trên Google Cloud Vertex AI.

## Tính năng hiện có

* **Thu thập thông tin DNS**: Tra cứu các bản ghi A, AAAA, MX, NS, TXT của tên miền
* **Tra cứu thông tin WHOIS**: Lấy thông tin đăng ký tên miền
* **Quét cổng cơ bản**: Kiểm tra các cổng thông dụng đang mở trên máy chủ đích
* **AI Agent tự động**: Khả năng lập kế hoạch và thực hiện reconnaissance tự động bằng AutoGen Framework
* **Tổng hợp báo cáo**: Tạo báo cáo tổng hợp về các phát hiện bảo mật

## Công nghệ sử dụng

* **Python:** Ngôn ngữ lập trình chính
* **AutoGen Framework:** Framework xây dựng và điều phối AI Agent
* **Google Cloud Vertex AI:** Nền tảng để chạy và quản lý AI Agent
    * Vertex AI SDK for Python 
    * Gemini Models
* **Các thư viện Python khác:** `dnspython`, `python-whois`, `requests`, `python-nmap`, `python-dotenv`

## Cài đặt

1.  **Clone repository:**
    ```bash
    git clone https://github.com/yourusername/ai-pentesting-assistant.git
    cd ai-pentesting-assistant
    ```

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
        * `GOOGLE_PROJECT_ID`: ID của dự án Google Cloud
        * `GOOGLE_REGION`: Region của Google Cloud (vd: `us-central1`)
        * `TARGET_DOMAIN`: Tên miền mặc định để phân tích
    * Thiết lập Google Cloud Authentication: Chạy lệnh `gcloud auth application-default login`

## Sử dụng

* **Chạy quy trình reconnaissance tự động:**
    ```bash
    python main.py --domain example.com
    ```

* **Chạy các công cụ riêng lẻ:**
    ```bash
    python tools/dns_lookup.py --domain example.com
    python tools/whois_lookup.py --domain example.com
    python tools/port_scanner.py --target 192.168.1.1
    ```

## Cấu trúc thư mục

* **agents/**: Chứa các module liên quan đến AI agent
* **config/**: Cấu hình ứng dụng và kết nối đến Vertex AI
* **notebooks/**: Jupyter notebooks để kiểm thử tính năng
* **reports/**: Lưu trữ các báo cáo tự động tạo
* **tests/**: Unit tests
* **tools/**: Các công cụ reconnaissance (DNS, WHOIS, Port Scanner)
* **utils/**: Tiện ích và các hàm hỗ trợ
* **workflows/**: Các quy trình reconnaissance định sẵn

## Các tính năng sắp có

* Liệt kê Subdomain (sử dụng các kỹ thuật passive/active)
* Kiểm tra thông tin Header của Web Server
* Tìm kiếm thông tin trên các công cụ tìm kiếm (Google Search, Shodan,...)
* Phân tích lỗ hổng bảo mật cơ bản
* Tạo đề xuất khắc phục thông qua AI

## Lưu ý về Bảo mật và Pháp lý

* **API Keys:** Không bao giờ commit API keys hoặc thông tin nhạy cảm vào Git. Sử dụng file `.env` và `.gitignore`.
* **Thực thi Tool:** Các tool thực hiện tương tác mạng phải được sử dụng một cách có trách nhiệm và **chỉ trên các mục tiêu bạn có quyền hợp pháp để kiểm thử**. Luôn tuân thủ luật pháp và quy tắc ứng xử (Rules of Engagement) khi thực hiện pentest. Công cụ này được cung cấp cho mục đích giáo dục và nghiên cứu. Người sử dụng hoàn toàn chịu trách nhiệm về hành động của mình.