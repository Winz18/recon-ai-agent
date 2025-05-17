# workflows/targeted_recon_workflow.py
import logging
import autogen
from typing import Dict, List, Optional, Tuple, Union, Any

# Import specialized agents
from agents import (
    WebAppReconAgent, 
    NetworkReconAgent
)

# Import all tool functions
from tools import (
    get_http_headers,
    extract_security_headers,
    detect_technologies,
    scan_ports,
    crawl_endpoints,
    analyze_ssl_tls,
    detect_waf,
    check_cors_config,
    detect_cms
)

# Import configuration
from config.settings import get_ag2_config_list

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("targeted_recon_workflow")

def run_targeted_recon_workflow(
    target_domain: str, 
    model_id: str = "gemini-2.5-pro-preview-05-06",
    output_format: str = "markdown",
    save_report: bool = True,
    save_raw_data: bool = True,
    target_type: str = "web",
    tool_config: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Run a targeted reconnaissance workflow focused on specific security aspects.
    
    Args:
        target_domain: The domain to perform reconnaissance on
        model_id: The model ID to use for LLM
        output_format: Format for the output report ("markdown", "html", "json")
        save_report: Whether to save the report to a file
        save_raw_data: Whether to save raw data to a file
        target_type: Type of target to focus on ("web", "api", "ssl", "waf", "cms")
        tool_config: Configuration for enabled tools and their parameters
        
    Returns:
        Tuple containing:
        - The reconnaissance report as a string
        - The path to the saved report file (if saved)
    """
    logger.info(f"Starting targeted reconnaissance workflow ({target_type}) for {target_domain}")
    
    # Set default tool config if not provided
    if tool_config is None:
        tool_config = {
            "enable_dns": False,
            "enable_whois": False,
            "enable_headers": True,
            "enable_subdomains": False,
            "enable_ports": False,
            "enable_osint": False,
            "enable_tech": True,
            "enable_screenshot": False,
            "enable_crawler": True,
            "enable_ssl_analysis": True,
            "enable_waf_detection": True,
            "enable_cors_checks": True,
            "enable_cms_detection": True,
            
            # Default tool parameters
            "port_list": None,
            "port_timeout": 1.0,
            "port_threads": 10,
            "port_scan_type": "tcp",
            
            "use_subdomain_apis": False,
            "max_subdomains": 0,
            
            "http_timeout": 10.0,
            "user_agent": None,
            
            "dorks_limit": 0,
            
            # Crawler parameters
            "crawler_depth": 1,
            "crawler_output_format": "json",
            "crawler_wordlist": True,
            "crawler_wayback": True,
            "crawler_analyze_js": True,
            "crawler_max_js": 10,
            "crawler_timeout": 10,
            
            # SSL/TLS analysis parameters
            "ssl_check_cert_info": True,
            "ssl_check_protocols": True,
            "ssl_check_ciphers": True,
            "ssl_timeout": 10,
            
            # WAF detection parameters
            "waf_test_payloads": True,
            "waf_timeout": 10,
            
            # CORS check parameters
            "cors_timeout": 10,
            
            # CMS detection parameters
            "cms_deep_scan": True,
            "cms_timeout": 10,
            
            "workflow_type": "targeted"
        }
    
    # Customize configuration based on target type
    if target_type == "web":
        # Focus on web application security
        tool_config["enable_headers"] = True
        tool_config["enable_tech"] = True
        tool_config["enable_crawler"] = True
        tool_config["enable_ssl_analysis"] = True
        tool_config["enable_waf_detection"] = True
        tool_config["enable_cors_checks"] = True
        tool_config["enable_cms_detection"] = True
        tool_config["enable_ports"] = True
        tool_config["port_list"] = [80, 443, 8080, 8443]
    elif target_type == "api":
        # Focus on API security
        tool_config["enable_headers"] = True
        tool_config["enable_tech"] = True
        tool_config["enable_crawler"] = True
        tool_config["crawler_wordlist"] = True
        tool_config["crawler_analyze_js"] = True
        tool_config["enable_cors_checks"] = True
        tool_config["enable_ports"] = True
        tool_config["port_list"] = [80, 443, 8080, 8443, 3000, 5000, 8000]
    elif target_type == "ssl":
        # Focus on SSL/TLS security
        tool_config["enable_headers"] = True
        tool_config["enable_ssl_analysis"] = True
        tool_config["ssl_check_cert_info"] = True
        tool_config["ssl_check_protocols"] = True
        tool_config["ssl_check_ciphers"] = True
        tool_config["ssl_timeout"] = 15
    elif target_type == "waf":
        # Focus on WAF detection and bypass
        tool_config["enable_headers"] = True
        tool_config["enable_waf_detection"] = True
        tool_config["waf_test_payloads"] = True
        tool_config["waf_timeout"] = 15
    elif target_type == "cms":
        # Focus on CMS detection and security
        tool_config["enable_tech"] = True
        tool_config["enable_cms_detection"] = True
        tool_config["cms_deep_scan"] = True
        tool_config["enable_crawler"] = True
    
    # Initialize configuration
    config_list = get_ag2_config_list(model_id=model_id)
    llm_config = {
        "config_list": config_list,
        "cache_seed": 42,
        "temperature": 0.7,
    }
    
    # Initialize UserProxyAgent for tool execution
    tool_executor = autogen.UserProxyAgent(
        name="Tool_Executor_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1000,
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
        code_execution_config={"use_docker": False},  # Disable Docker usage
        llm_config=False
    )
    
    # Register only the enabled tools with the UserProxyAgent
    function_map = {}
        
    if tool_config.get("enable_headers", True):
        function_map["get_http_headers"] = get_http_headers
        function_map["extract_security_headers"] = extract_security_headers
    
    if tool_config.get("enable_ports", False):
        function_map["scan_ports"] = lambda target, ports=None: scan_ports(
            target=target,
            ports=ports if ports is not None else tool_config.get("port_list"),
            timeout=tool_config.get("port_timeout", 1.0),
            threads=tool_config.get("port_threads", 10),
            scan_type=tool_config.get("port_scan_type", "tcp")
        )
        
    if tool_config.get("enable_tech", True):
        function_map["detect_technologies"] = detect_technologies
    
    # Add endpoint crawler to available functions
    if tool_config.get("enable_crawler", True):
        function_map["crawl_endpoints"] = lambda url: crawl_endpoints(
            url=url,
            depth=tool_config.get("crawler_depth", 1),
            output_format=tool_config.get("crawler_output_format", "json"),
            use_wordlist=tool_config.get("crawler_wordlist", True),
            use_wayback=tool_config.get("crawler_wayback", True),
            analyze_js=tool_config.get("crawler_analyze_js", True),
            max_js_files=tool_config.get("crawler_max_js", 10),
            timeout=tool_config.get("crawler_timeout", 10)
        )
    
    # Add SSL/TLS analyzer to available functions
    if tool_config.get("enable_ssl_analysis", True):
        function_map["analyze_ssl_tls"] = lambda url: analyze_ssl_tls(
            url=url,
            timeout=tool_config.get("ssl_timeout", 10),
            check_cert_info=tool_config.get("ssl_check_cert_info", True),
            check_protocols=tool_config.get("ssl_check_protocols", True),
            check_ciphers=tool_config.get("ssl_check_ciphers", True)
        )
    
    # Add WAF detector to available functions
    if tool_config.get("enable_waf_detection", True):
        function_map["detect_waf"] = lambda url: detect_waf(
            url=url,
            timeout=tool_config.get("waf_timeout", 10),
            user_agent=tool_config.get("user_agent"),
            test_payloads=tool_config.get("waf_test_payloads", True)
        )
    
    # Add CORS checker to available functions
    if tool_config.get("enable_cors_checks", True):
        function_map["check_cors_config"] = lambda url: check_cors_config(
            url=url,
            timeout=tool_config.get("cors_timeout", 10)
        )
    
    # Add CMS detector to available functions
    if tool_config.get("enable_cms_detection", True):
        function_map["detect_cms"] = lambda url: detect_cms(
            url=url,
            deep_scan=tool_config.get("cms_deep_scan", False),
            timeout=tool_config.get("cms_timeout", 10)
        )
    
    # Register the functions
    tool_executor.register_function(function_map=function_map)
    logger.info(f"Registered functions: {list(tool_executor.function_map.keys())}")
    
    # Choose appropriate agent based on target type
    if target_type in ["web", "api", "cms", "cors"]:
        agent = WebAppReconAgent(llm_config=llm_config)
    else:  # ssl, waf
        agent = NetworkReconAgent(llm_config=llm_config)
    
    # Dictionary to store collected data
    collected_data = {
        "target_domain": target_domain,
        "target_type": target_type,
        "summaries": {},
        "findings": []
    }
    
    # Prepare prompt based on target type
    if target_type == "web":
        prompt = f"Perform comprehensive web application security reconnaissance on {target_domain}. Focus on HTTP headers, security headers, technologies, endpoints discovery, SSL/TLS analysis, WAF detection, CORS configuration, and CMS detection."
    elif target_type == "api":
        prompt = f"Perform API security reconnaissance on {target_domain}. Focus on discovering API endpoints, analyzing CORS configuration, and examining HTTP security headers."
    elif target_type == "ssl":
        prompt = f"Perform detailed SSL/TLS security analysis on {target_domain}. Focus on certificate validation, supported protocols and ciphers."
    elif target_type == "waf":
        prompt = f"Detect and analyze web application firewalls (WAFs) protecting {target_domain}. Focus on WAF identification and characterization."
    elif target_type == "cms":
        prompt = f"Identify and analyze content management systems (CMS) used by {target_domain}. Focus on CMS detection, version information, and potential security issues."
    else:
        prompt = f"Perform targeted security reconnaissance on {target_domain} focusing on {target_type}."
    
    # Execute reconnaissance
    logger.info(f"Starting targeted reconnaissance for {target_domain} focusing on {target_type}")
    chat = tool_executor.initiate_chat(agent, message=prompt)
    
    # Get the summary from the chat
    try:
        collected_data["summaries"]["targeted_recon"] = agent.last_message(tool_executor)["content"]
    except (ValueError, KeyError, AttributeError, TypeError):
        if hasattr(chat, 'messages') and chat.messages:
            collected_data["summaries"]["targeted_recon"] = chat.messages[-1]["content"]
        elif hasattr(chat, 'get_last_message'):
            collected_data["summaries"]["targeted_recon"] = chat.get_last_message()["content"]
        elif hasattr(chat, 'chat_history') and chat.chat_history:
            collected_data["summaries"]["targeted_recon"] = chat.chat_history[-1]["content"]
        else:
            collected_data["summaries"]["targeted_recon"] = "Failed to retrieve chat summary"
    
    # Generate the report
    logger.info("Generating targeted reconnaissance report")
    
    # Initialize the reporter
    from agents import ReconReporter
    reporter = ReconReporter(llm_config=llm_config)
    
    # Generate the report
    report, report_path = reporter.generate_report(
        target_domain=target_domain, 
        collected_data=collected_data,
        output_format=output_format,
        save_report=save_report,
        save_raw_data=save_raw_data,
        report_type=f"targeted_{target_type}"
    )
    
    # Print report location
    if report_path:
        logger.info(f"Report saved to: {report_path}")
    
    logger.info(f"Targeted reconnaissance workflow for {target_type} completed successfully")
    
    return report, report_path 