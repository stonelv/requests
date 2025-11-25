import os
import json
import logging
from typing import Dict, Any

from webcache_explorer.utils import extract_text
from webcache_explorer.config import Config

logger = logging.getLogger(__name__)

def show_content(url: str, config: Config, raw: bool = False) -> None:
    """Show cached content for a specific URL."""
    index_path = os.path.join(config.data_dir, "index.json")
    
    if not os.path.exists(index_path):
        logger.error("Cache index not found. Please run 'fetch' command first.")
        return
    
    # Read index
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    if url not in index:
        logger.error(f"URL not found in cache: {url}")
        return
    
    entry = index[url]
    
    if not entry.get("success", False):
        logger.error(f"URL fetch failed: {url}. Error: {entry.get('error', 'Unknown error')}")
        return
    
    file_path = os.path.join(config.data_dir, entry["filename"])
    
    if not os.path.exists(file_path):
        logger.error(f"Content file not found for URL: {url}")
        return
    
    # Read and display content
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if raw:
        logger.info(f"Raw content for {url}:")
        print(content)
    else:
        text_content = extract_text(content)
        logger.info(f"Extracted text for {url}:")
        print(text_content)
