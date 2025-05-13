import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Add root project directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.tool_decorator import recon_tool

class TestToolDecorator(unittest.TestCase):
    """Test the recon_tool decorator functionality"""
    
    @patch('tools.tool_decorator.logger')
    def test_decorator_successful_execution(self, mock_logger):
        """Test decorator with successful function execution"""
        # Create a simple function and decorate it
        @recon_tool
        def sample_function(arg1, arg2="default"):
            return {"result": f"{arg1}-{arg2}"}
        
        # Call the function
        result = sample_function("test", arg2="value")
        
        # Check the result
        self.assertEqual(result, {"result": "test-value"})
        
        # Verify logging
        mock_logger.info.assert_called()
        # Expected to be called with function name and args
        self.assertTrue(mock_logger.info.call_args_list[0][0][0].startswith("Executing sample_function"))
        # Should log completion
        self.assertTrue(mock_logger.info.call_args_list[1][0][0].startswith("sample_function completed"))
    
    @patch('tools.tool_decorator.logger')
    def test_decorator_with_exception(self, mock_logger):
        """Test decorator with function that raises an exception"""
        # Create a function that raises an exception
        @recon_tool
        def failing_function():
            raise ValueError("Test error")
        
        # Call the function
        result = failing_function()
        
        # Check the error result format
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], True)
        self.assertEqual(result["tool"], "failing_function")
        self.assertEqual(result["message"], "Test error")
        
        # Verify logging
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()
    
    @patch('tools.tool_decorator.time.time')
    @patch('tools.tool_decorator.logger')
    def test_decorator_execution_time(self, mock_logger, mock_time):
        """Test that execution time is logged correctly"""
        # Mock time.time() to return controlled values
        mock_time.side_effect = [10.0, 12.5]  # 2.5 seconds difference
        
        # Create a simple function
        @recon_tool
        def timed_function():
            return {"result": "success"}
        
        # Call the function
        result = timed_function()
        
        # Check the result
        self.assertEqual(result, {"result": "success"})
        
        # Verify time logging
        completion_log = mock_logger.info.call_args_list[1][0][0]
        self.assertIn("2.50s", completion_log)
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function's metadata"""
        # Create a function with docstring and annotations
        @recon_tool
        def metadata_function(param: str) -> dict:
            """Test function docstring"""
            return {"result": param}
        
        # Check that metadata is preserved
        self.assertEqual(metadata_function.__name__, "metadata_function")
        self.assertIn("Test function docstring", metadata_function.__doc__)
        self.assertEqual(metadata_function.__annotations__["param"], str)
        self.assertEqual(metadata_function.__annotations__["return"], dict)

if __name__ == "__main__":
    unittest.main()
