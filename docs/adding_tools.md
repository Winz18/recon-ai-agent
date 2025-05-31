# Adding New Tools to Recon AI-Agent

This document describes how to add new reconnaissance tools to the Recon AI-Agent system. The project is designed with a modular architecture that allows easy extension with new tools.

## Overview

Each tool in Recon AI-Agent is a Python function that performs a specific reconnaissance task, such as DNS lookup, port scanning, or technology detection. These tools are organized in the `tools/` directory and are registered to be callable by AI agents.

## Step 1: Create a New Tool Function

Create a new Python file in the `tools/` directory or add functions to an existing file if they're functionally related. For example, to create an SSL/TLS analysis tool:

```python
# tools/ssl_analyzer.py
import ssl
import socket
import datetime
from typing import Dict, Any, List, Optional
import OpenSSL

from .tool_decorator import recon_tool

@recon_tool
def analyze_ssl_certificate(domain: str, port: int = 443) -> Dict[str, Any]:
    """
    Analyze SSL/TLS certificate for a domain.
    
    Args:
        domain: Target domain to analyze
        port: Port number (default 443 for HTTPS)
        
    Returns:
        Dict containing SSL certificate information
    """
    try:
        # Create SSL connection
        context = ssl.create_default_context()
        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=domain
        )
        conn.connect((domain, port))
        
        # Get certificate information
        cert = conn.getpeercert()
        
        # Analyze certificate data
        result = {
            "subject": dict(x[0] for x in cert["subject"]),
            "issuer": dict(x[0] for x in cert["issuer"]),
            "version": cert["version"],
            "notBefore": cert["notBefore"],
            "notAfter": cert["notAfter"],
            "serialNumber": cert["serialNumber"],
            "protocol_version": conn.version(),
            "cipher": conn.cipher(),
        }
        
        # Check expiration
        expiry_date = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        current_date = datetime.datetime.utcnow()
        remaining_days = (expiry_date - current_date).days
        
        result["days_until_expiry"] = remaining_days
        result["is_expired"] = remaining_days <= 0
        
        conn.close()
        return result
    except Exception as e:
        return {
            "error": str(e),
            "ssl_info": None
        }

@recon_tool
def check_ssl_vulnerabilities(domain: str, port: int = 443) -> Dict[str, Any]:
    """
    Check for common SSL/TLS vulnerabilities like POODLE, Heartbleed, FREAK, etc.
    
    Args:
        domain: Target domain to check
        port: Port number (default 443)
        
    Returns:
        Dict containing information about potential security vulnerabilities
    """
    # Implementation for vulnerability checks
    # This is a simplified example - real implementation would be more complex
    
    return {
        "poodle_vulnerable": False,
        "heartbleed_vulnerable": False,
        "freak_vulnerable": False,
        "logjam_vulnerable": False,
        "beast_vulnerable": False,
        "supports_tls_1_3": True,
        "cipher_strengths": {
            "strong": ["TLS_AES_256_GCM_SHA384"],
            "medium": [],
            "weak": []
        }
    }
```

### Important Conventions

1. **Use type hints:** Always declare data types for parameters and return values
2. **Provide docstrings:** Clearly describe what the tool does, parameters, and return values
3. **Error handling:** Always catch exceptions to avoid crashing the application
4. **Consistent results:** Return dictionaries with consistent structure
5. **Docker compatibility:** Ensure tools work in containerized environment

## Step 2: Add the recon_tool Decorator

Each tool must be marked with the `@recon_tool` decorator. This decorator adds features such as:

- Logging each time the tool is used
- Measuring execution time
- Storing results for reporting
- Providing callable interface for AI Agents

```python
from .tool_decorator import recon_tool

@recon_tool
def my_new_tool(param1, param2):
    # Tool implementation
    pass
```

## Step 3: Register Tool in __init__.py

To make the new tool importable from the `tools` module, add it to `tools/__init__.py`:

