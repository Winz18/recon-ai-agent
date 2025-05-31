# Defining New Workflows in Recon AI-Agent

This document describes how to create new workflows in the Recon AI-Agent system to automate different reconnaissance processes.

## Overview of Workflows

A workflow in Recon AI-Agent is a complete reconnaissance process that includes:

1. **Planning** - Define objectives and methodologies
2. **Data Collection** - Use multiple tools to gather intelligence
3. **Data Analysis** - Process and correlate information
4. **Reporting** - Aggregate findings into actionable intelligence

Workflows are stored in the `workflows/` directory and can be called from the main command-line interface.

## Step 1: Create a New Workflow File

Create a new Python file in the `workflows/` directory. For example, to create a workflow focused on web application analysis:

```python
# workflows/webapp_security_workflow.py

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime

# Import necessary agents
from agents import (
    DomainIntelAgent,
    WebAppReconAgent, 
    ReconReporter
)

# Import tools
from tools import (
    dns_lookup,
    get_http_headers,
    extract_security_headers,
    detect_technologies,
    capture_website_screenshot,
    scan_ports,
    check_ssl_vulnerabilities
)

# Import configuration
from config.settings import get_ag2_config_list

# Setup logging
logger = logging.getLogger(__name__)

def run_webapp_security_workflow(
    target_domain: str,
    use_ai_agents: bool = True,
    ag2_config: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
    output_format: str = "markdown"
) -> Dict[str, Any]:
    """
    Execute a comprehensive web application security assessment workflow.
    
    Args:
        target_domain: Target domain to analyze
        use_ai_agents: Whether to use AI agents or just run basic tools
        ag2_config: AutoGen configuration (if using AI agents)
        verbose: Show detailed information
        output_format: Report format (markdown, html, json)
        
    Returns:
        Dict containing analysis results
    """
    
    results = {
        "target": target_domain,
        "workflow": "webapp_security",
        "timestamp": datetime.now().isoformat(),
        "findings": {},
        "security_score": 0,
        "recommendations": []
    }
    
    if verbose:
        logger.info(f"Starting web application security analysis for {target_domain}")
    
    # Basic tool execution without AI agents
    if not use_ai_agents:
        results["findings"] = execute_basic_tools(target_domain, verbose)
        results["security_score"] = calculate_security_score(results["findings"])
        results["recommendations"] = generate_recommendations(results["findings"])
        return results
    
    # AI-driven analysis
    else:
        if ag2_config is None:
            ag2_config = get_ag2_config_list()[0]
        
        # Initialize agents
        domain_agent = DomainIntelAgent(config_list=ag2_config)
        webapp_agent = WebAppReconAgent(config_list=ag2_config)
        reporter = ReconReporter(config_list=ag2_config)
        
        # Execute AI-driven workflow
        results["findings"] = execute_ai_workflow(
            target_domain, domain_agent, webapp_agent, reporter, verbose
        )
        
        # Generate final report
        final_report = reporter.generate_comprehensive_report(
            results, output_format=output_format
        )
        
        return final_report

def execute_basic_tools(target_domain: str, verbose: bool = False) -> Dict[str, Any]:
    """Execute basic reconnaissance tools without AI agents."""
    findings = {}
    
    if verbose:
        logger.info("Executing DNS analysis...")
    
    # DNS Analysis
    dns_results = dns_lookup(target_domain)
    findings["dns_info"] = dns_results
    
    # HTTP Headers Analysis
    if verbose:
        logger.info("Analyzing HTTP headers...")
    
    headers_results = get_http_headers(f"https://{target_domain}")
    findings["http_headers"] = headers_results
    
    # Security Headers Analysis
    security_headers = extract_security_headers(headers_results)
    findings["security_headers"] = security_headers
    
    # Technology Detection
    if verbose:
        logger.info("Detecting technologies...")
    
    tech_results = detect_technologies(f"https://{target_domain}")
    findings["technologies"] = tech_results
    
    # SSL/TLS Analysis
    if verbose:
        logger.info("Analyzing SSL/TLS configuration...")
    
    ssl_results = check_ssl_vulnerabilities(target_domain)
    findings["ssl_analysis"] = ssl_results
    
    # Port Scanning (limited to web ports)
    if verbose:
        logger.info("Scanning web ports...")
    
    port_results = scan_ports(target_domain, ports="80,443,8080,8443")
    findings["port_scan"] = port_results
    
    # Website Screenshot
    if verbose:
        logger.info("Capturing website screenshot...")
    
    screenshot_path = capture_website_screenshot(f"https://{target_domain}")
    findings["screenshot"] = screenshot_path
    
    return findings

def execute_ai_workflow(
    target_domain: str,
    domain_agent: DomainIntelAgent,
    webapp_agent: WebAppReconAgent,
    reporter: ReconReporter,
    verbose: bool = False
) -> Dict[str, Any]:
    """Execute AI-driven analysis workflow."""
    
    if verbose:
        logger.info("Starting AI-driven workflow...")
    
    # Create analysis plan
    analysis_plan = {
        "target": target_domain,
        "objectives": [
            "Identify web technologies and frameworks",
            "Assess security header configuration",
            "Analyze SSL/TLS implementation",
            "Detect potential vulnerabilities",
            "Evaluate overall security posture"
        ],
        "methodologies": [
            "Passive reconnaissance",
            "HTTP header analysis",
            "SSL/TLS assessment",
            "Technology fingerprinting",
            "Security configuration review"
        ]
    }
    
    # Domain intelligence gathering
    domain_agent.start_analysis(target_domain)
    domain_findings = domain_agent.get_intelligence()
    
    # Web application analysis
    webapp_agent.analyze_webapp(target_domain, analysis_plan)
    webapp_findings = webapp_agent.get_security_assessment()
    
    # Combine findings
    combined_findings = {
        "domain_intelligence": domain_findings,
        "webapp_assessment": webapp_findings
    }
    
    return combined_findings

def calculate_security_score(findings: Dict[str, Any]) -> int:
    """Calculate overall security score based on findings."""
    score = 100
    
    # Deduct points for missing security headers
    security_headers = findings.get("security_headers", {})
    missing_headers = [
        "Content-Security-Policy",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Strict-Transport-Security"
    ]
    
    for header in missing_headers:
        if header not in security_headers:
            score -= 10
    
    # Deduct points for SSL/TLS issues
    ssl_analysis = findings.get("ssl_analysis", {})
    if ssl_analysis.get("vulnerabilities", {}).get("weak_ciphers"):
        score -= 15
    if ssl_analysis.get("certificate", {}).get("days_until_expiry", 999) < 30:
        score -= 10
    
    # Deduct points for open ports
    port_scan = findings.get("port_scan", {})
    open_ports = port_scan.get("open_ports", [])
    unnecessary_ports = [port for port in open_ports if port not in [80, 443]]
    score -= len(unnecessary_ports) * 5
    
    return max(0, score)

def generate_recommendations(findings: Dict[str, Any]) -> List[str]:
    """Generate security recommendations based on findings."""
    recommendations = []
    
    # Security headers recommendations
    security_headers = findings.get("security_headers", {})
    if "Content-Security-Policy" not in security_headers:
        recommendations.append(
            "Implement Content-Security-Policy header to prevent XSS attacks"
        )
    
    if "Strict-Transport-Security" not in security_headers:
        recommendations.append(
            "Enable HTTP Strict Transport Security (HSTS) header"
        )
    
    if "X-Frame-Options" not in security_headers:
        recommendations.append(
            "Add X-Frame-Options header to prevent clickjacking attacks"
        )
    
    # SSL/TLS recommendations
    ssl_analysis = findings.get("ssl_analysis", {})
    if ssl_analysis.get("vulnerabilities", {}).get("weak_ciphers"):
        recommendations.append(
            "Disable weak SSL/TLS cipher suites and protocols"
        )
    
    cert_info = ssl_analysis.get("certificate", {})
    if cert_info.get("days_until_expiry", 999) < 30:
        recommendations.append(
            "Renew SSL certificate - expires soon"
        )
    
    # Port security recommendations
    port_scan = findings.get("port_scan", {})
    open_ports = port_scan.get("open_ports", [])
    unnecessary_ports = [port for port in open_ports if port not in [80, 443]]
    if unnecessary_ports:
        recommendations.append(
            f"Review and close unnecessary open ports: {', '.join(map(str, unnecessary_ports))}"
        )
    
    return recommendations
```

