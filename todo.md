## Kế Hoạch Nâng Cấp Tổng Thể Dự Án Trợ Lý Pentest AI (AG2 Framework)

### Giai đoạn 1: Củng Cố Nền Tảng và Mở Rộng Công Cụ Hiện Có

Mục tiêu của giai đoạn này là hoàn thiện các tính năng cốt lõi, bổ sung công cụ còn thiếu và chuẩn hóa cấu trúc dự án.

1.  **Hoàn Thiện và Kiểm Thử Các Công Cụ Hiện Tại:**
    * **Rà soát `tools/network.py`, `tools/web.py`, `tools/search.py`:**
        * Đảm bảo tất cả các hàm công cụ đều được bọc bởi decorator `@recon_tool` (từ `tools/tool_decorator.py`) để chuẩn hóa logging và xử lý lỗi.
        * Cải thiện khả năng xử lý lỗi chi tiết hơn cho từng công cụ (ví dụ: lỗi kết nối, timeout, không tìm thấy thông tin).
        * Xem xét bổ sung các tùy chọn nâng cao cho các công cụ hiện có (ví dụ: cho phép chọn loại DNS record cụ thể trong `dns_lookup`).
    * **Viết/Bổ sung Unit Tests:**
        * Mở rộng các test cases trong `tests/test_tools_network.py` và `tests/test_tools_web.py` để bao phủ nhiều trường hợp hơn, bao gồm cả các trường hợp lỗi.
        * Tạo thêm file test cho `tools/search.py` và `tools/tool_decorator.py`.

2.  **Bổ Sung Các Công Cụ Thu Thập Thông Tin Cơ Bản (Theo `todo.md`):**
    * **Port Scanner:**
        * Tạo file `tools/port_scanner.py`.
        * Triển khai hàm `scan_ports(target: str, ports: Optional[List[int]] = None)` sử dụng thư viện như `python-nmap` hoặc `socket` cơ bản để quét các cổng phổ biến (ví dụ: top 100 TCP/UDP ports) hoặc danh sách cổng tùy chỉnh.
        * Đảm bảo tuân thủ nguyên tắc chỉ quét các mục tiêu được phép.
        * Tích hợp vào `Recon_Assistant` và `Tool_Executor_Proxy` trong `main.py` và `workflows/basic_recon.py`.
    * **Google Dorking:**
        * Tạo file `tools/google_dorking.py`.
        * Triển khai hàm `search_google_dorks(domain: str, dorks: Optional[List[str]] = None)` sử dụng `google-api-python-client` (đã có trong `requirements.txt`) hoặc thư viện `googlesearch-python`.
        * Xác định một danh sách các dork phổ biến cho giai đoạn Footprinting (ví dụ: `site:target.com`, `intitle:"index of" site:target.com`, `filetype:pdf site:target.com confidential`).
        * Lưu ý về giới hạn tần suất truy vấn của Google API.
        * Tích hợp vào các agent.
    * **Technology Detector (Phát hiện công nghệ web):**
        * Tạo file `tools/tech_detector.py`.
        * Triển khai hàm `detect_technologies(url: str)` sử dụng các thư viện như `Wappalyzer` (phiên bản Python) hoặc phân tích HTTP headers, nội dung HTML để phát hiện các công nghệ (CMS, framework, web server, ngôn ngữ lập trình).
        * Tích hợp vào các agent.
    * **Screenshot Capture (Chụp ảnh website):**
        * Tạo file `tools/screenshot.py`.
        * Triển khai hàm `capture_website_screenshot(url: str, output_path: str)` sử dụng thư viện như `Selenium` hoặc `Playwright` để chụp ảnh giao diện website.
        * Lưu ý về việc cài đặt webdriver cần thiết.
        * Xem xét cách agent sẽ xử lý và truyền file ảnh (ví dụ: lưu vào thư mục `reports/screenshots` và trả về đường dẫn).

3.  **Tổ Chức Lại Cấu Trúc Dự Án và Agent:**
    * **Chuyên môn hóa Agent:**
        * Thay vì chỉ có `Recon_Assistant` chung, xem xét tạo các AssistantAgent chuyên biệt hơn, ví dụ:
            * `Infrastructure_Recon_Agent`: Tập trung vào DNS, WHOIS, Port Scan.
            * `WebApp_Recon_Agent`: Tập trung vào HTTP Headers, Tech Detection, Subdomain (liên quan đến web app).
            * `OSINT_Agent`: Tập trung vào Google Dorking, tìm kiếm thông tin công khai.
        * Điều này giúp quản lý prompt hệ thống (system message) dễ dàng hơn và agent hoạt động hiệu quả hơn trong phạm vi chuyên môn của mình. [cite: 28]
    * **Cập nhật `main.py` và `workflows/`:**
        * Điều chỉnh luồng làm việc để sử dụng các agent chuyên biệt này.
        * Xem xét sử dụng các mẫu hội thoại AG2 phức tạp hơn (ví dụ: `SequentialChat` cho một chuỗi các bước recon, hoặc `GroupChat` để các agent chuyên biệt cùng thảo luận và đưa ra yêu cầu). [cite: 76, 77]
    * **Quản lý Tools:**
        * Đảm bảo tất cả các hàm tools mới đều được đăng ký với `UserProxyAgent` (hoặc `Tool_Executor_Proxy`). [cite: 3]

