"""HTTP request handling with retry logic"""

import time
from typing import Dict, Optional, Tuple, Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .logging_utils import get_logger

logger = get_logger(__name__)


class Requestor:
    """Handles HTTP requests with retry logic"""
    
    def __init__(
        self,
        method: str = "GET",
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None
    ):
        self.method = method
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.proxy = proxy
        self.headers = headers or {}
        self.cookies = cookies or {}
        
        # Create session with retry adapter
        self.session = requests.Session()
        self._setup_retry_adapter()
        
        if self.proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        
    def _setup_retry_adapter(self) -> None:
        """Setup retry adapter for the session"""
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def request(self, url: str) -> Dict[str, Any]:
        """Send HTTP request and return result"""
        result = {
            "url": url,
            "final_url": None,
            "status_code": None,
            "elapsed": None,
            "redirected": False,
            "timed_out": False,
            "content_length": None,
            "headers": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            response = self.session.request(
                self.method,
                url,
                timeout=self.timeout,
                headers=self.headers,
                cookies=self.cookies,
                allow_redirects=True
            )
            
            elapsed = time.time() - start_time
            
            result.update({
                "final_url": response.url,
                "status_code": response.status_code,
                "elapsed": elapsed,
                "redirected": len(response.history) > 0,
                "timed_out": False
            })
            
            # Get content length
            if "Content-Length" in response.headers:
                try:
                    result["content_length"] = int(response.headers["Content-Length"])
                except ValueError:
                    pass
            
            # Get headers
            result["headers"] = dict(response.headers)
            
            logger.info(f"[{response.status_code}] {url} -> {response.url}")
            
        except requests.Timeout:
            elapsed = time.time() - start_time
            error_msg = "Request timed out"
            result.update({
                "elapsed": elapsed,
                "timed_out": True,
                "error": error_msg
            })
            logger.error(f"[TIMEOUT] {url}: {error_msg}")
            
        except requests.RequestException as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            result.update({
                "elapsed": elapsed,
                "error": error_msg
            })
            logger.error(f"[ERROR] {url}: {error_msg}")
            
        return result
    
    def download(self, url: str, output_path: str) -> Tuple[bool, str, Optional[int]]:
        """Download file from URL"""
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                headers=self.headers,
                cookies=self.cookies,
                stream=True
            )
            response.raise_for_status()
            
            content_length = None
            if "Content-Length" in response.headers:
                try:
                    content_length = int(response.headers["Content-Length"])
                except ValueError:
                    pass
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded: {url} -> {output_path}")
            return True, "Download successful", content_length
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed: {url} -> {output_path}")
            return False, error_msg, None
    
    def close(self) -> None:
        """Close the session"""
        self.session.close()