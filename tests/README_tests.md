# Kiểm thử công cụ thu thập thông tin cơ bản

Tài liệu này mô tả cách kiểm thử các công cụ thu thập thông tin mới được thêm vào:
1. Port Scanner
2. Google Dorking
3. Technology Detector
4. Website Screenshot

## 1. Kiểm thử tự động (Unit Tests)

Để chạy tất cả các unit test cho các công cụ mới:

```
cd lab-ai-agent
python -m tests.test_new_tools
```

Hoặc sử dụng script `test_tools.py` với cờ `--unittest`:

```
python test_tools.py --unittest
```

## 2. Kiểm thử thủ công

Bạn có thể kiểm thử từng công cụ riêng biệt sử dụng script `test_tools.py`:

### Kiểm thử Port Scanner

```
python test_tools.py --ports -d example.com
```

### Kiểm thử Google Dorking

```
python test_tools.py --dorking -d example.com
```

### Kiểm thử Technology Detector

```
python test_tools.py --tech -u https://example.com
```

### Kiểm thử Website Screenshot

```
python test_tools.py --screenshot -u https://example.com
```

### Kiểm thử tất cả công cụ

```
python test_tools.py --all -d example.com -u https://example.com
```

## 3. Cấu trúc mã kiểm thử

Mỗi công cụ có một file kiểm thử riêng:

- `test_tools_port_scanner.py`: Kiểm thử cho Port Scanner
- `test_tools_google_dorking.py`: Kiểm thử cho Google Dorking
- `test_tools_tech_detector.py`: Kiểm thử cho Technology Detector
- `test_tools_screenshot.py`: Kiểm thử cho Website Screenshot

File `test_new_tools.py` tổng hợp và chạy tất cả kiểm thử.

## 4. Lưu ý quan trọng

- Để chạy `test_tools_screenshot.py`, bạn cần cài đặt Playwright hoặc Selenium.
- Để sử dụng Google Dorking đầy đủ, bạn cần cung cấp Google API key và Custom Search Engine ID.
- Port Scanner có thể bị chặn bởi firewall hoặc IDS/IPS, hãy chỉ quét các hệ thống bạn được phép.

## 5. Cài đặt các phụ thuộc cho kiểm thử

```
pip install -r requirements.txt
pip install playwright selenium
playwright install  # Cài đặt trình duyệt cho Playwright
```