### Giai đoạn 2: Nâng Cấp Quy Trình và Tương Tác Agent

Mục tiêu của giai đoạn này là tận dụng sâu hơn các khả năng của AG2 để tạo ra các quy trình thu thập thông tin thông minh và linh hoạt hơn.

1.  **Triển Khai Quy Trình Thu Thập Thông Tin Nâng Cao:**
    * **Sử dụng `GroupChatManager` và `GroupChat`:** [cite: 29]
        * Thiết kế một kịch bản `GroupChat` nơi `ReconPlanner` (đã có trong `agents/recon_planner.py`) đưa ra kế hoạch tổng thể.
        * Các agent chuyên biệt (Infrastructure, WebApp, OSINT) sẽ dựa vào kế hoạch đó, yêu cầu thực thi tool thông qua `Tool_Executor_Proxy`.
        * Các agent có thể trao đổi kết quả tìm được với nhau trong group chat để đưa ra các yêu cầu tiếp theo (ví dụ: WebApp_Recon_Agent tìm thấy một subdomain mới, OSINT_Agent có thể thực hiện Google Dorking trên subdomain đó).
        * Tham khảo tài liệu AG2 về `GroupChat` và cách `GroupChatManager` điều phối lượt nói. [cite: 22, 30, 77]
    * **Sử dụng `SequentialChat` (Hội thoại Tuần tự):** [cite: 76]
        * Đối với các tác vụ có thứ tự rõ ràng (ví dụ: phải tìm subdomain trước rồi mới quét cổng trên các subdomain đó), `SequentialChat` có thể phù hợp.
        * Agent đầu tiên thực hiện nhiệm vụ, sau đó "carryover" (chuyển tiếp ngữ cảnh) kết quả cho agent tiếp theo. [cite: 77]
    * **Khám phá `Swarm Pattern` (Nếu phù hợp):** [cite: 1, 79]
        * Nếu muốn các agent có khả năng tự ủy thác nhiệm vụ cho nhau dựa trên "khả năng" của chúng, `Swarm` pattern có thể được nghiên cứu. [cite: 79, 80] Điều này đòi hỏi các model hỗ trợ "tool calling" tốt. [cite: 80]

2.  **Nâng Cấp `ReconPlanner` Agent:**
    * Hiện tại `agents/recon_planner.py` tạo kế hoạch dựa trên danh sách tool có sẵn.
    * Cải thiện prompt hệ thống của `ReconPlanner` để nó có thể:
        * Phân tích mục tiêu (ví dụ: là một domain chính hay một IP) để đưa ra các bước phù hợp hơn.
        * Đề xuất thứ tự ưu tiên cho các công cụ.
        * Gợi ý cách kết hợp thông tin từ nhiều công cụ.

3.  **Nâng Cấp `ReconReporter` Agent:**
    * Hiện tại `agents/reporter.py` tạo báo cáo Markdown.
    * **Đa dạng định dạng báo cáo:**
        * Bổ sung khả năng xuất báo cáo dưới dạng JSON (để dễ dàng xử lý máy).
        * Xem xét xuất HTML với định dạng thân thiện hơn.
    * **Phân tích sâu hơn:**
        * Cải thiện prompt hệ thống của `ReconReporter` để nó không chỉ liệt kê thông tin mà còn:
            * Cố gắng chỉ ra các điểm yếu tiềm ẩn dựa trên thông tin thu thập được (ví dụ: "HTTP header X-Frame-Options bị thiếu có thể dẫn đến tấn công Clickjacking").
            * Liên kết các thông tin với nhau (ví dụ: "WHOIS cho thấy domain được đăng ký gần đây, kết hợp với việc không có nhiều bản ghi DNS, cho thấy đây có thể là một hệ thống mới triển khai").
    * **Lưu trữ kết quả và báo cáo:**
        * Chuẩn hóa việc lưu báo cáo vào thư mục `reports/` với tên file rõ ràng (ví dụ: `report_<target>_<timestamp>.md`).
        * Xem xét lưu trữ kết quả thô từ các tool (dưới dạng JSON) vào một thư mục riêng để có thể tái sử dụng hoặc phân tích lại sau này.

### Giai đoạn 3: Tối Ưu Hóa, Mở Rộng và Hoàn Thiện

