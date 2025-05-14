# main.py
import sys
import os
import argparse
from typing import Dict, List, Optional, Union

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__))) # Giả sử main.py nằm trong thư mục gốc dự án
# Nếu main.py nằm trong thư mục con (ví dụ: scripts), bạn cần điều chỉnh lại:
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import config
from config import settings
from utils.logging_setup import setup_logging, get_logger

# Cài đặt logging
logger = setup_logging()

def main():
    """
    Entry point for reconnaissance workflows.
    Parses command line arguments and runs the selected workflow.
    """
    parser = argparse.ArgumentParser(description='AI-powered Reconnaissance for Penetration Testing')
    
    # Add command line arguments
    parser.add_argument('-d', '--domain', type=str, default=settings.DEFAULT_TARGET_DOMAIN,
                      help=f'Target domain to analyze (default: {settings.DEFAULT_TARGET_DOMAIN})')
    parser.add_argument('-m', '--model', type=str, default="gemini-2.5-pro-preview-05-06",
                      help='Google Vertex AI model ID to use')
    parser.add_argument('-w', '--workflow', type=str, choices=["standard"], default="standard",
                      help='Workflow to run (default: standard)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting '{args.workflow}' reconnaissance workflow for: {args.domain}")
    
    # Select and run the appropriate workflow based on user choice
    if args.workflow == "standard":
        try:
            # Import the standard workflow
            from workflows.standard_recon_workflow import run_standard_recon_workflow
            
            # Run the standard workflow with the specified parameters
            report = run_standard_recon_workflow(
                target_domain=args.domain, 
                model_id=args.model
            )
            
            # Print a summary of the report
            print("\n=== RECONNAISSANCE REPORT SUMMARY ===")
            print(f"Target: {args.domain}")
            
            if isinstance(report, dict) and "summary" in report:
                print(f"\n{report['summary']}")
            elif isinstance(report, str):
                print(f"\n{report}")
            else:
                print("\nReport generated successfully. Check details in the logs.")
                
        except ImportError as e:
            logger.error(f"Failed to import standard workflow: {e}")
            print(f"Error: Could not load the standard workflow. {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error during workflow execution: {e}")
            print(f"Error: The workflow failed with error: {e}")
            sys.exit(1)
    
    # Add additional workflow options here in the future
    # elif args.workflow == "another_workflow":
    #     ...
    
    logger.info(f"Finished '{args.workflow}' reconnaissance workflow")
    return 0

if __name__ == "__main__":
    sys.exit(main())