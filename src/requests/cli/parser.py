"""
Argument parser for rhttp CLI tool.
"""

import argparse
import sys
from typing import List, Optional, Dict, Any


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for rhttp CLI."""
    parser = argparse.ArgumentParser(
        prog="rhttp",
        description="A powerful HTTP client CLI tool built on requests library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rhttp https://httpbin.org/get
  rhttp https://httpbin.org/post -X POST --json '{"key": "value"}'
  rhttp https://httpbin.org/headers -H "User-Agent: MyApp" -H "Accept: application/json"
  rhttp https://httpbin.org/basic-auth/user/pass --auth user:pass
  rhttp https://httpbin.org/bearer --bearer my-token
  rhttp --batch config.yaml
        """
    )

    # Single request mode
    parser.add_argument("url", nargs="?", help="URL to request")
    
    # HTTP method
    parser.add_argument(
        "--method", "-X",
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        help="HTTP method (default: GET)"
    )

    # Headers
    parser.add_argument(
        "-H", "--header",
        action="append",
        dest="headers",
        help="HTTP header (can be used multiple times)"
    )

    # Data options
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument(
        "--data", "-d",
        help="Form data as key=value pairs (e.g., 'key1=value1&key2=value2')"
    )
    data_group.add_argument(
        "--json", "-j",
        help="JSON data as string"
    )
    data_group.add_argument(
        "--file", "-f",
        help="File to upload"
    )
    parser.add_argument(
        "--file-field",
        help="Field name for file upload (default: file)"
    )

    # Authentication
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        "--auth", "-a",
        help="Basic authentication as user:pass"
    )
    auth_group.add_argument(
        "--bearer", "-b",
        help="Bearer token authentication"
    )

    # Request options
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=0,
        help="Number of retries on failure (default: 0)"
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=1.0,
        help="Initial backoff delay for retries in seconds (default: 1.0)"
    )

    # Output options
    parser.add_argument(
        "--save", "-s",
        help="Save response to file"
    )
    parser.add_argument(
        "--show",
        choices=["headers", "body", "all"],
        default="all",
        help="What to show in output (default: all)"
    )

    # Color output
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument(
        "--color",
        action="store_true",
        default=True,
        help="Enable colored output (default)"
    )
    color_group.add_argument(
        "--no-color",
        action="store_false",
        dest="color",
        help="Disable colored output"
    )

    # Batch processing
    parser.add_argument(
        "--batch",
        help="YAML configuration file for batch processing"
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Validate arguments
    if not parsed_args.batch and not parsed_args.url:
        parser.error("URL is required when not using --batch mode")

    if parsed_args.batch and parsed_args.url:
        parser.error("Cannot specify URL when using --batch mode")

    # Parse headers
    if parsed_args.headers:
        parsed_args.headers = parse_headers(parsed_args.headers)
    else:
        parsed_args.headers = {}

    # Parse form data
    if parsed_args.data:
        parsed_args.data = parse_form_data(parsed_args.data)

    return parsed_args


def parse_headers(headers: List[str]) -> Dict[str, str]:
    """Parse HTTP headers from command line format."""
    result = {}
    for header in headers:
        if ":" not in header:
            raise ValueError(f"Invalid header format: {header}")
        key, value = header.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def parse_form_data(data: str) -> Dict[str, str]:
    """Parse form data from key=value format."""
    result = {}
    for pair in data.split("&"):
        if "=" not in pair:
            raise ValueError(f"Invalid form data format: {pair}")
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments."""
    if args.retries < 0:
        raise ValueError("Retries must be non-negative")
    
    if args.retry_backoff < 0:
        raise ValueError("Retry backoff must be non-negative")
    
    if args.timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    if args.batch and not args.batch.endswith(('.yaml', '.yml')):
        raise ValueError("Batch config file must be a YAML file")