```python
# tools/__init__.py
from .network import dns_lookup, whois_lookup
from .web import get_http_headers, extract_security_headers
from .search import search_subdomains
from .tool_decorator import recon_tool
from .port_scanner import scan_ports
from .google_dorking import search_google_dorks
from .tech_detector import detect_technologies
from .screenshot import capture_website_screenshot
# Add new import
from .ssl_analyzer import analyze_ssl_certificate, check_ssl_vulnerabilities
```

## Step 4: Add Dependencies (if needed)

If the new tool requires external libraries, add them to `requirements.txt`:

```
# Add to requirements.txt
pyOpenSSL>=23.1.1
```

For Docker deployment, you may also need to update the `Dockerfile` if system packages are required:

```dockerfile
# Add to Dockerfile if system packages needed
RUN apt-get update && apt-get install -y \
    # existing packages... \
    openssl-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Step 5: Add Unit Tests

Create a test file in the `tests/` directory to verify the tool works correctly:

```python
# tests/test_tools_ssl_analyzer.py
import unittest
from unittest.mock import patch, MagicMock
from tools import analyze_ssl_certificate, check_ssl_vulnerabilities

class TestSSLAnalyzer(unittest.TestCase):
    
    @patch('tools.ssl_analyzer.ssl.create_default_context')
    def test_analyze_ssl_certificate(self, mock_context):
        # Setup mock
        mock_conn = MagicMock()
        mock_context.return_value.wrap_socket.return_value = mock_conn
        mock_conn.getpeercert.return_value = {
            "subject": ((("commonName", "example.com"),),),
            "issuer": ((("commonName", "Let's Encrypt Authority X3"),),),
            "version": 3,
            "notBefore": "Jan 1 00:00:00 2023 GMT",
            "notAfter": "Dec 31 23:59:59 2023 GMT",
            "serialNumber": "1234567890",
        }
        mock_conn.version.return_value = "TLSv1.3"
        mock_conn.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
        
        # Run test
        result = analyze_ssl_certificate("example.com")
        
        # Check results
        self.assertIn("subject", result)
        self.assertIn("issuer", result)
        self.assertIn("protocol_version", result)
        
    def test_check_ssl_vulnerabilities(self):
        result = check_ssl_vulnerabilities("example.com")
        self.assertIn("poodle_vulnerable", result)
        self.assertIn("heartbleed_vulnerable", result)

    def test_error_handling(self):
        # Test with invalid domain
        result = analyze_ssl_certificate("invalid-domain-12345.com")
        self.assertIn("error", result)
        
if __name__ == "__main__":
    unittest.main()
```

## Step 6: Test in Docker Environment

Always test new tools in the Docker environment:

```bash
# Build updated image
make build

# Test the new tool interactively
make shell

# Inside container, test the tool
python -c "from tools import analyze_ssl_certificate; print(analyze_ssl_certificate('google.com'))"
```

## Step 7: Use in Workflows

Update workflows to use the new tool:

```python
# workflows/standard_recon_workflow.py

# Add import
from tools import analyze_ssl_certificate, check_ssl_vulnerabilities

# In workflow definition, add logic to use the new tool
ssl_info = analyze_ssl_certificate(domain)
ssl_vulns = check_ssl_vulnerabilities(domain)

# Add data to results
results["ssl_analysis"] = {
    "certificate_info": ssl_info,
    "vulnerabilities": ssl_vulns
}
```

## Step 8: Update Documentation

Update the main README.md to include information about the new tool:

```markdown
## 🛠️ Available Tools

- **DNS Reconnaissance**: Analyze DNS records and discover subdomains
- **WHOIS Lookup**: Gather domain registration information
- ... (other existing tools)
- **SSL/TLS Analysis**: Check certificate validity and security configuration
```

## Common Tool Categories

Here are common types of reconnaissance tools:

### 1. Network Tools
- DNS analysis and subdomain discovery
- Port scanning and service detection
- Network topology mapping
- IP geolocation and ASN lookup

### 2. Web Application Tools
- HTTP header analysis
- Technology stack detection
- Security header evaluation
- Content discovery and crawling

### 3. OSINT Tools
- Search engine intelligence
- Social media reconnaissance
- Public database searches
- Domain and certificate transparency

### 4. Infrastructure Tools
- Cloud service detection
- CDN identification
- Load balancer analysis
- SSL/TLS configuration assessment

### 5. Security Tools
- Vulnerability scanning
- Configuration assessment
- Security policy evaluation
- Compliance checking

## Best Practices for Tool Development

### 1. Rate Limiting and Delays
```python
import time
import random

