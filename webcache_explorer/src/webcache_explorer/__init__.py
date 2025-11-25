"""WebCache Explorer - A concurrent web content caching and search tool."""

__version__ = "1.0.0"
__author__ = "WebCache Explorer Team"
__description__ = "A concurrent web content caching and search tool"

from .config import Config
from .crawler import WebCrawler, FetchResult
from .cache import CacheManager, CacheEntry
from .text_processor import TextProcessor, SearchResult

__all__ = [
    'Config',
    'WebCrawler',
    'FetchResult',
    'CacheManager',
    'CacheEntry',
    'TextProcessor',
    'SearchResult',
]