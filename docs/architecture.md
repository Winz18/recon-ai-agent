# Kiến trúc của AI Pentesting Assistant

Tài liệu này mô tả chi tiết kiến trúc của dự án AI Pentesting Assistant, một hệ thống sử dụng AutoGen Framework và Vertex AI để tự động hóa quá trình footprinting và reconnaissance trong kiểm thử bảo mật.

## Tổng quan Kiến trúc

```
                                  +------------------+
                                  |                  |
                                  |   Main CLI App   |
                                  |                  |
                                  +--------+---------+
                                           |
                                           |
                                           v
+----------------+            +------------+------------+             +----------------+
|                |            |                         |             |                |
|  Configuration +----------->+   Workflow Controller   +------------>+    Reporter    |
|                |            |                         |             |                |
+----------------+            +------------+------------+             +----------------+
                                           |
                                           |
                                           v
                              +------------+------------+
                              |                         |
                              |   AI Agent Orchestrator |
                              |                         |
                              +------------+------------+
                                           |
                    +--------------------+ | +----------------------+
                    |                    | | |                      |
                    v                    v v v                      v
            +-------+------+    +--------+----------+    +---------+----------+
            |              |    |                   |    |                    |
            | Domain Intel |    | Network Recon     |    | OSINT Gathering    |
            | Agent        |    | Agent             |    | Agent              |
            |              |    |                   |    |                    |
            +-------+------+    +--------+----------+    +---------+----------+
                    |                    |                          |
                    |                    |                          |
                    v                    v                          v
            +-------+------+    +--------+----------+    +---------+----------+
            |              |    |                   |    |                    |
            | DNS Tools    |    | Port Scanner      |    | Google Dorking     |
            | WHOIS Tools  |    | Header Analysis   |    | Tech Detection     |
            |              |    |                   |    | Screenshot         |
            +--------------+    +-------------------+    +--------------------+
```

## Các Thành phần Chính

### 1. Main CLI Application

**File:** `main.py`

Điểm vào chính của ứng dụng, cung cấp giao diện dòng lệnh cho người dùng để:
- Cấu hình các tham số reconnaissance
- Chọn workflow cần thực thi
- Chạy các công cụ tách biệt
- Xem và lưu trữ báo cáo

### 2. Configuration Module

**Thư mục:** `config/`

Quản lý tất cả các cài đặt của ứng dụng:
- Cấu hình kết nối đến Vertex AI và AutoGen
- Cài đặt mặc định cho các công cụ
- Quản lý biến môi trường
- Đọc cấu hình từ file `.env`

### 3. AI Agents (AutoGen Framework)

**Thư mục:** `agents/`

Triển khai các agent thông minh được điều phối bởi AutoGen Framework:

- **ReconPlanner Agent:** Lập kế hoạch chiến lược Reconnaissance dựa trên đầu vào của người dùng
- **DomainIntel Agent:** Chuyên về thu thập thông tin liên quan đến tên miền
- **NetworkRecon Agent:** Thực hiện các tác vụ quét mạng và phân tích
- **WebAppRecon Agent:** Phân tích các ứng dụng web và công nghệ
- **OSINTGathering Agent:** Thu thập thông tin từ các nguồn mở
- **Reporter Agent:** Tổng hợp dữ liệu và tạo báo cáo

### 4. Tools Module

**Thư mục:** `tools/`

Tập hợp các công cụ reconnaissance được sử dụng bởi các agent:

- **network.py:** Công cụ DNS lookup, WHOIS lookup
- **web.py:** Phân tích HTTP headers, thông tin bảo mật
- **port_scanner.py:** Quét cổng mở
- **search.py:** Tìm kiếm subdomain
- **google_dorking.py:** Thực hiện Google dorks
- **tech_detector.py:** Phát hiện công nghệ web
- **screenshot.py:** Chụp ảnh website
- **tool_decorator.py:** Decorator để đánh dấu và theo dõi việc sử dụng công cụ

### 5. Workflows Module

**Thư mục:** `workflows/`

Định nghĩa các quy trình reconnaissance chuẩn:

- **standard_recon_workflow.py:** Quy trình đầy đủ, bao gồm tất cả các bước
- **minimal_workflow.py (sắp có):** Quy trình rút gọn, chỉ chạy các công cụ thiết yếu
- **webapp_workflow.py (sắp có):** Tập trung vào ứng dụng web
- **osint_workflow.py (sắp có):** Chỉ sử dụng các công cụ thu thập thông tin mà không tương tác với hệ thống mục tiêu

### 6. Reports & Utilities

**Thư mục:** `reports/` và `utils/`

- **reports/:** Lưu trữ báo cáo dưới dạng JSON và HTML
- **utils/:** Các tiện ích hỗ trợ logging, định dạng dữ liệu, và tiện ích chung

## Luồng Hoạt động

1. Người dùng chạy `main.py` với các tham số cần thiết
2. Hệ thống tải cấu hình và khởi tạo các thành phần
3. Quy trình (workflow) được chọn sẽ được kích hoạt
4. ReconPlanner Agent tạo kế hoạch thu thập thông tin
5. Các Agent chuyên biệt được phân công nhiệm vụ
6. Mỗi Agent sử dụng các công cụ phù hợp để thu thập thông tin
7. Reporter Agent tổng hợp kết quả và tạo báo cáo
8. Báo cáo được lưu trữ và hiển thị cho người dùng

## Extensibility (Khả năng mở rộng)

Hệ thống được thiết kế để dễ dàng mở rộng:

- **Thêm công cụ mới:** Thêm module mới vào thư mục `tools/` và đăng ký trong `__init__.py`
- **Thêm Agent mới:** Triển khai Agent mới trong thư mục `agents/`
- **Thêm Workflow mới:** Tạo quy trình mới trong thư mục `workflows/`

## Vertex AI Integration

Dự án sử dụng Google Cloud Vertex AI để cung cấp năng lực AI cho các Agent:

- **Gemini Models:** Cung cấp khả năng xử lý ngôn ngữ tự nhiên và phân tích
- **Caching:** Lưu trữ kết quả gọi API để tối ưu chi phí

## Hạn chế và Thách thức

- **Rate Limiting:** Nhiều nguồn API có giới hạn số lượng request
- **False Positives:** Kết quả reconnaissance có thể chứa thông tin sai
- **Performance:** Một số công cụ có thể mất nhiều thời gian để thực thi
- **Phụ thuộc vào Internet:** Cần kết nối internet ổn định