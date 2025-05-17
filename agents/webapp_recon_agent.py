import autogen

class WebAppReconAgent(autogen.AssistantAgent):
    """Agent specialized in web application reconnaissance, focusing on HTTP headers, technologies detection, 
    subdomain enumeration, website screenshots, and endpoint crawling."""
    
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
            },
            {
                "type": "function",
                "function": {
                    "name": "crawl_endpoints",
                    "description": "Crawls a website to discover and enumerate application endpoints.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the website to crawl. If not starting with http, https will be prepended."
                            },
                            "depth": {
                                "type": "integer",
                                "description": "The depth of the crawl (number of levels to follow links). Default: 1",
                                "default": 1
                            },
                            "output_format": {
                                "type": "string",
                                "description": "The format to output the discovered endpoints (e.g., 'json', 'txt'). Default: 'json'",
                                "default": "json"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            # Add new tool schemas
            {
                "type": "function",
                "function": {
                    "name": "analyze_ssl_tls",
                    "description": "Analyzes SSL/TLS configuration of a web server for security issues.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to analyze SSL/TLS configuration for"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Connection timeout in seconds",
                                "default": 10
                            },
                            "check_cert_info": {
                                "type": "boolean",
                                "description": "Whether to check certificate information",
                                "default": True
                            },
                            "check_protocols": {
                                "type": "boolean",
                                "description": "Whether to check supported protocols",
                                "default": True
                            },
                            "check_ciphers": {
                                "type": "boolean",
                                "description": "Whether to check for weak ciphers",
                                "default": True
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_waf",
                    "description": "Detects if a Web Application Firewall (WAF) is protecting a website and attempts to identify it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to check for WAF protection"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Connection timeout in seconds",
                                "default": 10
                            },
                            "user_agent": {
                                "type": "string",
                                "description": "Custom User-Agent string to use (defaults to a standard browser)"
                            },
                            "test_payloads": {
                                "type": "boolean",
                                "description": "Whether to use test payloads to trigger WAF responses",
                                "default": True
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_cors_config",
                    "description": "Checks for Cross-Origin Resource Sharing (CORS) misconfigurations on a web server.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to check for CORS misconfigurations"
                            },
                            "test_origins": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Custom origins to test (defaults to a predefined list)"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Connection timeout in seconds",
                                "default": 10
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_cms",
                    "description": "Detects the Content Management System (CMS) used by a website.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the website to scan"
                            },
                            "deep_scan": {
                                "type": "boolean",
                                "description": "Whether to perform a deeper scan for version information",
                                "default": False
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Connection timeout in seconds",
                                "default": 10
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
        system_message = """You are an AI assistant for web application reconnaissance. Your tasks are to gather HTTP headers, identify web technologies, find subdomains relevant to web applications, capture website screenshots for a given target URL or domain, discover website endpoints, analyze SSL/TLS security, detect web application firewalls (WAFs), check for CORS misconfigurations, and identify content management systems (CMS). You must use the tools: get_http_headers, extract_security_headers, search_subdomains, detect_technologies, capture_website_screenshot, crawl_endpoints, analyze_ssl_tls, detect_waf, check_cors_config, and detect_cms. 

IMPORTANT: Make only ONE tool call at a time, and wait for the response before making the next call. Do not make multiple tool calls in a single message.

Ensure correct parameters ('url' for headers/tech/screenshot/endpoints/ssl/waf/cors/cms, 'domain' for subdomains). After executing all relevant tools one by one, summarize the findings and then state TERMINATE. If a tool fails, note it and proceed."""
        
        # Call the parent class constructor with the required parameters
        super().__init__(
            name="WebApp_Recon_Agent",
            llm_config=updated_llm_config,
            system_message=system_message
        )
