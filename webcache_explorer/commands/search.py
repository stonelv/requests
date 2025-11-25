import os
import json
import logging
from typing import List, Dict, Any, Tuple
import re
from collections import Counter

from webcache_explorer.utils import extract_text
from webcache_explorer.config import Config

logger = logging.getLogger(__name__)

def search_content(query: str, config: Config, top_k: int = 10) -> None:
    """Search cached content for the given query."""
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
    
    logger.info(f"Searching for: {query} (top {top_k} results)")
    
    # Preprocess query
    query_terms = query.lower().split()
    
    results = []
    
    # Search through all cached URLs
    for url, entry in index.items():
        if not entry.get("success", False):
            continue
            
        file_path = os.path.join(config.data_dir, entry["filename"])
        
        if not os.path.exists(file_path):
            logger.warning(f"Content file not found for URL: {url}")
            continue
            
        # Read and extract text from HTML
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
            
        text_content = extract_text(html_content)
        
        # Calculate relevance score
        text_lower = text_content.lower()
        score = 0
        
        for term in query_terms:
            # Exact matches
            score += text_lower.count(term)
            
            # Partial matches (whole words only)
            score += len(re.findall(rf'\b{re.escape(term)}', text_lower))
        
        if score > 0:
            results.append((score, url, text_content[:200]))  # Save first 200 chars as snippet
    
    # Sort results by score descending
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Display top K results
    if not results:
        logger.info("No results found for the query.")
        return
    
    logger.info(f"Found {len(results)} results. Top {top_k}:")
    for i, (score, url, snippet) in enumerate(results[:top_k], 1):
        logger.info(f"{i}. Score: {score} - {url}")
        logger.info(f"   Snippet: {snippet}...")
