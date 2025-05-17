#!/usr/bin/env python

print("Testing imports in standard_recon_workflow.py...")

# Import the workflow module
import workflows.standard_recon_workflow as workflow

# Check if crawl_endpoints is in the module's global namespace
has_crawl_endpoints = hasattr(workflow, 'crawl_endpoints')
print(f"workflow module has crawl_endpoints attribute: {has_crawl_endpoints}")

# Print out the names of all imported modules
print("\nAll imports in workflow module:")
for name in dir(workflow):
    if not name.startswith('__'):
        print(f"- {name}")

print("\nTesting WebAppReconAgent crawl_endpoints tool schema...")
# Import the agent
from agents.webapp_recon_agent import WebAppReconAgent

# Create a dummy config
dummy_config = {"config_list": [{"model": "gpt-3.5-turbo", "api_key": "dummy"}]}

# Try to get the tool schema
try:
    agent = WebAppReconAgent(llm_config=dummy_config)
    tools = agent.llm_config.get("tools", [])
    
    # Find crawl_endpoints schema
    for tool in tools:
        if tool.get("type") == "function" and tool.get("function", {}).get("name") == "crawl_endpoints":
            print("Found crawl_endpoints tool schema in WebAppReconAgent!")
            print(f"Tool description: {tool['function'].get('description', 'No description')}")
            break
    else:
        print("Could not find crawl_endpoints tool schema in WebAppReconAgent")
except Exception as e:
    print(f"Error creating agent: {e}") 