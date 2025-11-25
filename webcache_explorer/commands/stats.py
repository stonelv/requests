import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

from webcache_explorer.config import Config

logger = logging.getLogger(__name__)

def show_stats(config: Config) -> None:
    """Show cache statistics."""
    index_path = os.path.join(config.data_dir, "index.json")
    
    if not os.path.exists(index_path):
        logger.error("Cache index not found. Please run 'fetch' command first.")
        return
    
    # Read index
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    if not index:
        logger.info("No URLs found in the cache index.")
        return
    
    # Calculate statistics
    total_urls = len(index)
    successful_urls = len([entry for entry in index.values() if entry.get("success", False)])
    failed_urls = total_urls - successful_urls
    
    # Calculate cache size
    total_size = 0
    for entry in index.values():
        file_path = os.path.join(config.data_dir, entry["filename"])
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    # Calculate average success rate
    success_rate = (successful_urls / total_urls) * 100 if total_urls > 0 else 0
    
    # Find oldest and newest entries
    if index:
        oldest_timestamp = min(entry["timestamp"] for entry in index.values())
        newest_timestamp = max(entry["timestamp"] for entry in index.values())
        oldest_date = datetime.fromtimestamp(oldest_timestamp)
        newest_date = datetime.fromtimestamp(newest_timestamp)
    else:
        oldest_date = None
        newest_date = None
    
    # Display statistics
    logger.info("Cache Statistics:")
    logger.info(f"  Total URLs: {total_urls}")
    logger.info(f"  Successful: {successful_urls} ({success_rate:.1f}%)")
    logger.info(f"  Failed: {failed_urls}")
    logger.info(f"  Total Cache Size: {total_size / (1024 * 1024):.2f} MB")
    if oldest_date and newest_date:
        logger.info(f"  Oldest Entry: {oldest_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Newest Entry: {newest_date.strftime('%Y-%m-%d %H:%M:%S')}")
