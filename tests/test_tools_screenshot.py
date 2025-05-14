import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.screenshot import capture_website_screenshot, check_webdriver_requirements


class TestScreenshotTool(unittest.TestCase):
    """Test cases for Website Screenshot module"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_url = "https://example.com"
        self.test_output_dir = os.path.join(os.path.dirname(__file__), "test_screenshots")
        
        # Create test directory if it doesn't exist
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove any test screenshots
        for file in os.listdir(self.test_output_dir):
            if file.endswith(".png"):
                os.remove(os.path.join(self.test_output_dir, file))
        
        # Try to remove the directory
        if os.path.exists(self.test_output_dir):
            try:
                os.rmdir(self.test_output_dir)
            except:
                pass  # Directory not empty, leave it
    
    @patch('tools.screenshot._capture_with_playwright')
    def test_capture_with_playwright(self, mock_playwright):
        """Test screenshot capture using Playwright"""
        # Setup mock
        expected_result = {
            "success": True,
            "screenshot_path": os.path.join(self.test_output_dir, "example.com_20250514-120000.png"),
            "method": "playwright"
        }
        mock_playwright.return_value = expected_result
        
        # Call the function
        result = capture_website_screenshot(
            url=self.test_url,
            output_path=self.test_output_dir
        )
        
        # Verify the function was called with correct parameters
        mock_playwright.assert_called_once()
        args = mock_playwright.call_args[0]
        self.assertEqual(args[0], self.test_url)
        self.assertTrue(args[1].endswith(".png"))
        
        # Check result
        self.assertEqual(result, expected_result)
    
    @patch('tools.screenshot._capture_with_playwright', side_effect=ImportError("Playwright not installed"))
    @patch('tools.screenshot._capture_with_selenium')
    def test_fallback_to_selenium(self, mock_selenium, mock_playwright):
        """Test fallback to Selenium when Playwright is not available"""
        # Setup mock
        expected_result = {
            "success": True,
            "screenshot_path": os.path.join(self.test_output_dir, "example.com_20250514-120000.png"),
            "method": "selenium"
        }
        mock_selenium.return_value = expected_result
        
        # Call the function
        result = capture_website_screenshot(
            url=self.test_url,
            output_path=self.test_output_dir
        )
        
        # Verify both methods were called correctly
        mock_playwright.assert_called_once()
        mock_selenium.assert_called_once()
        
        # Check result
        self.assertEqual(result, expected_result)
    
    @patch('tools.screenshot._capture_with_playwright', side_effect=ImportError)
    @patch('tools.screenshot._capture_with_selenium', side_effect=ImportError)
    def test_both_methods_unavailable(self, mock_selenium, mock_playwright):
        """Test handling when both screenshot methods are unavailable"""
        # Call the function
        result = capture_website_screenshot(
            url=self.test_url,
            output_path=self.test_output_dir
        )
        
        # Check error message
        self.assertIn("error", result)
        self.assertTrue("Neither Playwright nor Selenium is installed" in result["error"])
    
    @patch('playwright.sync_api.sync_playwright')
    def test_playwright_screenshot_implementation(self, mock_playwright_import):
        """Test the actual implementation of _capture_with_playwright"""
        # Import function directly
        from tools.screenshot import _capture_with_playwright
        
        # Setup complex mock for the playwright library
        playwright_instance = MagicMock()
        browser_type = MagicMock()
        browser = MagicMock()
        context = MagicMock()
        page = MagicMock()
        
        mock_playwright_import.return_value.__enter__.return_value = playwright_instance
        playwright_instance.chromium = browser_type
        browser_type.launch.return_value = browser
        browser.new_context.return_value = context
        context.new_page.return_value = page
        
        # Set the test filename
        test_filename = os.path.join(self.test_output_dir, "test.png")
        
        # Call the function
        result = _capture_with_playwright(
            self.test_url,
            test_filename,
            1280, 800,
            True, 2, 30,
            True
        )
        
        # Check that all methods were called correctly
        browser_type.launch.assert_called_once()
        browser.new_context.assert_called_once()
        context.new_page.assert_called_once()
        page.goto.assert_called_once_with(self.test_url)
        page.wait_for_load_state.assert_called_once()
        page.screenshot.assert_called_once()
        
        # Check result structure
        self.assertIn("success", result)
        self.assertIn("screenshot_path", result)
        self.assertIn("method", result)
        self.assertEqual(result["method"], "playwright")
    
    def test_check_webdriver_requirements(self):
        """Test checking for webdriver requirements"""
        # Call the function
        result = check_webdriver_requirements()
        
        # Check that it returns a dictionary with the expected keys
        self.assertIsInstance(result, dict)
        self.assertIn("selenium", result)
        self.assertIn("playwright", result)
        self.assertIn("chrome", result)
        self.assertIn("firefox", result)


if __name__ == '__main__':
    unittest.main()
