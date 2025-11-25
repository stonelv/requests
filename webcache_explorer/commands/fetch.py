import os
import json
import time
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from webcache_explorer.utils import sanitize_url, extract_text
from webcache_explorer.config import Config

logger = logging.getLogger(__name__)

def fetch_url(url: str, session: requests.Session, timeout: int, retries: int) -> Dict[str, Any]:
    """Fetch a single URL with retries and timeouts."""
    try:
        start_time = time.time()
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        end_time = time.time()
        
        # Extract metadata
        metadata = {
            "url": url,
            "status": response.status_code,
            "headers": dict(response.headers),
            "timestamp": end_time,
            "fetch_duration": end_time - start_time,
            "success": True
        }
        
        return {
            "metadata": metadata,
            "content": response.text
        }
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {str(e)}")
        return {
            "metadata": {
                "url": url,
                "status": None,
                "headers": {},
                "timestamp": time.time(),
                "fetch_duration": 0,
                "success": False,
                "error": str(e)
            },
            "content": ""
        }

def fetch_urls(url_list_path: str, config: Config) -> None:
    """Fetch all URLs from the provided file concurrently."""
    # Create data directory if it doesn't exist
    os.makedirs(config.data_dir, exist_ok=True)
    
    # Read URLs from file
    with open(url_list_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        logger.info("No URLs found in the provided file.")
        return
    
    logger.info(f"Starting to fetch {len(urls)} URLs...")
    
    # Create a session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=config.retries,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Fetch URLs concurrently
    results = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = {executor.submit(fetch_url, url, session, config.timeout, config.retries): url for url in urls}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result["metadata"]["success"]:
                logger.info(f"Successfully fetched {result['metadata']['url']}")
            else:
                logger.error(f"Failed to fetch {result['metadata']['url']}: {result['metadata']['error']}")
    
    # Update cache index
    index_path = os.path.join(config.data_dir, "index.json")
    index = {}
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
    
    for result in results:
        metadata = result["metadata"]
        url = metadata["url"]
        filename = sanitize_url(url) + ".html"
        
        # Save content to file
        with open(os.path.join(config.data_dir, filename), 'w', encoding='utf-8') as f:
            f.write(result["content"])
        
        # Update index
        index[url] = {
            "filename": filename,
            "status": metadata["status"],
            "timestamp": metadata["timestamp"],
            "success": metadata["success"],
            **({"error": metadata["error"]} if "error" in metadata else {})
        }
    
    # Save updated index
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"Fetch completed. {len([r for r in results if r['metadata']['success']])} successful, {len([r for r in results if not r['metadata']['success']])} failed.")
