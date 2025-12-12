"""Main runner for URL checks"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from pathlib import Path

from tqdm import tqdm

from .config import Config
from .logging_utils import setup_logger
from .requestor import Requestor
from .exporters import get_exporter
from .downloader import Downloader

logger = setup_logger()


def load_urls(urls_file: Path) -> List[str]:
    """Load URLs from file"""
    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not urls:
        raise ValueError("No URLs found in input file")
    
    logger.info(f"Loaded {len(urls)} URLs from {urls_file}")
    return urls


def run_checks(config: Config) -> None:
    """Main function to run URL checks"""
    # Setup logging
    setup_logger(config.verbose)
    
    # Load URLs
    urls = load_urls(config.urls_file)
    
    # Create requestor
    requestor = Requestor(
        method=config.method,
        timeout=config.timeout,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay,
        proxy=config.proxy,
        headers=config.headers,
        cookies=config.cookies
    )
    
    results = []
    
    # Run checks with concurrency
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(requestor.request, url): url for url in urls}
        
        # Process results with progress bar
        progress_bar = tqdm(
            total=len(urls),
            desc="Checking URLs",
            unit="url",
            disable=not config.show_progress
        )
        
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            progress_bar.update(1)
        
        progress_bar.close()
    
    # Close requestor
    requestor.close()
    
    # Print summary
    print_summary(results)
    
    # Export results
    if config.output_file:
        exporter = get_exporter(config.output_file)
        exporter.export(results)
    
    # Download mode
    if config.download:
        run_downloads(config, urls)


def run_downloads(config: Config, urls: List[str]) -> None:
    """Run downloads for all URLs"""
    logger.info(f"Starting download mode, saving to {config.download_dir}")
    
    downloader = Downloader({
        "timeout": config.timeout,
        "max_retries": config.max_retries,
        "retry_delay": config.retry_delay,
        "proxy": config.proxy,
        "headers": config.headers,
        "cookies": config.cookies,
        "download_dir": config.download_dir
    })
    
    results = []
    
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        future_to_url = {executor.submit(downloader.download, url, config.show_progress): url for url in urls}
        
        progress_bar = tqdm(
            total=len(urls),
            desc="Downloading files",
            unit="file",
            disable=not config.show_progress
        )
        
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            progress_bar.update(1)
        
        progress_bar.close()
    
    downloader.close()
    
    # Print download summary
    print_download_summary(results)


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of results"""
    total = len(results)
    success = sum(1 for r in results if r["status_code"] is not None and 200 <= r["status_code"] < 300)
    errors = sum(1 for r in results if r["error"] is not None)
    timed_out = sum(1 for r in results if r["timed_out"])
    redirected = sum(1 for r in results if r["redirected"])
    
    print(f"\n=== Summary ===")
    print(f"Total URLs checked: {total}")
    print(f"Successful responses: {success} ({success/total*100:.1f}%)")
    print(f"Errors: {errors} ({errors/total*100:.1f}%)")
    print(f"Timeouts: {timed_out} ({timed_out/total*100:.1f}%)")
    print(f"Redirected: {redirected} ({redirected/total*100:.1f}%)")
    
    if results:
        avg_time = sum(r["elapsed"] for r in results if r["elapsed"] is not None) / len(results)
        print(f"Average response time: {avg_time:.4f}s")


def print_download_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of download results"""
    total = len(results)
    success = sum(1 for r in results if r["success"])
    errors = sum(1 for r in results if not r["success"])
    
    print(f"\n=== Download Summary ===")
    print(f"Total files: {total}")
    print(f"Successfully downloaded: {success} ({success/total*100:.1f}%)")
    print(f"Failed downloads: {errors} ({errors/total*100:.1f}%)")