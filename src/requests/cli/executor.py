# -*- coding: utf-8 -*-
"""Request executor for rhttp tool."""
import time
import requests
from typing import Dict, Any, Optional, Tuple
from requests import Response
from requests.auth import HTTPBasicAuth


def execute_request(
    url: str,
    method: str = 'GET',
    headers: Dict[str, str] = None,
    data: Dict[str, Any] = None,
    json: Dict[str, Any] = None,
    files: Dict[str, Any] = None,
    auth: Tuple[str, str] = None,
    bearer: str = None,
    timeout: float = 30.0,
    retries: int = 0,
    retry_backoff: float = 1.0
) -> Tuple[Response, float, int]:
    """Execute an HTTP request with optional retries, returning (response, elapsed_time, attempts_used)."""
    session = requests.Session()
    # Initialize headers to empty dict if None to avoid KeyError when adding auth/bearer token
    headers = headers or {}
    if auth:
        session.auth = HTTPBasicAuth(*auth)
    
    # Configure bearer token with Authorization header conflict check
    if bearer:
        if 'Authorization' in headers:
            print(f"Warning: Overwriting existing Authorization header with Bearer token")
        headers['Authorization'] = f'Bearer {bearer}'
    
    response = None
    start_time = time.time()
    attempts_used = 0
    
    for attempt in range(retries + 1):
        attempts_used += 1
        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json,
                files=files,
                timeout=timeout
            )
            
            # If successful, break the loop
            break
        except requests.RequestException as e:
            # If last attempt, raise the exception
            if attempt == retries:
                raise
            
            # Calculate exponential backoff
            backoff = retry_backoff * (2 ** attempt)
            time.sleep(backoff)
    
    elapsed_time = time.time() - start_time
    return response, elapsed_time, attempts_used


def prepare_request(
    url: str,
    method: str = 'GET',
    headers: Dict[str, str] = None,
    data: str = None,
    json: str = None,
    file_path: str = None,
    file_field: str = 'file',
    auth: str = None,
    bearer: str = None
) -> Dict[str, Any]:
    """Prepare request parameters from command-line arguments."""
    request_params = {
        'url': url,
        'method': method,
        'headers': headers or {}
    }
    
    # Parse form data
    if data:
        request_params['data'] = {k: v for k, v in [pair.split('=') for pair in data.split('&')]}
    
    # Parse JSON data
    if json:
        import json as json_module
        request_params['json'] = json_module.loads(json)
    
    # Prepare files for upload
    if file_path:
        request_params['files'] = {file_field: open(file_path, 'rb')}
    
    # Parse authentication
    if auth:
        request_params['auth'] = tuple(auth.split(':', 1)) if ':' in auth else (auth, '')
    
    # Bearer token
    if bearer:
        request_params['bearer'] = bearer
    
    return request_params
