import requests
import time
import random
from typing import Dict, Optional, Any
from requests.exceptions import RequestException
from ..config import config
from ..logging_utils import get_logger

class RequestResult:
    def __init__(self, url: str):
        self.url = url
        self.status_code: Optional[int] = None
        self.final_url: Optional[str] = None
        self.elapsed: float = 0.0
        self.redirected: bool = False
        self.timed_out: bool = False
        self.content_length: Optional[int] = None
        self.headers: Dict[str, str] = {}
        self.error: Optional[str] = None
        self.success: bool = False

class Requestor:
    def __init__(self):
        self.logger = get_logger()
        self.session = requests.Session()
        
        # Configure proxy if set
        if config.proxy:
            self.session.proxies = {
                "http": config.proxy,
                "https": config.proxy
            }
        
        # Configure headers
        if config.headers:
            self.session.headers.update(config.headers)
    
    def send_request(self, url: str) -> RequestResult:
        result = RequestResult(url)
        start_time = time.time()
        
        for attempt in range(config.retries + 1):
            try:
                self.logger.debug(f"Attempt {attempt + 1} for URL: {url}")
                response = self.session.get(
                    url,
                    timeout=config.timeout,
                    allow_redirects=True
                )
                
                # Update result
                result.status_code = response.status_code
                result.final_url = response.url
                result.elapsed = time.time() - start_time
                result.redirected = response.history != []
                result.timed_out = False
                result.content_length = int(response.headers.get("Content-Length", "0")) if "Content-Length" in response.headers else None
                result.headers = dict(response.headers)
                result.success = True
                
                self.logger.debug(f"Success for URL: {url} (Status: {response.status_code})")
                return result
                
            except RequestException as e:
                error_msg = f"Attempt {attempt + 1} failed for URL: {url}. Error: {str(e)}"
                if isinstance(e, requests.exceptions.Timeout):
                    result.timed_out = True
                    error_msg += " (Timeout)"
                self.logger.debug(error_msg)
                
                # If last attempt, record error
                if attempt == config.retries:
                    result.error = str(e)
                    result.success = False
                    self.logger.error(f"All attempts failed for URL: {url}. Error: {str(e)}")
                    return result
                
                # Calculate delay with jitter
                delay = config.retry_delay * (config.retry_backoff ** attempt)
                delay += random.uniform(0, delay * 0.1)  # Add jitter
                
                self.logger.debug(f"Waiting {delay:.2f} seconds before next attempt...")
                time.sleep(delay)
        
        return result
    
    def close(self):
        self.session.close()

def create_requestor() -> Requestor:
    return Requestor()