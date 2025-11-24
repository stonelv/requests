"""
Timing HTTP Adapter that wraps the standard HTTPAdapter to collect timing information.
"""

import time
from typing import Optional, Callable, Any
from urllib3.response import HTTPResponse

from ..adapters import HTTPAdapter
from .record import RequestRecord


class TimingAdapter(HTTPAdapter):
    """
    An HTTP adapter that wraps the standard HTTPAdapter to collect timing information
    for each request.
    
    This adapter intercepts the send method to measure:
    - Request start time
    - Time to first byte (TTFB)
    - Total request duration
    - Response status code
    - Response content length
    
    The timing information is stored in a callback function that can be used to
    collect and analyze request performance.
    """
    
    def __init__(self, record_callback: Optional[Callable[[RequestRecord], None]] = None, *args, **kwargs):
        """
        Initialize the TimingAdapter.
        
        Args:
            record_callback: Optional callback function to handle timing records
            *args, **kwargs: Arguments passed to the parent HTTPAdapter
        """
        super().__init__(*args, **kwargs)
        self.record_callback = record_callback
    
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """
        Send a request and collect timing information.
        
        Args:
            request: The prepared request object
            stream: Whether to stream the response
            timeout: Request timeout
            verify: SSL verification
            cert: Client certificate
            proxies: Proxy configuration
            
        Returns:
            Response object with timing information
        """
        # Create a new request record
        record = RequestRecord(
            url=request.url,
            method=request.method
        )
        
        try:
            # Call the parent send method to make the actual request
            response = super().send(
                request, stream=stream, timeout=timeout, 
                verify=verify, cert=cert, proxies=proxies
            )
            
            # Mark first byte received when we get the response
            record.mark_first_byte()
            
            # Extract response information
            status_code = response.status_code
            content_length = len(response.content) if hasattr(response, 'content') else 0
            
            # Mark request as complete
            record.mark_complete(
                status_code=status_code,
                content_length=content_length
            )
            
            # Store timing information in the response object for easy access
            response._timing_record = record
            
            # Call the callback with the successful record
            if self.record_callback:
                self.record_callback(record)
            
            return response
            
        except Exception as e:
            # Mark request as failed
            record.mark_complete(error=str(e))
            
            # Call the callback with the failed record
            if self.record_callback:
                self.record_callback(record)
            
            # Re-raise the exception to maintain normal error handling
            raise
    
    def close(self):
        """Close the adapter and clean up resources."""
        super().close()