#!/usr/bin/env python3

import argparse
import logging
from typing import List, Dict, Any

from webcache_explorer import __version__
from webcache_explorer.commands import fetch, refetch, add_url, search, stats, show, export
from webcache_explorer.config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():    
    parser = argparse.ArgumentParser(
        description='WebCache Explorer - A tool for batch URL caching and exploration',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument('--config', default='config.toml', help='Path to configuration file')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch URLs from urls.txt')
    fetch_parser.add_argument('--url-list', default='urls.txt', help='Path to URL list file')
    
    # Refetch command
    refetch_parser = subparsers.add_parser('refetch', help='Refetch all cached URLs')
    
    # Add-url command
    add_url_parser = subparsers.add_parser('add-url', help='Add a new URL to cache')
    add_url_parser.add_argument('url', help='URL to add')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search cached content')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--top-k', type=int, default=10, help='Number of top results to return')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show cached content for a URL')
    show_parser.add_argument('url', help='URL to show')
    show_parser.add_argument('--raw', action='store_true', help='Show raw content instead of extracted text')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export cache index')
    export_parser.add_argument('output', help='Output file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Execute command
    if args.command == 'fetch':
        fetch.fetch_urls(args.url_list, config)
    elif args.command == 'refetch':
        refetch.refetch_all(config)
    elif args.command == 'add-url':
        add_url.add_single_url(args.url, config)
    elif args.command == 'search':
        search.search_content(args.query, config, args.top_k)
    elif args.command == 'stats':
        stats.show_stats(config)
    elif args.command == 'show':
        show.show_content(args.url, config, args.raw)
    elif args.command == 'export':
        export.export_index(args.output, config)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
