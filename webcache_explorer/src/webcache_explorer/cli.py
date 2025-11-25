"""Command-line interface for WebCache Explorer."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .config import Config
from .crawler import WebCrawler
from .cache import CacheManager
from .text_processor import TextProcessor


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from file.
    
    Args:
        file_path: Path to file containing URLs.
        
    Returns:
        List of URLs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
            return urls
    except FileNotFoundError:
        logging.error(f"URLs file not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Failed to load URLs from {file_path}: {e}")
        return []


def cmd_fetch(args, config: Config, crawler: WebCrawler, cache_manager: CacheManager):
    """Fetch URLs command."""
    urls = load_urls_from_file(args.urls_file)
    if not urls:
        print("No URLs to fetch.")
        return
    
    print(f"Fetching {len(urls)} URLs...")
    results = crawler.fetch_urls(urls, show_progress=not args.no_progress)
    
    # Store results in cache
    success_count = 0
    for result in results:
        if cache_manager.store(result):
            success_count += 1
    
    print(f"\nFetch completed: {success_count}/{len(results)} URLs processed successfully")
    
    # Show summary of failures
    failed_results = [r for r in results if not r.success]
    if failed_results:
        print(f"\nFailed URLs ({len(failed_results)}):")
        for result in failed_results[:10]:  # Show first 10 failures
            print(f"  - {result.url}: {result.error_message}")
        if len(failed_results) > 10:
            print(f"  ... and {len(failed_results) - 10} more failures")


def cmd_refetch(args, config: Config, crawler: WebCrawler, cache_manager: CacheManager):
    """Refetch failed URLs command."""
    failed_urls = cache_manager.get_failed_urls()
    if not failed_urls:
        print("No failed URLs to refetch.")
        return
    
    print(f"Refetching {len(failed_urls)} failed URLs...")
    results = crawler.fetch_urls(failed_urls, show_progress=not args.no_progress)
    
    # Update cache with new results
    success_count = 0
    for result in results:
        if result.success:
            cache_manager.store(result)
            success_count += 1
    
    print(f"\nRefetch completed: {success_count}/{len(results)} URLs successful")


def cmd_add_url(args, config: Config, crawler: WebCrawler, cache_manager: CacheManager):
    """Add URL command."""
    url = args.url
    
    # Validate URL
    if not crawler.validate_url(url):
        print(f"Invalid URL: {url}")
        return
    
    print(f"Fetching URL: {url}")
    result = crawler.fetch_url(url)
    
    if result.success:
        cache_manager.store(result)
        print(f"Successfully cached: {url}")
    else:
        print(f"Failed to fetch {url}: {result.error_message}")


def cmd_search(args, config: Config, crawler: WebCrawler, cache_manager: CacheManager, text_processor: TextProcessor):
    """Search command."""
    query = args.query
    max_results = args.max_results or config.max_search_results
    
    print(f"Searching for: '{query}'")
    results = text_processor.search_content(cache_manager, query, max_results)
    
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title or result.url}")
        print(f"   URL: {result.url}")
        print(f"   Score: {result.relevance_score:.3f}")
        print(f"   Length: {result.content_length} characters")
        print(f"   Matched: {', '.join(result.matched_keywords)}")
        print(f"   Snippet: {result.snippet}")


def cmd_stats(args, config: Config, cache_manager: CacheManager):
    """Stats command."""
    stats = cache_manager.get_stats()
    
    print("Cache Statistics:")
    print("-" * 40)
    print(f"Total entries: {stats['total_entries']}")
    print(f"Successful: {stats['successful_entries']}")
    print(f"Failed: {stats['failed_entries']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Average fetch time: {stats['average_fetch_time']:.2f}s")
    print(f"Index file: {stats['index_file']}")
    print(f"Data directory: {stats['data_directory']}")


def cmd_show(args, config: Config, cache_manager: CacheManager, text_processor: TextProcessor):
    """Show command."""
    url = args.url
    
    cached_data = cache_manager.retrieve(url)
    if not cached_data:
        print(f"No cached content found for: {url}")
        return
    
    print(f"Cached content for: {url}")
    print("-" * 80)
    
    if cached_data.get('error_message'):
        print(f"Error: {cached_data['error_message']}")
        return
    
    print(f"Status: {cached_data['status_code']}")
    print(f"Content-Type: {cached_data['content_type']}")
    print(f"Fetch time: {cached_data['fetch_time']:.2f}s")
    print(f"Content size: {cached_data['content_size']} bytes")
    print(f"Content hash: {cached_data['content_hash']}")
    
    if args.content and cached_data.get('content'):
        print("\nContent:")
        print("-" * 40)
        if args.no_html:
            # Extract text only
            text, title = text_processor.extract_text_from_html(cached_data['content'])
            print(text)
        else:
            print(cached_data['content'])
    
    if args.keywords and cached_data.get('content'):
        print("\nKeywords:")
        print("-" * 40)
        text, _ = text_processor.extract_text_from_html(cached_data['content'])
        keywords = text_processor.extract_keywords(text)
        for keyword, count in keywords[:20]:
            print(f"  {keyword}: {count}")


def cmd_export(args, config: Config, cache_manager: CacheManager):
    """Export command."""
    output_file = args.output
    
    try:
        cache_manager.export_index(output_file)
        print(f"Cache index exported to: {output_file}")
    except Exception as e:
        print(f"Failed to export cache index: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="WebCache Explorer - Concurrent web content caching and search tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s fetch                    # Fetch all URLs from urls.txt
  %(prog)s refetch                  # Refetch failed URLs
  %(prog)s add-url https://example.com  # Add and fetch a URL
  %(prog)s search "python tutorial" # Search cached content
  %(prog)s stats                    # Show cache statistics
  %(prog)s show https://example.com # Show cached content
  %(prog)s export results.json      # Export cache index
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path',
        default=None
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch URLs from file')
    fetch_parser.add_argument(
        'urls_file',
        nargs='?',
        default='urls.txt',
        help='File containing URLs to fetch (default: urls.txt)'
    )
    fetch_parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    
    # Refetch command
    refetch_parser = subparsers.add_parser('refetch', help='Refetch failed URLs')
    refetch_parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    
    # Add URL command
    add_url_parser = subparsers.add_parser('add-url', help='Add and fetch a single URL')
    add_url_parser.add_argument('url', help='URL to fetch and cache')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search cached content')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument(
        '--max-results', '-n',
        type=int,
        help='Maximum number of results to show'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show cached content for URL')
    show_parser.add_argument('url', help='URL to show')
    show_parser.add_argument(
        '--content', '-c',
        action='store_true',
        help='Show content'
    )
    show_parser.add_argument(
        '--no-html',
        action='store_true',
        help='Strip HTML tags from content'
    )
    show_parser.add_argument(
        '--keywords', '-k',
        action='store_true',
        help='Show extracted keywords'
    )
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export cache index')
    export_parser.add_argument('output', help='Output file path')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize components
    try:
        config = Config(args.config)
        crawler = WebCrawler(config)
        cache_manager = CacheManager(config)
        text_processor = TextProcessor(config)
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)
    
    try:
        # Execute command
        if args.command == 'fetch':
            cmd_fetch(args, config, crawler, cache_manager)
        elif args.command == 'refetch':
            cmd_refetch(args, config, crawler, cache_manager)
        elif args.command == 'add-url':
            cmd_add_url(args, config, crawler, cache_manager)
        elif args.command == 'search':
            cmd_search(args, config, crawler, cache_manager, text_processor)
        elif args.command == 'stats':
            cmd_stats(args, config, cache_manager)
        elif args.command == 'show':
            cmd_show(args, config, cache_manager, text_processor)
        elif args.command == 'export':
            cmd_export(args, config, cache_manager)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'crawler' in locals():
            crawler.close()


if __name__ == '__main__':
    main()