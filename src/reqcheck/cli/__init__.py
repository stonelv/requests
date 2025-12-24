#!/usr/bin/env python3
import sys
import os
from typing import Optional
from ..config import config
from ..logging_utils import init_logger
from ..runner import create_runner

def main() -> int:
    try:
        # Parse command line arguments
        config.parse_args()
        
        # Initialize logger
        init_logger()
        
        # Create runner and run
        runner = create_runner()
        runner.run()
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())