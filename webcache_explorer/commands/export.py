import os
import json
import logging
from typing import Dict, Any

from webcache_explorer.config import Config

logger = logging.getLogger(__name__)

def export_index(output_path: str, config: Config) -> None:
    """Export the cache index to a file."""
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
    
    # Export to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"Cache index exported to: {output_path}")
