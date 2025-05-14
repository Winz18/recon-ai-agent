import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.port_scanner import scan_ports, get_service_name, get_top_ports


class TestPortScanner(unittest.TestCase):
    """Test cases for port scanner module"""

    def test_get_top_ports(self):
        """Test get_top_ports function with different counts"""
        # Test default top 100 ports
        ports = get_top_ports()
        self.assertEqual(len(ports), 100)
        self.assertEqual(ports[0], 21)  # First port should be 21
        
        # Test with custom count
        ports = get_top_ports(10)
        self.assertEqual(len(ports), 10)
        
        # Test with count larger than available ports
        ports = get_top_ports(1000)
        self.assertTrue(len(ports) >= 100)  # Should return all available ports    def test_get_service_name(self):
        """Test get_service_name function for common ports"""
        # Test common ports - modifying to match case in implementation
        # The function may return lowercase values from socket.getservbyport
        # or uppercase from the hardcoded dictionary
        self.assertEqual(get_service_name(80).upper(), "HTTP")
        self.assertEqual(get_service_name(443).upper(), "HTTPS")
        
        # Test uncommon port should return "unknown"
        self.assertEqual(get_service_name(12345), "unknown")

    @patch('socket.socket')
    def test_scan_tcp_port_open(self, mock_socket):
        """Test scanning an open TCP port"""
        # Setup mock
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        mock_instance.connect_ex.return_value = 0  # 0 means port is open
        
        # Mock hostname resolution
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            result = scan_ports('localhost', ports=[80])
        
        # Check results
        self.assertIn(80, result)
        self.assertTrue(result[80]['open'])
        self.assertIn('service', result[80])

    @patch('socket.socket')
    def test_scan_tcp_port_closed(self, mock_socket):
        """Test scanning a closed TCP port"""
        # Setup mock
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        mock_instance.connect_ex.return_value = 1  # Non-zero means port is closed
        
        # Mock hostname resolution
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            result = scan_ports('localhost', ports=[80])
        
        # Check results
        self.assertEqual(result, {})  # Empty dict as scan_ports only returns open ports

    @patch('socket.socket')
    def test_scan_udp_port(self, mock_socket):
        """Test scanning a UDP port"""
        # Setup mock
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        mock_instance.recvfrom.return_value = (b'data', ('127.0.0.1', 53))
        
        # Mock hostname resolution
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            result = scan_ports('localhost', ports=[53], scan_type='udp')
          # Check results
        self.assertIn(53, result)
        self.assertTrue(result[53]['open'])
        self.assertIn('service', result[53])
        
    def test_invalid_hostname(self):
        """Test with an invalid hostname"""
        import socket
        with patch('socket.gethostbyname', side_effect=socket.gaierror):
            result = scan_ports('invalid-hostname-that-does-not-exist')
        
        # Check results
        self.assertIn('error', result)

    @patch('socket.socket')
    def test_multiple_ports_scan(self, mock_socket):
        """Test scanning multiple ports"""
        # Setup mock
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        
        # First port is open, second is closed
        def connect_ex_side_effect(addr):
            if addr[1] == 80:
                return 0  # Open
            else:
                return 1  # Closed
                
        mock_instance.connect_ex.side_effect = connect_ex_side_effect
        
        # Mock hostname resolution
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            result = scan_ports('localhost', ports=[80, 81])
        
        # Check results
        self.assertIn(80, result)  # Port 80 should be in results
        self.assertNotIn(81, result)  # Port 81 should not be in results (closed)
        self.assertTrue(result[80]['open'])


if __name__ == '__main__':
    unittest.main()
