# workflows/stealth_recon_workflow.py
import logging
import autogen
import time
import random
from typing import Dict, List, Optional, Tuple, Union, Any

# Import specialized agents
from agents import (
    DomainIntelAgent,
    OSINTGatheringAgent,
    ReconReporter
)

# Import passive reconnaissance tools
from tools import (
    whois_lookup,
    search_google_dorks,
    search_subdomains
)

# Import configuration
from config.settings import get_ag2_config_list

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stealth_recon_workflow")

def run_stealth_recon_workflow(
    target_domain: str, 
    model_id: str = "gemini-2.5-pro-preview-05-06",
    output_format: str = "markdown",
    save_report: bool = True,
    save_raw_data: bool = True,
    delay_between_requests: float = 2.0,
    jitter: float = 0.5,
    tool_config: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Run a stealth reconnaissance workflow that minimizes detection.
    
    Args:
        target_domain: The domain to perform reconnaissance on
        model_id: The model ID to use for LLM
        output_format: Format for the output report ("markdown", "html", "json")
        save_report: Whether to save the report to a file
        save_raw_data: Whether to save raw data to a file
        delay_between_requests: Base delay between requests (seconds)
        jitter: Random jitter to add to delays (seconds)
        tool_config: Configuration for enabled tools and their parameters
        
    Returns:
        Tuple containing:
        - The reconnaissance report as a string
        - The path to the saved report file (if saved)
    """
    logger.info(f"Starting stealth reconnaissance workflow for {target_domain}")
    
    # Set default tool config if not provided
    if tool_config is None:
        tool_config = {
            "enable_dns": False,  # DNS queries can be logged
            "enable_whois": True,
            "enable_headers": False,  # Direct HTTP requests can be logged
            "enable_subdomains": True, 
            "enable_ports": False,  # Port scans are highly detectable
            "enable_osint": True,
            "enable_tech": False,  # Requires active probing
            "enable_screenshot": False,  # Requires active probing
            "enable_crawler": False,  # Crawling is highly detectable
            "enable_ssl_analysis": False,  # Requires active probing
            "enable_waf_detection": False,  # WAF detection can trigger alerts
            "enable_cors_checks": False,  # Requires active probing
            "enable_cms_detection": False,  # Requires active probing
            
            # Subdomain parameters
            "use_subdomain_apis": True,  # Use passive techniques only
            "max_subdomains": 50,
            
            # OSINT parameters
            "dorks_limit": 20,
            
            # Proxy settings
            "use_proxy": True,
            "proxy_rotation": True,
            "rotate_user_agents": True,
            
            "workflow_type": "stealth"
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
    
    # Create a wrapper for tools to add delay and jitter
    def stealth_wrapper(func):
        def wrapper(*args, **kwargs):
            # Add random delay with jitter
            delay = delay_between_requests + random.uniform(-jitter, jitter)
            if delay > 0:
                logger.info(f"Applying stealth delay of {delay:.2f} seconds")
                time.sleep(delay)
            
            return func(*args, **kwargs)
        return wrapper
    
    # Register only the enabled tools with the UserProxyAgent
    function_map = {}
    
    if tool_config.get("enable_whois", True):
        function_map["whois_lookup"] = stealth_wrapper(whois_lookup)
        
    if tool_config.get("enable_subdomains", True):
        # Use passive subdomain enumeration only
        function_map["search_subdomains"] = stealth_wrapper(
            lambda domain: search_subdomains(
                domain=domain, 
                use_apis=True,  # Force using APIs for passive recon
                max_results=tool_config.get("max_subdomains", 50)
            )
        )
        
    if tool_config.get("enable_osint", True):
        function_map["search_google_dorks"] = lambda domain: search_google_dorks(
            domain=domain,
            max_results=tool_config.get("dorks_limit", 5),
            respect_rate_limits=True
        )
    
    # Register the functions
    tool_executor.register_function(function_map=function_map)
    logger.info(f"Registered functions: {list(tool_executor.function_map.keys())}")
    
    # Initialize specialized agents for passive reconnaissance
    domain_intel_agent = DomainIntelAgent(llm_config=llm_config)
    osint_gathering_agent = OSINTGatheringAgent(llm_config=llm_config)
    
    # Dictionary to store collected data summaries
    collected_data = {
        "target_domain": target_domain,
        "summaries": {},
        "findings": []
    }
    
    # Step 1: WHOIS Information (completely passive)
    if tool_config.get("enable_whois", True):
        logger.info("Step 1: Collecting WHOIS information")
        
        # Delay for stealth
        time.sleep(delay_between_requests + random.uniform(-jitter, jitter))
        
        whois_prompt = f"Perform a WHOIS lookup for the domain: {target_domain}. Extract all useful information but DO NOT perform any other lookups or active reconnaissance."
        whois_chat = tool_executor.initiate_chat(
            domain_intel_agent,
            message=whois_prompt
        )
        
        try:
            collected_data["summaries"]["whois_intel"] = domain_intel_agent.last_message(tool_executor)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            if hasattr(whois_chat, 'messages') and whois_chat.messages:
                collected_data["summaries"]["whois_intel"] = whois_chat.messages[-1]["content"]
            elif hasattr(whois_chat, 'get_last_message'):
                collected_data["summaries"]["whois_intel"] = whois_chat.get_last_message()["content"]
            elif hasattr(whois_chat, 'chat_history') and whois_chat.chat_history:
                collected_data["summaries"]["whois_intel"] = whois_chat.chat_history[-1]["content"]
            else:
                collected_data["summaries"]["whois_intel"] = "Failed to retrieve WHOIS information"
                
        logger.info("WHOIS information collection completed")
    
    # Step 2: Subdomain enumeration (passive methods only)
    if tool_config.get("enable_subdomains", True):
        logger.info("Step 2: Performing passive subdomain enumeration")
        
        # Delay for stealth
        time.sleep(delay_between_requests + random.uniform(-jitter, jitter))
        
        subdomain_prompt = f"Find subdomains for {target_domain} using ONLY PASSIVE techniques. Do not perform any active scans or direct connections to the target."
        domain_intel_chat = tool_executor.initiate_chat(
            domain_intel_agent,
            message=subdomain_prompt
        )
        
        try:
            collected_data["summaries"]["subdomain_enum"] = domain_intel_agent.last_message(tool_executor)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            if hasattr(domain_intel_chat, 'messages') and domain_intel_chat.messages:
                collected_data["summaries"]["subdomain_enum"] = domain_intel_chat.messages[-1]["content"]
            elif hasattr(domain_intel_chat, 'get_last_message'):
                collected_data["summaries"]["subdomain_enum"] = domain_intel_chat.get_last_message()["content"]
            elif hasattr(domain_intel_chat, 'chat_history') and domain_intel_chat.chat_history:
                collected_data["summaries"]["subdomain_enum"] = domain_intel_chat.chat_history[-1]["content"]
            else:
                collected_data["summaries"]["subdomain_enum"] = "Failed to retrieve subdomain information"
                
        logger.info("Passive subdomain enumeration completed")
    
    # Step 3: OSINT Gathering (Google Dorking)
    if tool_config.get("enable_osint", True):
        logger.info("Step 3: Gathering OSINT information using Google Dorking")
        
        # Delay for stealth
        time.sleep(delay_between_requests + random.uniform(-jitter, jitter))
        
        osint_prompt = f"Perform Google dorking on the domain: {target_domain} with a limit of {tool_config.get('dorks_limit', 20)} results. Use diverse dork queries to find exposed information."
        osint_chat = tool_executor.initiate_chat(
            osint_gathering_agent,
            message=osint_prompt
        )
        
        try:
            collected_data["summaries"]["osint_gathering"] = osint_gathering_agent.last_message(tool_executor)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            if hasattr(osint_chat, 'messages') and osint_chat.messages:
                collected_data["summaries"]["osint_gathering"] = osint_chat.messages[-1]["content"]
            elif hasattr(osint_chat, 'get_last_message'):
                collected_data["summaries"]["osint_gathering"] = osint_chat.get_last_message()["content"]
            elif hasattr(osint_chat, 'chat_history') and osint_chat.chat_history:
                collected_data["summaries"]["osint_gathering"] = osint_chat.chat_history[-1]["content"]
            else:
                collected_data["summaries"]["osint_gathering"] = "Failed to retrieve OSINT information"
                
        logger.info("OSINT gathering completed")
    
    # Generate the final report
    logger.info("Generating stealth reconnaissance report")
    
    # Initialize the report generator
    reporter = ReconReporter(llm_config=llm_config)
    
    # Generate the report
    report, report_path = reporter.generate_report(
        target_domain=target_domain, 
        collected_data=collected_data,
        output_format=output_format,
        save_report=save_report,
        save_raw_data=save_raw_data,
        report_type="stealth"
    )
    
    # Print report location
    if report_path:
        logger.info(f"Report saved to: {report_path}")
    
    logger.info("Stealth reconnaissance workflow completed successfully")
    
    return report, report_path 