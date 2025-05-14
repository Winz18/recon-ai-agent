import autogen

class WebAppReconAgent(autogen.AssistantAgent):
    """Agent specialized in web application reconnaissance, focusing on HTTP headers, technologies detection, 
    subdomain enumeration, and website screenshots."""
    
    def __init__(self, llm_config):
        # Define the tools schemas specifically for web application reconnaissance
        tools_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "get_http_headers",
                    "description": "Retrieves HTTP headers from a web server.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to get HTTP headers from. If not starting with http, https will be prepended."
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_subdomains",
                    "description": "Searches for subdomains of a given domain using passive techniques.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "description": "The base domain to find subdomains for."
                            },
                            "use_apis": {
                                "type": "boolean",
                                "description": "Whether to use online services (can be slower but more comprehensive). Default: True",
                                "default": True
                            }
                        },
                        "required": ["domain"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_technologies",
                    "description": "Detect technologies used by a website based on HTTP headers, HTML content and other indicators.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the website to analyze."
                            },
                            "check_js": {
                                "type": "boolean",
                                "description": "Whether to analyze JavaScript files (more comprehensive but slower)."
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capture_website_screenshot",
                    "description": "Captures a screenshot of a website using Selenium or Playwright.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the website to capture."
                            },
                            "output_path": {
                                "type": "string",
                                "description": "Directory path where to save the screenshot."
                            },
                            "fullpage": {
                                "type": "boolean",
                                "description": "Whether to capture the full page or just the viewport."
                            }
                        },
                        "required": ["url", "output_path"]
                    }
                }
            },
            # Adding extract_security_headers schema
            {
                "type": "function",
                "function": {
                    "name": "extract_security_headers",
                    "description": "Extracts and analyzes security-related HTTP headers from a web server.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to analyze security headers from. If not starting with http, https will be prepended."
                            }
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
        
        # Update the llm_config with the tools schemas
        updated_llm_config = llm_config.copy() if llm_config else {}
        updated_llm_config["tools"] = tools_schemas
        
        # Define the system message as per requirements
        system_message = """You are an AI assistant for web application reconnaissance. Your tasks are to gather HTTP headers, identify web technologies, find subdomains relevant to web applications, and capture website screenshots for a given target URL or domain. You must use the tools: get_http_headers, extract_security_headers, search_subdomains, detect_technologies, and capture_website_screenshot. Generate a tool_call for each tool. Ensure correct parameters ('url' for headers/tech/screenshot, 'domain' for subdomains). After executing all relevant tools, summarize the findings and then state TERMINATE. If a tool fails, note it and proceed."""
        
        # Call the parent class constructor with the required parameters
        super().__init__(
            name="WebApp_Recon_Agent",
            llm_config=updated_llm_config,
            system_message=system_message
        )
