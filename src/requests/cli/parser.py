# -*- coding: utf-8 -*-
"""Command line argument parser for rhttp tool."""
import argparse
import sys
from typing import List, Dict, Any

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='rhttp',
        description='A command-line HTTP client for making requests with advanced features.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Common arguments
    parser.add_argument('url', nargs='?', help='URL for single request mode')
    parser.add_argument('-X', '--method', default='GET', help='HTTP method to use')
    parser.add_argument('-H', '--header', action='append', default=[], help='Custom headers (repeatable)')
    parser.add_argument('--data', help='Form data to send (application/x-www-form-urlencoded)')
    parser.add_argument('--json', help='JSON data to send (application/json)')
    parser.add_argument('--file', help='File to upload')
    parser.add_argument('--auth', help='Basic authentication (user:pass)')
    parser.add_argument('--bearer', help='Bearer token authentication')
    parser.add_argument('--timeout', type=float, default=30.0, help='Request timeout in seconds')
    parser.add_argument('--retries', type=int, default=0, help='Number of retries')
    parser.add_argument('--retry-backoff', type=float, default=1.0, help='Initial retry backoff in seconds')
    parser.add_argument('--save', help='Save response to file')
    parser.add_argument('--show', choices=['headers', 'body', 'all'], default='body', help='What to show in output')
    parser.add_argument('--color', action='store_true', default=True, help='Enable colored output')
    parser.add_argument('--no-color', action='store_false', dest='color', help='Disable colored output')

    # Batch mode argument
    parser.add_argument('--batch', help='Batch mode configuration file (YAML)')

    return parser


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = create_parser()
    return parser.parse_args(args or sys.argv[1:])


def parse_headers(header_list: List[str]) -> Dict[str, str]:
    """Parse list of headers into a dictionary."""
    headers = {}
    for header in header_list:
        if ':' not in header:
            continue
        key, value = header.split(':', 1)
        headers[key.strip()] = value.strip()
    return headers


def parse_auth(auth_str: str) -> tuple:
    """Parse authentication string into (user, pass) tuple."""
    if ':' not in auth_str:
        return auth_str, ''
    user, password = auth_str.split(':', 1)
    return user, password
