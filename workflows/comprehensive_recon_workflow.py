# workflows/comprehensive_recon_workflow.py
import logging
import autogen
import time
from typing import Dict, List, Optional, Tuple, Union, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all specialized agents
from agents import (
    DomainIntelAgent,
    WebAppReconAgent,
    NetworkReconAgent,
    OSINTGatheringAgent,
    ReconReporter
)

# Import all tool functions
from tools import (
    dns_lookup,
    whois_lookup,
    get_http_headers,
    extract_security_headers,
    search_subdomains,
    scan_ports,
    search_google_dorks,
    detect_technologies,
    capture_website_screenshot,
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
logger = logging.getLogger("comprehensive_recon_workflow")

def run_comprehensive_recon_workflow(
    target_domain: str, 
    model_id: str = "gemini-2.5-pro-preview-05-06",
    output_format: str = "markdown",
    save_report: bool = True,
    save_raw_data: bool = True,
    parallelism: int = 2,
    tool_config: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Run a comprehensive reconnaissance workflow using all available tools.
    
    Args:
        target_domain: The domain to perform reconnaissance on
        model_id: The model ID to use for LLM
        output_format: Format for the output report ("markdown", "html", "json")
        save_report: Whether to save the report to a file
        save_raw_data: Whether to save raw data to a file
        parallelism: How many reconnaissance operations to run in parallel (1=sequential)
        tool_config: Configuration for enabled tools and their parameters
        
    Returns:
        Tuple containing:
        - The reconnaissance report as a string
        - The path to the saved report file (if saved)
    """
    logger.info(f"Starting comprehensive reconnaissance workflow for {target_domain}")
    
    # Set default tool config if not provided - enable everything
    if tool_config is None:
        tool_config = {
            "enable_dns": True,
            "enable_whois": True,
            "enable_headers": True,
            "enable_subdomains": True,
            "enable_ports": True,
            "enable_osint": True,
            "enable_tech": True,
            "enable_screenshot": True,
            "enable_crawler": True,
            "enable_ssl_analysis": True,
            "enable_waf_detection": True,
            "enable_cors_checks": True,
            "enable_cms_detection": True,
            
            # Default tool parameters - enhanced for comprehensive scan
            "port_list": None,  # Scan common ports
            "port_timeout": 2.0,
            "port_threads": 20,
            "port_scan_type": "tcp",
            
            "use_subdomain_apis": True,
            "max_subdomains": 200,
            
            "http_timeout": 15.0,
            "user_agent": None,
            
            "dorks_limit": 30,
            
            # Crawler parameters
            "crawler_depth": 2,
            "crawler_output_format": "json",
            "crawler_wordlist": True,
            "crawler_wayback": True,
            "crawler_analyze_js": True,
            "crawler_max_js": 20,
            "crawler_timeout": 15,
            
            # SSL/TLS analysis parameters
            "ssl_check_cert_info": True,
            "ssl_check_protocols": True,
            "ssl_check_ciphers": True,
            "ssl_timeout": 15,
            
            # WAF detection parameters
            "waf_test_payloads": True,
            "waf_timeout": 15,
            
            # CORS check parameters
            "cors_timeout": 15,
            
            # CMS detection parameters
            "cms_deep_scan": True,
            "cms_timeout": 15,
            
            "workflow_type": "comprehensive"
        }
    
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
      
    # Register all tools with the UserProxyAgent
    function_map = {}
    if tool_config.get("enable_dns", True):
        function_map["dns_lookup"] = dns_lookup
        
    if tool_config.get("enable_whois", True):
        function_map["whois_lookup"] = whois_lookup
        
    if tool_config.get("enable_headers", True):
        function_map["get_http_headers"] = get_http_headers
        function_map["extract_security_headers"] = extract_security_headers
        
    if tool_config.get("enable_subdomains", True):
        function_map["search_subdomains"] = lambda domain: search_subdomains(
            domain=domain, 
            use_apis=tool_config.get("use_subdomain_apis", True),
            max_results=tool_config.get("max_subdomains", 200)
        )
        
    if tool_config.get("enable_ports", True):
        function_map["scan_ports"] = lambda target, ports=None: scan_ports(
            target=target,
            ports=ports if ports is not None else tool_config.get("port_list"),
            timeout=tool_config.get("port_timeout", 2.0),
            threads=tool_config.get("port_threads", 20),
            scan_type=tool_config.get("port_scan_type", "tcp")
        )
        
    if tool_config.get("enable_osint", True):
        function_map["search_google_dorks"] = lambda domain: search_google_dorks(
            domain=domain,
            max_results=tool_config.get("dorks_limit", 30)
        )
        
    if tool_config.get("enable_tech", True):
        function_map["detect_technologies"] = detect_technologies
        
    if tool_config.get("enable_screenshot", True):
        function_map["capture_website_screenshot"] = capture_website_screenshot
        
    if tool_config.get("enable_crawler", True):
        function_map["crawl_endpoints"] = lambda url: crawl_endpoints(
            url=url,
            depth=tool_config.get("crawler_depth", 2),
            output_format=tool_config.get("crawler_output_format", "json"),
            use_wordlist=tool_config.get("crawler_wordlist", True),
            use_wayback=tool_config.get("crawler_wayback", True),
            analyze_js=tool_config.get("crawler_analyze_js", True),
            max_js_files=tool_config.get("crawler_max_js", 20),
            timeout=tool_config.get("crawler_timeout", 15)
        )
    
    if tool_config.get("enable_ssl_analysis", True):
        function_map["analyze_ssl_tls"] = lambda url: analyze_ssl_tls(
            url=url,
            timeout=tool_config.get("ssl_timeout", 15),
            check_cert_info=tool_config.get("ssl_check_cert_info", True),
            check_protocols=tool_config.get("ssl_check_protocols", True),
            check_ciphers=tool_config.get("ssl_check_ciphers", True)
        )
    
    if tool_config.get("enable_waf_detection", True):
        function_map["detect_waf"] = lambda url: detect_waf(
            url=url,
            timeout=tool_config.get("waf_timeout", 15),
            user_agent=tool_config.get("user_agent"),
            test_payloads=tool_config.get("waf_test_payloads", True)
        )
    
    if tool_config.get("enable_cors_checks", True):
        function_map["check_cors_config"] = lambda url: check_cors_config(
            url=url,
            timeout=tool_config.get("cors_timeout", 15)
        )
    
    if tool_config.get("enable_cms_detection", True):
        function_map["detect_cms"] = lambda url: detect_cms(
            url=url,
            deep_scan=tool_config.get("cms_deep_scan", True),
            timeout=tool_config.get("cms_timeout", 15)
        )
    
    # Register the functions
    tool_executor.register_function(function_map=function_map)
    logger.info(f"Registered functions: {list(tool_executor.function_map.keys())}")
    
    # Initialize specialized agents
    domain_intel_agent = DomainIntelAgent(llm_config=llm_config)
    webapp_recon_agent = WebAppReconAgent(llm_config=llm_config)
    network_recon_agent = NetworkReconAgent(llm_config=llm_config)
    osint_gathering_agent = OSINTGatheringAgent(llm_config=llm_config)
    
    # Dictionary to store collected data summaries
    collected_data = {
        "target_domain": target_domain,
        "summaries": {},
        "findings": []
    }
    
    # Define all reconnaissance tasks
    recon_tasks = []
    
    # Task 1: Domain Intelligence (DNS & WHOIS)
    if tool_config.get("enable_dns", True) or tool_config.get("enable_whois", True):
        domain_tools = []
        if tool_config.get("enable_dns", True):
            domain_tools.append("DNS records")
        if tool_config.get("enable_whois", True):
            domain_tools.append("WHOIS information")
            
        domain_intel_prompt = f"Collect {' and '.join(domain_tools)} for the domain: {target_domain}"
        
        recon_tasks.append({
            "name": "domain_intel",
            "agent": domain_intel_agent,
            "prompt": domain_intel_prompt,
            "description": "Domain Intelligence Collection"
        })
    
    # Task 2: Web Application Reconnaissance
    web_tools_enabled = any([
        tool_config.get("enable_headers", True),
        tool_config.get("enable_subdomains", True),
        tool_config.get("enable_tech", True),
        tool_config.get("enable_screenshot", True),
        tool_config.get("enable_crawler", True),
        tool_config.get("enable_ssl_analysis", True),
        tool_config.get("enable_waf_detection", True),
        tool_config.get("enable_cors_checks", True),
        tool_config.get("enable_cms_detection", True)
    ])
    
    if web_tools_enabled:
        web_tools = []
        if tool_config.get("enable_headers", True):
            web_tools.append("HTTP headers and security headers")
        if tool_config.get("enable_tech", True):
            web_tools.append("technologies")
        if tool_config.get("enable_subdomains", True):
            web_tools.append("subdomains")
        if tool_config.get("enable_screenshot", True):
            web_tools.append("screenshot of the website")
        if tool_config.get("enable_crawler", True):
            web_tools.append("website endpoints")
        if tool_config.get("enable_ssl_analysis", True):
            web_tools.append("SSL/TLS security configuration")
        if tool_config.get("enable_waf_detection", True):
            web_tools.append("web application firewall (WAF) details")
        if tool_config.get("enable_cors_checks", True):
            web_tools.append("CORS configuration security")
        if tool_config.get("enable_cms_detection", True):
            web_tools.append("content management system (CMS) information")
            
        webapp_recon_prompt = f"Gather {', '.join(web_tools)} for the website: {target_domain}"
        
        recon_tasks.append({
            "name": "webapp_recon",
            "agent": webapp_recon_agent,
            "prompt": webapp_recon_prompt,
            "description": "Web Application Reconnaissance"
        })
    
    # Task 3: Network Reconnaissance (Port Scanning)
    if tool_config.get("enable_ports", True):
        port_info = ""
        if tool_config.get("port_list"):
            port_info = f" on specific ports: {tool_config.get('port_list')}"
        scan_type_info = f" using {tool_config.get('port_scan_type', 'TCP').upper()} scanning"
        
        network_recon_prompt = f"Scan for open ports{port_info} on the domain: {target_domain}{scan_type_info}"
        
        recon_tasks.append({
            "name": "network_recon",
            "agent": network_recon_agent,
            "prompt": network_recon_prompt,
            "description": "Network Reconnaissance"
        })
    
    # Task 4: OSINT Gathering (Google Dorking)
    if tool_config.get("enable_osint", True):
        osint_prompt = f"Perform Google dorking on the domain: {target_domain} with a limit of {tool_config.get('dorks_limit', 30)} results"
        
        recon_tasks.append({
            "name": "osint_gathering",
            "agent": osint_gathering_agent,
            "prompt": osint_prompt,
            "description": "OSINT Gathering"
        })
    
    # Execute tasks based on parallelism setting
    if parallelism <= 1:
        # Sequential execution
        logger.info("Executing reconnaissance tasks sequentially")
        for task in recon_tasks:
            logger.info(f"Starting task: {task['description']}")
            
            chat = tool_executor.initiate_chat(
                task["agent"],
                message=task["prompt"]
            )
            
            try:
                collected_data["summaries"][task["name"]] = task["agent"].last_message(tool_executor)["content"]
            except (ValueError, KeyError, AttributeError, TypeError):
                if hasattr(chat, 'messages') and chat.messages:
                    collected_data["summaries"][task["name"]] = chat.messages[-1]["content"]
                elif hasattr(chat, 'get_last_message'):
                    collected_data["summaries"][task["name"]] = chat.get_last_message()["content"]
                elif hasattr(chat, 'chat_history') and chat.chat_history:
                    collected_data["summaries"][task["name"]] = chat.chat_history[-1]["content"]
                else:
                    collected_data["summaries"][task["name"]] = f"Failed to retrieve {task['description']} summary"
                    
            logger.info(f"Completed task: {task['description']}")
    else:
        # Parallel execution using ThreadPoolExecutor
        logger.info(f"Executing reconnaissance tasks in parallel (max workers: {parallelism})")
        
        def execute_task(task):
            logger.info(f"Starting task: {task['description']}")
            
            # Create new tool executor for each thread
            thread_tool_executor = autogen.UserProxyAgent(
                name=f"Tool_Executor_Proxy_{task['name']}",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1000,
                is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
                code_execution_config={"use_docker": False},
                llm_config=False
            )
            
            # Register the functions
            thread_tool_executor.register_function(function_map=function_map)
            
            chat = thread_tool_executor.initiate_chat(
                task["agent"],
                message=task["prompt"]
            )
            
            try:
                result = task["agent"].last_message(thread_tool_executor)["content"]
            except (ValueError, KeyError, AttributeError, TypeError):
                if hasattr(chat, 'messages') and chat.messages:
                    result = chat.messages[-1]["content"]
                elif hasattr(chat, 'get_last_message'):
                    result = chat.get_last_message()["content"]
                elif hasattr(chat, 'chat_history') and chat.chat_history:
                    result = chat.chat_history[-1]["content"]
                else:
                    result = f"Failed to retrieve {task['description']} summary"
            
            logger.info(f"Completed task: {task['description']}")
            return task["name"], result
        
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            future_to_task = {executor.submit(execute_task, task): task for task in recon_tasks}
            for future in as_completed(future_to_task):
                task_name, result = future.result()
                collected_data["summaries"][task_name] = result
    
    # Generate the final report
    logger.info("Generating comprehensive reconnaissance report")
    
    # Initialize the report generator
    reporter = ReconReporter(llm_config=llm_config)
    
    # Generate the report
    report, report_path = reporter.generate_report(
        target_domain=target_domain, 
        collected_data=collected_data,
        output_format=output_format,
        save_report=save_report,
        save_raw_data=save_raw_data,
        report_type="comprehensive"
    )
    
    # Print report location
    if report_path:
        logger.info(f"Report saved to: {report_path}")
    
    logger.info("Comprehensive reconnaissance workflow completed successfully")
    
    return report, report_path 