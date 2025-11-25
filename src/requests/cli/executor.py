"""
HTTP request executor for rhttp CLI tool.
"""

import json
import time
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError


class RequestExecutor:
    """Handles HTTP request execution with retry logic and error handling."""
    
    def __init__(self, timeout: float = 30.0, retries: int = 0, retry_backoff: float = 1.0):
        self.timeout = timeout
        self.retries = retries
        self.retry_backoff = retry_backoff
        self.session = requests.Session()
    
    def execute_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, Dict[str, str]]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        bearer_token: Optional[str] = None,
    ) -> requests.Response:
        """Execute an HTTP request with retry logic."""
        
        # Prepare request parameters
        request_params = self._prepare_request_params(
            url, method, headers, data, json_data, file_path, auth, bearer_token
        )
        
        # Execute request with retries
        last_exception = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(**request_params)
                return response
            except (Timeout, ConnectionError, HTTPError) as e:
                last_exception = e
                if attempt < self.retries:
                    backoff_time = self.retry_backoff * (2 ** attempt)
                    time.sleep(backoff_time)
                else:
                    raise RequestExecutorException(f"Request failed after {self.retries + 1} attempts: {str(e)}") from e
            except RequestException as e:
                raise RequestExecutorException(f"Request failed: {str(e)}") from e
        
        raise RequestExecutorException(f"Request failed after {self.retries + 1} attempts: {str(last_exception)}")
    
    def _prepare_request_params(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]],
        data: Optional[Union[str, Dict[str, str]]],
        json_data: Optional[Dict[str, Any]],
        file_path: Optional[str],
        auth: Optional[Tuple[str, str]],
        bearer_token: Optional[str],
    ) -> Dict[str, Any]:
        """Prepare request parameters."""
        params = {
            "method": method.upper(),
            "url": url,
            "timeout": self.timeout,
        }
        
        # Add headers
        if headers:
            params["headers"] = headers
        
        # Add authentication
        if auth:
            username, password = auth
            params["auth"] = HTTPBasicAuth(username, password)
        elif bearer_token:
            if "headers" not in params:
                params["headers"] = {}
            params["headers"]["Authorization"] = f"Bearer {bearer_token}"
        
        # Add data
        if json_data:
            params["json"] = json_data
        elif data:
            if isinstance(data, dict):
                params["data"] = data
            else:
                params["data"] = data
        elif file_path:
            try:
                with open(file_path, "rb") as f:
                    params["files"] = {"file": f}
            except IOError as e:
                raise RequestExecutorException(f"Failed to read file {file_path}: {str(e)}") from e
        
        return params


class RequestExecutorException(Exception):
    """Exception raised when request execution fails."""
    pass


def create_executor(timeout: float = 30.0, retries: int = 0, retry_backoff: float = 1.0) -> RequestExecutor:
    """Create a request executor instance."""
    return RequestExecutor(timeout=timeout, retries=retries, retry_backoff=retry_backoff)


def parse_auth(auth_string: str) -> Tuple[str, str]:
    """Parse authentication string in format 'user:pass'."""
    if ":" not in auth_string:
        raise ValueError("Authentication must be in format 'user:pass'")
    username, password = auth_string.split(":", 1)
    return username.strip(), password.strip()


def is_success_status_code(status_code: int) -> bool:
    """Check if status code indicates success (2xx)."""
    return 200 <= status_code < 300


def get_status_code_category(status_code: int) -> str:
    """Get the category of HTTP status code."""
    if 100 <= status_code < 200:
        return "Informational"
    elif 200 <= status_code < 300:
        return "Success"
    elif 300 <= status_code < 400:
        return "Redirection"
    elif 400 <= status_code < 500:
        return "Client Error"
    elif 500 <= status_code < 600:
        return "Server Error"
    else:
        return "Unknown"