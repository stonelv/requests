import re
import os
import json
from typing import Optional, Dict, Any, List
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    """HTML parser to strip tags from HTML content."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []
    
    def handle_data(self, d):
        self.fed.append(d)
    
    def get_data(self):
        return ''.join(self.fed)

def extract_text(html: str) -> str:
    """Extract text from HTML content by stripping tags."""
    if not html:
        return ""
    
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def sanitize_url(url: str) -> str:
    """Sanitize URL to create a safe filename."""
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    # Remove trailing slash
    url = url.rstrip('/')
    # Replace invalid characters with underscores
    url = re.sub(r'[\/:*?"<>|]', '_', url)
    # Truncate to 200 characters to avoid filename length issues
    return url[:200]

def load_index(index_path: str) -> Dict[str, Any]:
    """Load cache index from JSON file."""
    if not os.path.exists(index_path):
        return {}
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_index(index: Dict[str, Any], index_path: str) -> None:
    """Save cache index to JSON file."""
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def get_cache_file_path(url: str, data_dir: str) -> str:
    """Get cache file path for a URL."""
    sanitized_url = sanitize_url(url)
    return os.path.join(data_dir, f"{sanitized_url}.html")

def get_metrics_file_path(data_dir: str) -> str:
    """Get metrics file path."""
    return os.path.join(data_dir, "metrics.json")

def load_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load metrics from JSON file."""
    if not os.path.exists(metrics_path):
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_time': 0.0
        }
    with open(metrics_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metrics(metrics: Dict[str, Any], metrics_path: str) -> None:
    """Save metrics to JSON file."""
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def calculate_similarity(query: str, text: str) -> float:
    """Calculate similarity between query and text (simple token matching)."""
    query_tokens = set(query.lower().split())
    text_tokens = set(text.lower().split())
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)

def rank_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Rank search results by similarity to query."""
    for result in results:
        result['similarity'] = calculate_similarity(query, result['text'])
    return sorted(results, key=lambda x: x['similarity'], reverse=True)
