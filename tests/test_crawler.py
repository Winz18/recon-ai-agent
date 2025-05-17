import json
from tools.endpoint_helper import crawl_endpoints

def main():
    print("Testing endpoint crawler...")
    
    # Test URL
    test_url = "https://google.com"
    
    # Run the crawler
    results = crawl_endpoints(
        url=test_url,
        depth=1,
        output_format="json"
    )
    
    # Print results
    print(f"\nResults for {test_url}:")
    print(f"Found {results.get('discovered_endpoints_count', 0)} endpoints")
    
    # Print the first few endpoints from each method
    for method, endpoints in results.get("endpoints_by_method", {}).items():
        if endpoints:
            print(f"\n{method.capitalize()} (showing first 5):")
            for endpoint in endpoints[:5]:
                print(f"  - {endpoint}")

if __name__ == "__main__":
    main() 