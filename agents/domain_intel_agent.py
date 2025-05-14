import autogen

class DomainIntelAgent(autogen.AssistantAgent):
    """Agent specialized in domain intelligence gathering, focusing on DNS and WHOIS information."""
    
    def __init__(self, llm_config):
        # Define the tools schemas specifically for DNS and WHOIS lookups
        tools_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "dns_lookup",
                    "description": "Performs DNS lookups (A, AAAA, MX, NS, TXT records) for a given domain.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "description": "The domain name to lookup."
                            }
                        },
                        "required": ["domain"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "whois_lookup",
                    "description": "Performs a WHOIS lookup for the given domain.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "description": "The domain name to perform WHOIS lookup."
                            }
                        },
                        "required": ["domain"]
                    }
                }
            }
        ]
        
        # Update the llm_config with the tools schemas
        updated_llm_config = llm_config.copy() if llm_config else {}
        updated_llm_config["tools"] = tools_schemas
        
        # Define the system message as per requirements
        system_message = """You are an AI assistant specialized in basic domain intelligence gathering. Your goal is to collect DNS records and WHOIS information for the target domain. You must use the provided tools: dns_lookup and whois_lookup. When you need to use a tool, respond with a tool_call. Provide the 'domain' parameter correctly. After successfully executing both tools for the target domain, summarize the key findings from DNS and WHOIS, then state TERMINATE. If a tool fails or returns no data, note it, attempt the other tool if available, then summarize and TERMINATE."""
        
        # Call the parent class constructor with the required parameters
        super().__init__(
            name="Domain_Intel_Agent",
            llm_config=updated_llm_config,
            system_message=system_message
        )