## Step 2: Register Workflow in __init__.py

Update the `workflows/__init__.py` file to register the new workflow:

```python
# workflows/__init__.py
from .standard_recon_workflow import run_standard_recon
from .quick_workflow import run_quick_recon
from .webapp_security_workflow import run_webapp_security_workflow
from .comprehensive_workflow import run_comprehensive_recon

__all__ = [
    'run_standard_recon',
    'run_quick_recon', 
    'run_webapp_security_workflow',
    'run_comprehensive_recon'
]
```

## Step 3: Add Workflow to Main CLI

Update `main.py` to include the new workflow option:

```python
# main.py (add to argument parsing section)

parser.add_argument(
    '--workflow', '-w',
    choices=['standard', 'quick', 'deep', 'comprehensive', 'stealth', 'targeted', 'webapp-security'],
    default='standard',
    help='Choose reconnaissance workflow type'
)

# ... in the workflow execution section

elif args.workflow == 'webapp-security':
    from workflows import run_webapp_security_workflow
    results = run_webapp_security_workflow(
        target_domain=args.domain,
        use_ai_agents=not args.no_agent,
        ag2_config=ag2_config,
        verbose=args.verbose,
        output_format=args.output
    )
```

## Step 4: Add Docker Support

Update the Docker run scripts to support the new workflow:

