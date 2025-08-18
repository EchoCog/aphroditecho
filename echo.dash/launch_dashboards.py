#!/usr/bin/env python3

import sys
import logging
from unified_launcher import UnifiedLauncher, create_config_from_args, create_argument_parser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='dashboard_launcher.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for dashboard launcher"""
    
    # Parse arguments using unified launcher's parser
    parser = create_argument_parser("dashboards")
    args = parser.parse_args()
    
    # Create config from arguments  
    config = create_config_from_args("dashboards", args)
    
    # Use unified launcher
    launcher = UnifiedLauncher()
    return launcher.launch_sync(config)

if __name__ == "__main__":
    sys.exit(main())