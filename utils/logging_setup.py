import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 3
) -> logging.Logger:
    """
    Cài đặt logging cho ứng dụng.
    
    Args:
        log_level: Mức độ logging (INFO, DEBUG...)
        log_file: Đường dẫn tới file log, None nếu chỉ log ra console
        max_file_size: Kích thước tối đa của file log
        backup_count: Số lượng file log backup giữ lại
        
    Returns:
        Logger đã cấu hình
    """
    # Tạo formatter với định dạng chuẩn
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Cấu hình root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Xóa tất cả handlers cũ nếu có
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    # Thêm handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Thêm file handler nếu được chỉ định
    if log_file:
        # Đảm bảo thư mục chứa file log tồn tại
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Tạo rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger cho module cụ thể.
    
    Args:
        name: Tên của logger, thường là __name__
        
    Returns:
        Logger đã được cấu hình
    """
    return logging.getLogger(name)