```bash
# docker-run.sh (add to workflow options)
case "$WORKFLOW" in
    "standard"|"quick"|"deep"|"comprehensive"|"stealth"|"targeted"|"webapp-security")
        DOCKER_ARGS+=(-w "$WORKFLOW")
        ;;
    *)
        echo "❌ Invalid workflow: $WORKFLOW"
        echo "Valid options: standard, quick, deep, comprehensive, stealth, targeted, webapp-security"
        exit 1
        ;;
esac
```

```powershell
# docker-run.ps1 (add to workflow validation)
$ValidWorkflows = @("standard", "quick", "deep", "comprehensive", "stealth", "targeted", "webapp-security")
if ($Workflow -and $Workflow -notin $ValidWorkflows) {
    Write-Host "❌ Invalid workflow: $Workflow" -ForegroundColor Red
    Write-Host "Valid options: $($ValidWorkflows -join ', ')" -ForegroundColor Yellow
    exit 1
}
```

## Step 5: Create Unit Tests

Create comprehensive tests for the new workflow:

```python
# tests/test_webapp_security_workflow.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workflows.webapp_security_workflow import (
    run_webapp_security_workflow,
    execute_basic_tools,
    calculate_security_score,
    generate_recommendations
)

class TestWebAppSecurityWorkflow(unittest.TestCase):
    
    @patch('workflows.webapp_security_workflow.dns_lookup')
    @patch('workflows.webapp_security_workflow.get_http_headers')
    @patch('workflows.webapp_security_workflow.extract_security_headers')
    @patch('workflows.webapp_security_workflow.detect_technologies')
    @patch('workflows.webapp_security_workflow.check_ssl_vulnerabilities')
    @patch('workflows.webapp_security_workflow.scan_ports')
    @patch('workflows.webapp_security_workflow.capture_website_screenshot')
    def test_execute_basic_tools(self, mock_screenshot, mock_ports, mock_ssl, 
                                mock_tech, mock_sec_headers, mock_headers, mock_dns):
        # Setup mock data
        mock_dns.return_value = {"A": ["192.168.1.1"]}
        mock_headers.return_value = {"Server": "nginx/1.18.0"}
        mock_sec_headers.return_value = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff"
        }
        mock_tech.return_value = {"web_server": "nginx", "frameworks": ["React"]}
        mock_ssl.return_value = {
            "vulnerabilities": {"weak_ciphers": False},
            "certificate": {"days_until_expiry": 90}
        }
        mock_ports.return_value = {"open_ports": [80, 443]}
        mock_screenshot.return_value = "/app/reports/example.png"
        
        # Execute workflow
        findings = execute_basic_tools("example.com", verbose=True)
        
        # Verify results
        self.assertIn("dns_info", findings)
        self.assertIn("http_headers", findings)
        self.assertIn("security_headers", findings)
        self.assertIn("technologies", findings)
        self.assertIn("ssl_analysis", findings)
        self.assertIn("port_scan", findings)
        self.assertIn("screenshot", findings)
        
        # Verify mock calls
        mock_dns.assert_called_once_with("example.com")
        mock_headers.assert_called_once_with("https://example.com")
    
    def test_calculate_security_score(self):
        # Test with good security configuration
        good_findings = {
            "security_headers": {
                "Content-Security-Policy": "default-src 'self'",
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff",
                "Strict-Transport-Security": "max-age=31536000"
            },
            "ssl_analysis": {
                "vulnerabilities": {"weak_ciphers": False},
                "certificate": {"days_until_expiry": 90}
            },
            "port_scan": {"open_ports": [80, 443]}
        }
        
        score = calculate_security_score(good_findings)
        self.assertEqual(score, 100)
        
        # Test with poor security configuration
        poor_findings = {
            "security_headers": {},
            "ssl_analysis": {
                "vulnerabilities": {"weak_ciphers": True},
                "certificate": {"days_until_expiry": 15}
            },
            "port_scan": {"open_ports": [80, 443, 8080, 3000]}
        }
        
        score = calculate_security_score(poor_findings)
        self.assertLess(score, 50)
    
    def test_generate_recommendations(self):
        findings = {
            "security_headers": {},
            "ssl_analysis": {
                "vulnerabilities": {"weak_ciphers": True},
                "certificate": {"days_until_expiry": 15}
            },
            "port_scan": {"open_ports": [80, 443, 8080]}
        }
        
        recommendations = generate_recommendations(findings)
        
        # Check that recommendations are generated
        self.assertTrue(len(recommendations) > 0)
        
        # Check for specific recommendations
        csp_rec = any("Content-Security-Policy" in rec for rec in recommendations)
        self.assertTrue(csp_rec)
        
        hsts_rec = any("Strict Transport Security" in rec for rec in recommendations)
        self.assertTrue(hsts_rec)
    
    @patch('workflows.webapp_security_workflow.execute_basic_tools')
    @patch('workflows.webapp_security_workflow.calculate_security_score')
    @patch('workflows.webapp_security_workflow.generate_recommendations')
    def test_run_webapp_security_workflow_without_agents(self, mock_recommendations, 
                                                        mock_score, mock_tools):
        # Setup mocks
        mock_tools.return_value = {"test": "data"}
        mock_score.return_value = 75
        mock_recommendations.return_value = ["Test recommendation"]
        
        # Run workflow
        result = run_webapp_security_workflow(
            "example.com", 
            use_ai_agents=False
        )
        
        # Verify results
        self.assertEqual(result["target"], "example.com")
        self.assertEqual(result["workflow"], "webapp_security")
        self.assertEqual(result["security_score"], 75)
        self.assertIn("timestamp", result)
        self.assertIn("findings", result)
        self.assertIn("recommendations", result)

if __name__ == "__main__":
    unittest.main()
```

