#!/usr/bin/env python3
import time
import logging
from webcache_explorer.commands import fetch
from webcache_explorer.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Create a test URL list with 10 URLs
    test_urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/delay/1",  # Add a delay to test timeouts
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/encoding/utf8",
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]
    
    # Write test URLs to a file
    with open("bench_urls.txt", "w") as f:
        f.write("\n".join(test_urls))
    
    # Load configuration (use default for bench)
    config = Config()
    
    logger.info("Starting performance benchmark with 10 URLs...")
    start_time = time.time()
    
    # Fetch URLs
    fetch.fetch_urls("bench_urls.txt", config)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"Benchmark completed in {total_time:.2f} seconds")
    logger.info(f"Average time per URL: {total_time/len(test_urls):.2f} seconds")
    
    # Clean up test file
    import os
    os.remove("bench_urls.txt")

if __name__ == "__main__":
    main()
