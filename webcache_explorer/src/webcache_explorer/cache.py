"""Cache management for WebCache Explorer."""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class CacheEntry:
    """Cache entry metadata."""
    url: str
    content_hash: str
    status_code: int
    content_type: str
    fetch_time: float
    file_path: str
    error_message: Optional[str] = None
    content_size: int = 0
    last_modified: Optional[str] = None
    encoding: Optional[str] = None


class CacheManager:
    """Manages cached web content and metadata."""
    
    def __init__(self, config):
        """Initialize cache manager.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(config.data_dir)
        self.index_file = self.data_dir / config.index_file
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, CacheEntry]:
        """Load cache index from file."""
        if not self.index_file.exists():
            self.logger.info("No existing cache index found, starting fresh")
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Convert dictionary back to CacheEntry objects
            index = {}
            for url, entry_data in data.items():
                # Handle legacy format without content_size
                if 'content_size' not in entry_data:
                    entry_data['content_size'] = 0
                index[url] = CacheEntry(**entry_data)
                
            self.logger.info(f"Loaded cache index with {len(index)} entries")
            return index
            
        except Exception as e:
            self.logger.error(f"Failed to load cache index: {e}")
            return {}
    
    def _save_index(self):
        """Save cache index to file."""
        try:
            # Convert CacheEntry objects to dictionaries
            data = {url: asdict(entry) for url, entry in self.index.items()}
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(f"Saved cache index with {len(self.index)} entries")
            
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")
            raise
    
    def _get_cache_filename(self, url: str, content_hash: str) -> str:
        """Generate cache filename for URL and content hash."""
        # Create a safe filename from URL and hash
        import hashlib
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        content_short = content_hash[:8]
        
        # Get file extension based on content type (simplified)
        extension = '.html'  # Default
        
        return f"cache_{url_hash}_{content_short}{extension}"
    
    def _save_content(self, url: str, content: str, content_hash: str) -> str:
        """Save content to cache file.
        
        Args:
            url: URL of the content.
            content: Content to save.
            content_hash: Hash of the content.
            
        Returns:
            Path to saved file.
        """
        filename = self._get_cache_filename(url, content_hash)
        file_path = self.data_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.debug(f"Saved content for {url} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save content for {url}: {e}")
            raise
    
    def _load_content(self, file_path: str) -> Optional[str]:
        """Load content from cache file.
        
        Args:
            file_path: Path to cache file.
            
        Returns:
            Content if successful, None otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Failed to load content from {file_path}: {e}")
            return None
    
    def store(self, fetch_result) -> bool:
        """Store fetch result in cache.
        
        Args:
            fetch_result: FetchResult from WebCrawler.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            if fetch_result.success:
                # Save content to file
                file_path = self._save_content(
                    fetch_result.url,
                    fetch_result.content,
                    fetch_result.content_hash
                )
                
                # Create cache entry
                entry = CacheEntry(
                    url=fetch_result.url,
                    content_hash=fetch_result.content_hash,
                    status_code=fetch_result.status_code,
                    content_type=fetch_result.content_type or 'unknown',
                    fetch_time=fetch_result.fetch_time,
                    file_path=file_path,
                    content_size=len(fetch_result.content.encode('utf-8')),
                    encoding='utf-8'
                )
                
            else:
                # Store failed fetch
                entry = CacheEntry(
                    url=fetch_result.url,
                    content_hash='',
                    status_code=0,
                    content_type='unknown',
                    fetch_time=fetch_result.fetch_time,
                    file_path='',
                    error_message=fetch_result.error_message
                )
            
            # Update index
            self.index[fetch_result.url] = entry
            self._save_index()
            
            self.logger.info(f"Stored cache for {fetch_result.url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store cache for {fetch_result.url}: {e}")
            return False
    
    def retrieve(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached content for URL.
        
        Args:
            url: URL to retrieve.
            
        Returns:
            Dictionary with content and metadata if found, None otherwise.
        """
        if url not in self.index:
            return None
        
        entry = self.index[url]
        
        result = {
            'url': entry.url,
            'status_code': entry.status_code,
            'content_type': entry.content_type,
            'fetch_time': entry.fetch_time,
            'content_hash': entry.content_hash,
            'error_message': entry.error_message,
            'content_size': entry.content_size,
            'last_modified': entry.last_modified,
            'encoding': entry.encoding
        }
        
        if entry.error_message:
            # Failed fetch
            result['content'] = None
            result['success'] = False
        else:
            # Successful fetch
            content = self._load_content(entry.file_path)
            if content is not None:
                result['content'] = content
                result['success'] = True
            else:
                result['content'] = None
                result['success'] = False
                result['error_message'] = "Failed to load cached content"
        
        return result
    
    def get_failed_urls(self) -> List[str]:
        """Get list of URLs that failed to fetch.
        
        Returns:
            List of failed URLs.
        """
        return [url for url, entry in self.index.items() if entry.error_message is not None]
    
    def get_successful_urls(self) -> List[str]:
        """Get list of URLs that were successfully fetched.
        
        Returns:
            List of successful URLs.
        """
        return [url for url, entry in self.index.items() if entry.error_message is None]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics.
        """
        total_entries = len(self.index)
        successful_entries = len(self.get_successful_urls())
        failed_entries = len(self.get_failed_urls())
        
        total_size = sum(entry.content_size for entry in self.index.values() if entry.content_size > 0)
        
        # Calculate average fetch time
        fetch_times = [entry.fetch_time for entry in self.index.values() if entry.fetch_time]
        avg_fetch_time = sum(fetch_times) / len(fetch_times) if fetch_times else 0
        
        return {
            'total_entries': total_entries,
            'successful_entries': successful_entries,
            'failed_entries': failed_entries,
            'success_rate': successful_entries / total_entries if total_entries > 0 else 0,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'average_fetch_time': avg_fetch_time,
            'index_file': str(self.index_file),
            'data_directory': str(self.data_dir)
        }
    
    def search_urls(self, keyword: str) -> List[str]:
        """Search for URLs containing keyword.
        
        Args:
            keyword: Keyword to search for.
            
        Returns:
            List of matching URLs.
        """
        if len(keyword) < self.config.min_keyword_length:
            return []
        
        keyword_lower = keyword.lower()
        matching_urls = []
        
        for url in self.index.keys():
            if keyword_lower in url.lower():
                matching_urls.append(url)
        
        return matching_urls
    
    def remove(self, url: str) -> bool:
        """Remove cached entry for URL.
        
        Args:
            url: URL to remove.
            
        Returns:
            True if removed, False if not found.
        """
        if url not in self.index:
            return False
        
        entry = self.index[url]
        
        try:
            # Remove content file if it exists
            if entry.file_path and os.path.exists(entry.file_path):
                os.remove(entry.file_path)
                
            # Remove from index
            del self.index[url]
            self._save_index()
            
            self.logger.info(f"Removed cache for {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove cache for {url}: {e}")
            return False
    
    def clear(self):
        """Clear all cached content."""
        try:
            # Remove all cache files
            for entry in self.index.values():
                if entry.file_path and os.path.exists(entry.file_path):
                    os.remove(entry.file_path)
            
            # Clear index
            self.index.clear()
            self._save_index()
            
            self.logger.info("Cleared all cache")
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            raise
    
    def export_index(self, output_file: str):
        """Export cache index to file.
        
        Args:
            output_file: Output file path.
        """
        try:
            # Convert to serializable format
            data = {
                'export_time': datetime.now().isoformat(),
                'stats': self.get_stats(),
                'entries': {url: asdict(entry) for url, entry in self.index.items()}
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Exported cache index to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export cache index: {e}")
            raise