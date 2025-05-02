# Pentest AG2 Tool - Footprinting & Reconnaissance

Công cụ hỗ trợ Pentester trong giai đoạn Footprinting và Reconnaissance sử dụng AI Agent (AG2 Framework) và triển khai trên Google Cloud Vertex AI.

## Tính năng hiện có

* **Thu thập thông tin DNS**: Tra cứu các bản ghi A, AAAA, MX, NS, TXT của tên miền
* **Tra cứu thông tin WHOIS**: Lấy thông tin đăng ký tên miền
* **AI Agent tự động**: Khả năng lập kế hoạch và thực hiện reconnaissance đơn giản bằng AG2 Framework

## Công nghệ sử dụng

* **Python:** Ngôn ngữ lập trình chính
* **AG2 Framework:** Framework xây dựng và điều phối AI Agent (autogen)
* **Google Cloud Vertex AI:** Nền tảng để chạy và quản lý AI Agent
    * Vertex AI SDK for Python 
    * Gemini Models (đang sử dụng gemini-2.5-pro-preview-03-25)
* **Các thư viện Python khác:** `dnspython`, `python-whois`, `requests`, `python-dotenv`

## Cài đặt

1.  **Clone repository:**
    ```bash
    git clone <your-repo-url>
    cd lab-ai-agent
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

* **Chạy quy trình reconnaissance cơ bản:**
    ```bash
    python main.py
    ```
    Script này khởi tạo AI Agent để thực hiện phân tích DNS và WHOIS cho tên miền đã cấu hình.

## Cấu trúc thư mục

* **agents/**: Chứa các module liên quan đến AI agent
* **config/**: Cấu hình ứng dụng và kết nối đến Vertex AI
* **notebooks/**: Jupyter notebooks để kiểm thử tính năng
* **tests/**: Unit tests
* **tools/**: Các công cụ reconnaissance (DNS, WHOIS)
* **utils/**: Tiện ích và các hàm hỗ trợ
* **workflows/**: Các quy trình reconnaissance định sẵn

## Các tính năng sắp có

* Liệt kê Subdomain (sử dụng các kỹ thuật passive/active)
* Kiểm tra thông tin Header của Web Server
* Tìm kiếm thông tin trên các công cụ tìm kiếm (Google Search, Shodan,...)
* Quét cổng cơ bản (nếu được phép)
* Tổng hợp và báo cáo kết quả chi tiết hơn bởi AI Agent

## Lưu ý về Bảo mật và Pháp lý

* **API Keys:** Không bao giờ commit API keys hoặc thông tin nhạy cảm vào Git. Sử dụng file `.env` và `.gitignore`.
* **Thực thi Tool:** Các tool thực hiện tương tác mạng phải được sử dụng một cách có trách nhiệm và **chỉ trên các mục tiêu bạn có quyền hợp pháp để kiểm thử**. Luôn tuân thủ luật pháp và quy tắc ứng xử (Rules of Engagement) khi thực hiện pentest. Công cụ này được cung cấp cho mục đích giáo dục và nghiên cứu. Người sử dụng hoàn toàn chịu trách nhiệm về hành động của mình.