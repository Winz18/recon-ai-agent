import os
import time
from typing import Optional, Dict, Union, Annotated
from pathlib import Path
from .tool_decorator import recon_tool

@recon_tool
def capture_website_screenshot(
    url: Annotated[str, "URL of the website to capture"],
    output_path: Annotated[str, "Directory path where to save the screenshot"], 
    width: Annotated[int, "Browser viewport width"] = 1280,
    height: Annotated[int, "Browser viewport height"] = 800,
    fullpage: Annotated[bool, "Whether to capture the full page or just the viewport"] = True,
    wait_time: Annotated[float, "Time to wait after page load before screenshot (seconds)"] = 2.0,
    timeout: Annotated[int, "Page load timeout in seconds"] = 30,
    headless: Annotated[bool, "Run browser in headless mode"] = True
) -> Dict[str, Union[str, bool]]:
    """
    Captures a screenshot of a website using Selenium or Playwright.
    
    Args:
        url: URL of the website to capture
        output_path: Directory path where to save the screenshot
        width: Browser viewport width
        height: Browser viewport height
        fullpage: Whether to capture the full page or just the viewport
        wait_time: Time to wait after page load before screenshot (seconds)
        timeout: Page load timeout in seconds
        headless: Run browser in headless mode
        
    Returns:
        Dictionary with screenshot path and status information
    """
    # Create directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    # Generate filename based on URL
    domain = url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
    domain = domain.replace('/', '_').replace(':', '_').replace('?', '_').replace('=', '_')
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{domain}_{timestamp}.png"
    full_path = os.path.join(output_path, filename)
    
    # First try Playwright if available
    try:
        return _capture_with_playwright(url, full_path, width, height, fullpage, wait_time, timeout, headless)
    except ImportError:
        # Fall back to Selenium
        try:
            return _capture_with_selenium(url, full_path, width, height, fullpage, wait_time, timeout, headless)
        except ImportError:
            return {"error": "Neither Playwright nor Selenium is installed. Install with 'pip install playwright selenium'"}
        
def _capture_with_playwright(url, full_path, width, height, fullpage, wait_time, timeout, headless):
    """Capture screenshot using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser_type = p.chromium
            browser = browser_type.launch(headless=headless)
            
            # Create a new context with viewport
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            
            # Set timeout
            page.set_default_timeout(timeout * 1000)  # milliseconds
            
            # Navigate to page
            try:
                page.goto(url)
                
                # Wait for network to be idle (or timeout)
                page.wait_for_load_state("networkidle", timeout=timeout * 1000)
                
                # Additional wait time
                time.sleep(wait_time)
                
                # Take screenshot
                page.screenshot(path=full_path, full_page=fullpage)
                
                browser.close()
                
                return {
                    "success": True,
                    "screenshot_path": full_path,
                    "method": "playwright"
                }
                
            except Exception as e:
                browser.close()
                return {"error": f"Playwright screenshot failed: {str(e)}"}
    
    except ImportError:
        raise ImportError("Playwright not installed")
    except Exception as e:
        return {"error": f"Playwright error: {str(e)}"}

def _capture_with_selenium(url, full_path, width, height, fullpage, wait_time, timeout, headless):
    """Capture screenshot using Selenium"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")  # new headless mode for Chrome
        chrome_options.add_argument("--disable-gpu")  # Required for Windows
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        try:
            # Navigate to the URL
            driver.get(url)
            
            # Wait for page to load
            time.sleep(wait_time)
            
            # Take screenshot
            if fullpage:
                # For fullpage, we need to adjust the screenshot method
                # Get the height of the page
                height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight);")
                # Set window size to capture full page
                driver.set_window_size(width, height)
                time.sleep(0.5)  # Brief pause for resize
            
            # Take screenshot
            driver.save_screenshot(full_path)
            
            driver.quit()
            
            return {
                "success": True,
                "screenshot_path": full_path,
                "method": "selenium"
            }
            
        except TimeoutException:
            driver.quit()
            return {"error": "Page load timed out"}
        except Exception as e:
            driver.quit()
            return {"error": f"Selenium screenshot failed: {str(e)}"}
    
    except ImportError:
        raise ImportError("Selenium not installed")
    except Exception as e:
        return {"error": f"Selenium error: {str(e)}"}

def check_webdriver_requirements():
    """
    Check if the necessary webdriver requirements are installed
    
    Returns:
        Dictionary with status of available tools
    """
    requirements = {
        "selenium": False,
        "playwright": False,
        "chrome": False,
        "firefox": False
    }
    
    # Check Selenium
    try:
        import selenium
        requirements["selenium"] = True
    except ImportError:
        pass
    
    # Check Playwright
    try:
        import playwright
        requirements["playwright"] = True
    except ImportError:
        pass
    
    # Check if Chrome webdriver is available (simple check)
    try:
        import shutil
        chrome_path = shutil.which("chrome") or shutil.which("google-chrome")
        requirements["chrome"] = bool(chrome_path)
    except:
        pass
        
    # Check if Firefox is available (simple check)
    try:
        import shutil
        firefox_path = shutil.which("firefox")
        requirements["firefox"] = bool(firefox_path)
    except:
        pass
        
    return requirements
