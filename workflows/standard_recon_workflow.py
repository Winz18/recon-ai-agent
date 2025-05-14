#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import autogen
from typing import Dict, List, Any, Optional

# Import specialized agents
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
    capture_website_screenshot
)

# Import configuration
from config.settings import get_ag2_config_list
from config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("standard_recon_workflow")

def run_standard_recon_workflow(target_domain: str, model_id: str = "gemini-2.5-pro-preview-05-06") -> Dict:
    """
    Run a standard reconnaissance workflow using specialized agents in sequence.
    
    Args:
        target_domain: The domain to perform reconnaissance on
        model_id: The model ID to use for LLM
        
    Returns:
        Dictionary containing the reconnaissance report
    """
    logger.info(f"Starting standard reconnaissance workflow for {target_domain}")
    
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
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: isinstance(x, dict) and "TERMINATE" in x.get("content", "").upper(),
        code_execution_config=False,
        llm_config=False
    )
    
    # Register all tools with the UserProxyAgent
    tool_executor.register_function(
        function_map={
            "dns_lookup": dns_lookup,
            "whois_lookup": whois_lookup,
            "get_http_headers": get_http_headers,
            "extract_security_headers": extract_security_headers,
            "search_subdomains": search_subdomains,
            "scan_ports": scan_ports,
            "search_google_dorks": search_google_dorks,
            "detect_technologies": detect_technologies,
            "capture_website_screenshot": capture_website_screenshot,
        }
    )
    logger.info(f"Registered functions: {list(tool_executor.function_map.keys())}")
    
    # Initialize specialized agents
    domain_intel_agent = DomainIntelAgent(llm_config=llm_config)
    webapp_recon_agent = WebAppReconAgent(llm_config=llm_config)
    network_recon_agent = NetworkReconAgent(llm_config=llm_config)
    osint_gathering_agent = OSINTGatheringAgent(llm_config=llm_config)
    
    # Initialize the report generator
    reporter = ReconReporter(llm_config=llm_config)
    
    # Dictionary to store collected data summaries
    collected_data = {
        "target_domain": target_domain,
        "summaries": {},
        "findings": []
    }
    
    # Step 1: Domain Intelligence (DNS & WHOIS)
    logger.info("Step 1: Collecting domain intelligence (DNS & WHOIS)")
    domain_intel_prompt = f"Collect DNS records and WHOIS information for the domain: {target_domain}"
    domain_intel_chat = tool_executor.initiate_chat(
        domain_intel_agent,
        message=domain_intel_prompt
    )
    # Option 1: If messages are stored as a list property
    if hasattr(domain_intel_chat, 'messages') and domain_intel_chat.messages:
        collected_data["summaries"]["domain_intel"] = domain_intel_chat.messages[-1]["content"]
    # Option 2: If there's a get_last_message method instead
    elif hasattr(domain_intel_chat, 'get_last_message'):
        collected_data["summaries"]["domain_intel"] = domain_intel_chat.get_last_message()["content"]
    # Option 3: For direct access to chat history
    elif hasattr(domain_intel_chat, 'chat_history') and domain_intel_chat.chat_history:
        collected_data["summaries"]["domain_intel"] = domain_intel_chat.chat_history[-1]["content"]
    else:
        collected_data["summaries"]["domain_intel"] = "Failed to retrieve chat summary"
    logger.info("Domain intelligence collection completed")
    
    # Step 2: Web Application Reconnaissance
    logger.info("Step 2: Performing web application reconnaissance")
    webapp_recon_prompt = f"Gather HTTP headers, security headers, technologies, subdomains, and take a screenshot of the website: {target_domain}"
    webapp_recon_chat = tool_executor.initiate_chat(
        webapp_recon_agent,
        message=webapp_recon_prompt
    )
    if hasattr(webapp_recon_chat, 'messages') and webapp_recon_chat.messages:
        collected_data["summaries"]["webapp_recon"] = webapp_recon_chat.messages[-1]["content"]
    elif hasattr(webapp_recon_chat, 'get_last_message'):
        collected_data["summaries"]["webapp_recon"] = webapp_recon_chat.get_last_message()["content"]
    elif hasattr(webapp_recon_chat, 'chat_history') and webapp_recon_chat.chat_history:
        collected_data["summaries"]["webapp_recon"] = webapp_recon_chat.chat_history[-1]["content"]
    else:
        collected_data["summaries"]["webapp_recon"] = "Failed to retrieve web application reconnaissance summary"
    logger.info("Web application reconnaissance completed")
    
    # Step 3: Network Reconnaissance (Port Scanning)
    logger.info("Step 3: Performing network reconnaissance (port scanning)")
    network_recon_prompt = f"Scan for open ports on the domain: {target_domain}"
    network_recon_chat = tool_executor.initiate_chat(
        network_recon_agent,
        message=network_recon_prompt
    )
    collected_data["summaries"]["network_recon"] = network_recon_chat.last_message()["content"]
    logger.info("Network reconnaissance completed")
    
    # Step 4: OSINT Gathering (Google Dorking)
    logger.info("Step 4: Gathering OSINT information using Google Dorking")
    osint_prompt = f"Perform Google dorking on the domain: {target_domain}"
    osint_chat = tool_executor.initiate_chat(
        osint_gathering_agent,
        message=osint_prompt
    )
    collected_data["summaries"]["osint_gathering"] = osint_chat.last_message()["content"]
    logger.info("OSINT gathering completed")
    
    # Generate the final report
    logger.info("Generating final reconnaissance report")
    report = reporter.generate_report(target_domain, collected_data)
    logger.info("Reconnaissance workflow completed successfully")
    
    return report
     