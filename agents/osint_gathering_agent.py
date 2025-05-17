import autogen

class OSINTGatheringAgent(autogen.AssistantAgent):
    """Agent specialized in OSINT gathering through Google Dorking techniques."""
    
    def __init__(self, llm_config):
        # Define the tools schemas specifically for Google Dorking
        tools_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "search_google_dorks",
                    "description": "Perform Google dorking on a domain using predefined or custom dorks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "description": "Target domain to perform dorking on."
                            },
                            "dorks": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "List of specific dork queries. If not provided, uses common dorks."
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of search results to return. Default is 10."
                            }
                        },
                        "required": ["domain"]
                    }
                }
            }
        ]
        
        # Update the llm_config with the tools schemas
        updated_llm_config = llm_config.copy() if llm_config else {}
        updated_llm_config["tools"] = tools_schemas        # Define the system message as per requirements
        system_message = """You are an AI assistant for Open Source Intelligence (OSINT) gathering, focusing on Google Dorking. Your tool is search_google_dorks. Make one tool call for search_google_dorks, providing the 'domain' and optionally a list of specific 'dorks' to use. If no dorks are specified, the tool may use a default set. You can also specify a 'limit' parameter to control the number of results returned.

After the search, summarize any significant findings and then state TERMINATE. 

If you encounter errors like "rate limit exceeded", "Google API quota exceeded", or similar rate-limiting messages, inform the user that searches are being limited by Google and suggest they try again later or use fewer dorks. Then state TERMINATE.

If the search fails for other reasons or yields no results, note it and state TERMINATE."""
        
        # Call the parent class constructor with the required parameters
        super().__init__(
            name="OSINT_Gathering_Agent",
            llm_config=updated_llm_config,
            system_message=system_message
        ) 