## Step 6: Add Integration with AI Agents

If using AI agents, ensure they have the necessary methods to support the workflow:

```python
# agents/webapp_recon_agent.py (add new methods)

class WebAppReconAgent:
    def analyze_webapp(self, target_domain: str, analysis_plan: Dict[str, Any]) -> None:
        """
        Analyze web application based on the provided plan.
        
        Args:
            target_domain: Target domain to analyze
            analysis_plan: Analysis plan with objectives and methodologies
        """
        self.logger.info(f"WebAppReconAgent starting analysis of {target_domain}")
        
        results = {}
        
        # Execute analysis based on plan objectives
        for objective in analysis_plan.get("objectives", []):
            if "security header" in objective.lower():
                results["security_headers"] = self._analyze_security_headers(target_domain)
            elif "ssl/tls" in objective.lower():
                results["ssl_analysis"] = self._analyze_ssl_configuration(target_domain)
            elif "technologies" in objective.lower():
                results["technologies"] = self._detect_technologies(target_domain)
        
        # Store results for reporter
        self.analysis_results = results
        
        # Send to reporter agent
        self.send_message({
            "type": "webapp_analysis_complete",
            "target": target_domain,
            "results": results
        })
    
    def get_security_assessment(self) -> Dict[str, Any]:
        """Return the security assessment results."""
        return getattr(self, 'analysis_results', {})
    
    def _analyze_security_headers(self, target_domain: str) -> Dict[str, Any]:
        """Analyze security headers with AI interpretation."""
        # Implementation for security header analysis
        pass
    
    def _analyze_ssl_configuration(self, target_domain: str) -> Dict[str, Any]:
        """Analyze SSL/TLS configuration with AI assessment."""
        # Implementation for SSL analysis
        pass
    
    def _detect_technologies(self, target_domain: str) -> Dict[str, Any]:
        """Detect technologies with AI-powered analysis."""
        # Implementation for technology detection
        pass
```

## Step 7: Create Example Usage

Create example usage scripts:

```python
# examples/webapp_security_example.py
#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from workflows.webapp_security_workflow import run_webapp_security_workflow

def main():
    target_domains = ["example.com", "github.com", "google.com"]
    
    for domain in target_domains:
        print(f"[+] Analyzing web application security for {domain}")
        
        results = run_webapp_security_workflow(
            target_domain=domain,
            use_ai_agents=False,
            verbose=True,
            output_format="json"
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            project_root, 
            'reports', 
            f"webapp_security_{domain}_{timestamp}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        
        # Display summary
        print(f"    Security Score: {results['security_score']}/100")
        print(f"    Recommendations: {len(results['recommendations'])}")
        print(f"    Report saved: {output_file}")
        print()

if __name__ == "__main__":
    main()
```