@recon_tool
def api_based_tool(target, delay_range=(1, 3)):
    """Tool that makes API calls with random delays."""
    # Random delay to avoid rate limiting
    time.sleep(random.uniform(*delay_range))
    
    # Tool implementation
    pass
```

### 2. Error Handling and Logging
```python
import logging

logger = logging.getLogger(__name__)

@recon_tool
def robust_tool(target):
    """Tool with comprehensive error handling."""
    try:
        # Tool logic here
        result = perform_reconnaissance(target)
        logger.info(f"Successfully analyzed {target}")
        return result
    except ConnectionError as e:
        logger.warning(f"Connection failed for {target}: {e}")
        return {"error": "connection_failed", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error analyzing {target}: {e}")
        return {"error": "unexpected_error", "details": str(e)}
```

### 3. Configuration and Customization
```python
@recon_tool
def configurable_tool(target, timeout=10, retries=3, custom_headers=None):
    """Tool with configurable parameters."""
    headers = custom_headers or {"User-Agent": "Recon-AI-Agent/1.0"}
    
    for attempt in range(retries):
        try:
            # Tool implementation with timeout
            result = make_request(target, timeout=timeout, headers=headers)
            return result
        except TimeoutError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return {"error": "timeout", "attempts": retries}
```

### 4. Docker-Aware Implementation
```python
import os
import shutil

@recon_tool
def system_dependent_tool(target):
    """Tool that checks for system dependencies."""
    # Check if required system tool exists
    if not shutil.which('nmap'):
        return {"error": "nmap not found", "suggestion": "ensure nmap is installed in container"}
    
    # Check for required files
    wordlist_path = "/app/wordlists/common.txt"
    if not os.path.exists(wordlist_path):
        return {"error": "wordlist not found", "path": wordlist_path}
    
    # Tool implementation
    pass
```

### 5. Data Validation and Sanitization
```python
import re
from urllib.parse import urlparse

@recon_tool
def validated_tool(target):
    """Tool with input validation."""
    # Validate domain format
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, target):
        return {"error": "invalid_domain_format", "target": target}
    
    # Sanitize input
    target = target.lower().strip()
    
    # Tool implementation
    pass
```

## Testing Your Tools

### Unit Testing
```bash
# Run specific tool tests
python -m pytest tests/test_tools_ssl_analyzer.py -v

# Run all tool tests
python -m pytest tests/ -k "test_tools" -v
```

### Integration Testing
```bash
# Test in Docker environment
./docker-run.sh --build -d example.com -w standard

# Test with Make
make test
```

### Manual Testing
```bash
# Interactive testing
make shell

# Test individual tools
python -c "
from tools import analyze_ssl_certificate
result = analyze_ssl_certificate('github.com')
print(result)
"
```

## Tool Performance Considerations

1. **Async Operations**: For I/O bound tools, consider async implementations
2. **Caching**: Implement caching for expensive operations
3. **Resource Usage**: Monitor memory and CPU usage in containers
4. **Timeout Management**: Always implement timeouts for network operations
5. **Parallel Execution**: Design tools to work well in parallel workflows

## Security Considerations

1. **Input Validation**: Always validate and sanitize inputs
2. **Output Sanitization**: Ensure outputs don't contain sensitive data
3. **Network Security**: Be aware of network isolation in containers
4. **Credential Management**: Never hardcode credentials in tools
5. **Legal Compliance**: Ensure tools comply with terms of service and legal requirements

Following these guidelines will help you create robust, reliable tools that integrate seamlessly with the Recon AI-Agent ecosystem and work effectively in both development and production Docker environments.