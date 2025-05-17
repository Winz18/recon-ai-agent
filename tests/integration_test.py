#!/usr/bin/env python
import autogen
import os
from agents import WebAppReconAgent

def test_webapp_agent():
    print("Testing WebAppReconAgent tool configuration...")
    
    # Create a minimal valid LLM config
    llm_config = {
        "config_list": [{"model": "gpt-3.5-turbo", "api_key": "dummy-key"}],
        "temperature": 0.1
    }
    
    # Create the agent
    agent = WebAppReconAgent(llm_config=llm_config)
    
    # Extract tool names from the agent's configuration
    tool_names = [tool['function']['name'] for tool in agent.llm_config['tools'] 
                  if tool['type'] == 'function']
    
    print("\nTools available in WebAppReconAgent:")
    for tool in tool_names:
        print(f"- {tool}")
    
    print(f"\nIs 'crawl_endpoints' in the tools? {'Yes' if 'crawl_endpoints' in tool_names else 'No'}")

def test_workflow_function_map():
    print("\nChecking if workflow imports endpoint crawler...")
    
    # Import directly from the module
    import workflows.standard_recon_workflow as workflow_module
    
    # Get the source code of the module to check for crawl_endpoints imports
    import inspect
    source = inspect.getsource(workflow_module)
    
    print(f"'crawl_endpoints' is imported in workflow: {'crawl_endpoints,' in source or 'crawl_endpoints)' in source}")
    
    # See if there's a function_map entry for crawl_endpoints
    print(f"'enable_crawler' setting exists in tool_config: {'enable_crawler' in source}")
    print(f"'crawl_endpoints' is registered in function_map: {'function_map[\"crawl_endpoints\"]' in source}")
    
    # Check if crawl_endpoints is included in the agent prompts
    print(f"'website endpoints' is included in the agent prompt: {'website endpoints' in source}")
    
    print("Integration check complete!")

if __name__ == "__main__":
    print("=== WebAppReconAgent and Endpoint Crawler Integration Test ===\n")
    
    # Test the WebAppReconAgent
    try:
        test_webapp_agent()
    except Exception as e:
        print(f"Error testing WebAppReconAgent: {e}")
    
    # Test the workflow imports
    try:
        test_workflow_function_map()
    except Exception as e:
        print(f"Error testing workflow integration: {e}") 