## Step 8: Update Documentation

Update the main documentation to include the new workflow:

```markdown
# README.md update

## 🎯 Available Workflows

| Workflow | Description | Use Case | Docker Example |
|----------|-------------|----------|----------------|
| **webapp-security** | Web application security assessment | Security-focused web app testing | `./docker-run.sh -d example.com -w webapp-security` |
```

## Common Workflow Types

Here are common types of reconnaissance workflows you can create:

### 1. Security-Focused Workflows
- **webapp-security**: Web application security assessment
- **network-security**: Network infrastructure security analysis
- **ssl-assessment**: SSL/TLS configuration and certificate analysis
- **vulnerability-scan**: Automated vulnerability detection

### 2. Intelligence Gathering Workflows
- **osint-deep**: Comprehensive open-source intelligence gathering
- **domain-intel**: Domain and DNS intelligence collection
- **social-recon**: Social media and people reconnaissance
- **competitive-intel**: Competitor analysis and intelligence

### 3. Infrastructure Analysis Workflows
- **cloud-recon**: Cloud infrastructure reconnaissance
- **cdn-analysis**: CDN and edge infrastructure analysis
- **api-discovery**: API endpoint discovery and analysis
- **mobile-app-recon**: Mobile application reconnaissance

### 4. Compliance and Audit Workflows
- **gdpr-assessment**: GDPR compliance assessment
- **pci-scan**: PCI DSS compliance scanning
- **security-audit**: Comprehensive security audit
- **privacy-assessment**: Privacy policy and implementation review

## Best Practices for Workflow Development

### 1. Modular Design
```python
def execute_phase_1(target):
    """Phase 1: Information gathering"""
    pass

def execute_phase_2(target, phase1_results):
    """Phase 2: Active reconnaissance"""  
    pass

def execute_phase_3(target, previous_results):
    """Phase 3: Analysis and reporting"""
    pass
```

### 2. Error Handling and Resilience
```python
def robust_workflow_step(target, retries=3):
    """Workflow step with error handling and retries."""
    for attempt in range(retries):
        try:
            return execute_step(target)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                return {"error": str(e), "step": "failed"}
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Progress Tracking
```python
def workflow_with_progress(target, progress_callback=None):
    """Workflow with progress tracking."""
    total_steps = 5
    
    for step, step_func in enumerate([step1, step2, step3, step4, step5]):
        if progress_callback:
            progress_callback(step + 1, total_steps, step_func.__name__)
        
        result = step_func(target)
        yield step + 1, result
```

### 4. Configuration Management
```python
class WorkflowConfig:
    def __init__(self, config_dict=None):
        self.timeout = config_dict.get('timeout', 30)
        self.retries = config_dict.get('retries', 3)
        self.delay = config_dict.get('delay', 1)
        self.parallel = config_dict.get('parallel', False)
```

### 5. Resource Management for Docker
```python
import resource

def resource_aware_workflow(target, max_memory_mb=512):
    """Workflow that monitors resource usage."""
    # Set memory limit
    resource.setrlimit(
        resource.RLIMIT_AS, 
        (max_memory_mb * 1024 * 1024, -1)
    )
    
    # Monitor resource usage
    start_time = time.time()
    
    try:
        result = execute_workflow(target)
        
        # Log resource usage
        usage = resource.getrusage(resource.RUSAGE_SELF)
        logger.info(f"Memory usage: {usage.ru_maxrss / 1024:.2f} MB")
        logger.info(f"Execution time: {time.time() - start_time:.2f} seconds")
        
        return result
    except MemoryError:
        return {"error": "workflow_memory_limit_exceeded"}
```

## Testing Workflows

### Unit Testing
```bash
# Test specific workflow
python -m pytest tests/test_webapp_security_workflow.py -v

# Test all workflows
python -m pytest tests/ -k "workflow" -v
```

### Docker Testing
```bash
# Test workflow in Docker
./docker-run.sh --build -d example.com -w webapp-security

# Test with different output formats
./docker-run.sh -d example.com -w webapp-security -o html
./docker-run.sh -d example.com -w webapp-security -o json
```

### Performance Testing
```bash
# Benchmark workflow performance
time ./docker-run.sh -d example.com -w webapp-security

# Memory usage monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" recon-ai-agent
```

Following these guidelines will help you create effective, maintainable workflows that integrate seamlessly with the Recon AI-Agent ecosystem and provide valuable reconnaissance capabilities for security professionals.