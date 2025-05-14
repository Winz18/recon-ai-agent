import autogen

class NetworkReconAgent(autogen.AssistantAgent):
    """Agent specialized in network reconnaissance, focusing specifically on port scanning."""
    
    def __init__(self, llm_config):
        # Define the tools schemas specifically for port scanning
        tools_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "scan_ports",
                    "description": "Scan ports on a target host using basic socket connections.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target IP address or hostname to scan."
                            },
                            "ports": {
                                "type": "array",
                                "items": {
                                    "type": "integer"
                                },
                                "description": "List of specific ports to scan. If not provided, scans top 100 common ports."
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Socket connection timeout in seconds. Default is 1.0 second."
                            }
                        },
                        "required": ["target"]
                    }
                }
            }
        ]
        
        # Update the llm_config with the tools schemas
        updated_llm_config = llm_config.copy() if llm_config else {}
        updated_llm_config["tools"] = tools_schemas
        
        # Define the system message as per requirements
        system_message = """You are an AI assistant for network reconnaissance, specifically port scanning. Your primary tool is scan_ports. Generate a tool_call for scan_ports, providing the 'target' (IP address or hostname) and optionally a list of 'ports'. If no ports are specified, the tool will scan common ports. After the scan is complete, summarize the open ports found and then state TERMINATE. If the scan fails, note it and TERMINATE."""
        
        # Call the parent class constructor with the required parameters
        super().__init__(
            name="Network_Recon_Agent",
            llm_config=updated_llm_config,
            system_message=system_message
        ) 