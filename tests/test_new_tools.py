import os
import sys
import unittest

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import các test cases
from test_tools_port_scanner import TestPortScanner
from test_tools_google_dorking import TestGoogleDorking
from test_tools_tech_detector import TestTechDetector
from test_tools_screenshot import TestScreenshotTool

def run_tests():
    # Tạo test suite cho tất cả các test cases
    test_suite = unittest.TestSuite()
    
    # Thêm các test cases vào test suite sử dụng TestLoader (thay vì makeSuite để tránh cảnh báo)
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestPortScanner))
    test_suite.addTest(loader.loadTestsFromTestCase(TestGoogleDorking))
    test_suite.addTest(loader.loadTestsFromTestCase(TestTechDetector))
    test_suite.addTest(loader.loadTestsFromTestCase(TestScreenshotTool))
    
    # Chạy các test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
