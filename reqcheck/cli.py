#!/usr/bin/env python3
"""reqcheck command-line interface"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .__version__ import __version__
from .config import Config
from .runner import run_checks


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="reqcheck - A bulk URL checker tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/output options
    parser.add_argument(
        "--urls",
        help="File containing URLs to check (one per line)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (supports .csv or .json)"
    )
    
    # Request options
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "HEAD", "POST"],
        help="HTTP request method"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries per URL"
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Initial retry delay in seconds (exponential backoff)"
    )
    parser.add_argument(
        "--proxy",
        help="Proxy URL (e.g., http://proxy.example.com:8080)"
    )
    parser.add_argument(
        "--headers",
        help="Path to JSON file containing custom headers"
    )
    parser.add_argument(
        "--cookies",
        help="Path to JSON file containing cookies"
    )
    
    # Download options
    parser.add_argument(
        "--download",
        action="store_true",
        help="Enable download mode to save responses"
    )
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory to save downloaded files"
    )
    
    # Concurrency options
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests"
    )
    
    # Logging and output options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"reqcheck {__version__}"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point"""
    args = parse_args()
    
    # Validate required arguments
    if not args.urls:
        print("Error: --urls file is required", file=sys.stderr)
        sys.exit(1)
    
    urls_path = Path(args.urls)
    if not urls_path.exists():
        print(f"Error: URLs file not found at {urls_path}", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    config = Config.from_args(args)
    
    # Run checks
    try:
        run_checks(config)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()