1.  **Tùy Chỉnh và Mở Rộng:**
    * **Hệ thống Plugin cho Tools (Nâng cao):**
        * Nếu dự án phát triển lớn, xem xét một cơ chế để dễ dàng thêm các "tool plugins" mới mà không cần sửa đổi nhiều code lõi. Điều này có thể dựa trên việc đăng ký động các hàm tool.
    * **Giao diện Dòng lệnh (CLI) Hoàn Chỉnh:**
        * Mở rộng `main.py` (hoặc tạo một file CLI riêng) với `argparse` để cung cấp nhiều tùy chọn hơn:
            * Chọn workflow cụ thể để chạy.
            * Chỉ định output format cho báo cáo.
            * Bật/tắt các nhóm công cụ cụ thể.
            * Cấu hình các tham số cho từng tool (ví dụ: danh sách cổng cho port scanner).
    * **Cho phép người dùng định nghĩa quy trình (workflow) riêng:**
        * Có thể thông qua file cấu hình YAML/JSON mô tả chuỗi agent và tool cần chạy.

2.  **Hiệu Suất và Độ Tin Cậy:**
    * **Caching Kết Quả:**
        * Đối với các tool ít thay đổi kết quả (ví dụ: WHOIS), xem xét triển khai caching đơn giản (ví dụ: lưu kết quả vào file và kiểm tra thời gian) để tránh gọi lại không cần thiết và tiết kiệm tài nguyên/API call.
    * **Retry và Xử lý lỗi Nâng cao:**
        * Trong `tool_decorator.py` hoặc trong từng tool, triển khai logic retry cho các lỗi tạm thời (ví dụ: lỗi mạng).
    * **Chạy Song Song (Nếu có thể và an toàn):**
        * Đối với các tool không phụ thuộc nhau, AG2 có thể hỗ trợ các kịch bản chạy song song thông qua cách cấu trúc các cuộc hội thoại và agent. Cần nghiên cứu kỹ tài liệu AG2 về khả năng này.

3.  **Hoàn Thiện Tài Liệu và Hướng Dẫn:**
    * Cập nhật `README.md` chi tiết hơn về các tính năng mới, cách cài đặt, cấu hình và sử dụng các workflow khác nhau.
    * Tạo thêm các file Markdown trong thư mục `docs/` để giải thích kiến trúc, cách thêm tool mới, cách định nghĩa workflow mới.
    * Bổ sung ví dụ sử dụng trong thư mục `examples/` (nếu cần).

### Lưu Ý Quan Trọng Bám Sát AG2:

* **`ConversableAgent`:** Đây là lớp cơ sở. [cite: 1, 30] Khi tạo agent mới, hãy kế thừa từ `ConversableAgent` hoặc các lớp con tiện ích như `AssistantAgent` và `UserProxyAgent`. [cite: 3, 28]
* **`LLMConfig`:** Sử dụng `get_ag2_config_list` từ `config/settings.py` để lấy cấu hình LLM, đảm bảo tính nhất quán. [cite: 103]
* **Đăng ký Hàm (Tools):** Luôn sử dụng `register_function` trên `UserProxyAgent` (hoặc agent thực thi tool) để đăng ký các hàm Python mà `AssistantAgent` có thể yêu cầu. [cite: 3, 115]
* **Thực Thi Mã Lệnh (`code_execution_config`):** [cite: 57]
    * Nếu `UserProxyAgent` chỉ gọi các hàm Python đã đăng ký (tools), hãy đặt `code_execution_config=False`. [cite: 3]
    * Nếu muốn agent có khả năng *tự viết và thực thi* các khối mã Python (ví dụ: để phân tích dữ liệu phức tạp), hãy cấu hình `code_execution_config={"use_docker": True}` để đảm bảo an toàn. [cite: 3, 67, 68] Tham khảo kỹ cảnh báo bảo mật và các phương pháp tốt nhất trong tài liệu AG2 về việc này. [cite: 31, 66, 69]
* **Prompt Hệ Thống (`system_message`):** Thiết kế `system_message` cho các `AssistantAgent` một cách cẩn thận, rõ ràng về vai trò, mục tiêu, các tool có sẵn và định dạng output mong muốn. Đây là yếu tố then chốt để LLM hoạt động hiệu quả. [cite: 28]
* **Termination Message (`is_termination_msg`):** Đảm bảo các agent (đặc biệt là `AssistantAgent`) có cách để kết thúc cuộc hội thoại (ví dụ: trả về "TERMINATE" khi hoàn thành nhiệm vụ). [cite: 3]
* **Human-in-the-Loop (`human_input_mode`):** Sử dụng `human_input_mode` trên `UserProxyAgent` ("ALWAYS", "NEVER", "TERMINATE") để kiểm soát mức độ tương tác của người dùng. [cite: 3, 43]