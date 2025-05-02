import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

def recon_tool(func: Callable) -> Callable:
    """
    Decorator cho các hàm tool trong dự án.
    Thêm logging, thời gian thực thi và xử lý ngoại lệ.
    
    Args:
        func: Hàm tool cần được trang trí
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        tool_name = func.__name__
        start_time = time.time()
        
        # Log bắt đầu thực thi
        arg_str = ", ".join([f"{a}" for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
        logger.info(f"Executing {tool_name}({arg_str})")
        
        try:
            # Thực thi tool
            result = func(*args, **kwargs)
            
            # Log thời gian thực thi
            duration = time.time() - start_time
            logger.info(f"{tool_name} completed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            # Log lỗi
            duration = time.time() - start_time
            logger.error(f"{tool_name} failed after {duration:.2f}s: {str(e)}")
            
            # Trả về thông báo lỗi dạng dictionary để AI Agent có thể xử lý
            return {
                "error": True,
                "tool": tool_name,
                "message": str(e)
            }
            
    return wrapper