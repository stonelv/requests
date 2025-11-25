"""Web crawling functionality for WebCache Explorer."""

import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class FetchResult:
    """Result of a web fetch operation."""
    url: str
    success: bool
    content: Optional[str] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    fetch_time: Optional[float] = None
    content_hash: Optional[str] = None


class WebCrawler:
    """Web crawler with concurrent fetching and retry mechanisms."""
    
    def __init__(self, config):
        """Initialize web crawler.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create configured requests session."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=self.config.max_workers)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'WebCache Explorer/1.0.0 (Educational Purpose)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for change detection."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _fetch_single_url(self, url: str) -> FetchResult:
        """Fetch a single URL with retry logic.
        
        Args:
            url: URL to fetch.
            
        Returns:
            FetchResult with fetch details.
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Fetching URL: {url}")
            
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=True,
                stream=True
            )
            
            # Check content size before downloading
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.config.max_content_size:
                raise ValueError(f"Content too large: {content_length} bytes")
            
            # Download content
            content = response.text
            
            # Check content size after downloading
            if len(content.encode('utf-8')) > self.config.max_content_size:
                raise ValueError(f"Content too large: {len(content.encode('utf-8'))} bytes")
            
            fetch_time = time.time() - start_time
            content_hash = self._calculate_content_hash(content)
            
            result = FetchResult(
                url=url,
                success=True,
                content=content,
                status_code=response.status_code,
                content_type=response.headers.get('content-type', 'unknown'),
                fetch_time=fetch_time,
                content_hash=content_hash
            )
            
            self.logger.info(f"Successfully fetched {url} in {fetch_time:.2f}s")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {self.config.timeout}s"
            self.logger.error(f"Timeout fetching {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error_message=error_msg,
                fetch_time=time.time() - start_time
            )
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            self.logger.error(f"Connection error fetching {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error_message=error_msg,
                fetch_time=time.time() - start_time
            )
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {str(e)}"
            self.logger.error(f"HTTP error fetching {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error_message=error_msg,
                fetch_time=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error fetching {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error_message=error_msg,
                fetch_time=time.time() - start_time
            )
    
    def fetch_urls(self, urls: List[str], show_progress: bool = True) -> List[FetchResult]:
        """Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch.
            show_progress: Whether to show progress bar.
            
        Returns:
            List of FetchResult objects.
        """
        self.logger.info(f"Starting to fetch {len(urls)} URLs with {self.config.max_workers} workers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(self._fetch_single_url, url): url for url in urls}
            
            # Process completed tasks
            if show_progress:
                try:
                    from tqdm import tqdm
                    progress = tqdm(as_completed(future_to_url), total=len(urls), desc="Fetching URLs")
                except ImportError:
                    progress = as_completed(future_to_url)
            else:
                progress = as_completed(future_to_url)
            
            for future in progress:
                try:
                    result = future.result()
                    results.append(result)
                    
                    if show_progress and hasattr(progress, 'set_postfix'):
                        success_count = sum(1 for r in results if r.success)
                        progress.set_postfix({"Success": f"{success_count}/{len(results)}"})
                        
                except Exception as e:
                    url = future_to_url[future]
                    self.logger.error(f"Exception in future for {url}: {e}")
                    results.append(FetchResult(
                        url=url,
                        success=False,
                        error_message=f"Future exception: {str(e)}"
                    ))
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Fetch completed: {success_count}/{len(urls)} URLs successful")
        
        return results
    
    def fetch_url(self, url: str) -> FetchResult:
        """Fetch a single URL.
        
        Args:
            url: URL to fetch.
            
        Returns:
            FetchResult with fetch details.
        """
        return self._fetch_single_url(url)
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format.
        
        Args:
            url: URL to validate.
            
        Returns:
            True if URL is valid, False otherwise.
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def close(self):
        """Close the crawler and cleanup resources."""
        if self.session:
            self.session.close()