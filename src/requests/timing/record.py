"""
Request timing record data structure.
"""

import time
from typing import Optional


class RequestRecord:
    """
    A record of a single HTTP request's timing information.
    
    Attributes:
        url: The request URL
        method: HTTP method (GET, POST, etc.)
        start_time: Unix timestamp when request started
        duration_ms: Total request duration in milliseconds
        ttfb_ms: Time to first byte in milliseconds
        status_code: HTTP response status code
        content_length: Length of response content in bytes
        error: Optional error message if request failed
    """
    
    def __init__(self, url: str, method: str):
        """Initialize a new request record."""
        self.url = url
        self.method = method.upper()
        self.start_time = time.time()
        self.duration_ms = 0.0
        self.ttfb_ms = 0.0
        self.status_code = None
        self.content_length = 0
        self.error = None
        self._first_byte_time = None
    
    def mark_first_byte(self):
        """Mark the time when the first byte was received."""
        self._first_byte_time = time.time()
        if self.start_time:
            self.ttfb_ms = (self._first_byte_time - self.start_time) * 1000
    
    def mark_complete(self, status_code: Optional[int] = None, content_length: int = 0, error: Optional[str] = None):
        """
        Mark the request as complete and calculate duration.
        
        Args:
            status_code: HTTP response status code
            content_length: Length of response content
            error: Optional error message
        """
        end_time = time.time()
        self.duration_ms = (end_time - self.start_time) * 1000
        self.status_code = status_code
        self.content_length = content_length
        self.error = error
        
        # If first byte time wasn't recorded, use completion time
        if self._first_byte_time is None:
            self._first_byte_time = end_time
            self.ttfb_ms = self.duration_ms
    
    def to_dict(self) -> dict:
        """Convert the record to a dictionary."""
        return {
            'url': self.url,
            'method': self.method,
            'start_time': self.start_time,
            'duration_ms': self.duration_ms,
            'ttfb_ms': self.ttfb_ms,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'error': self.error
        }
    
    def to_csv_row(self) -> list:
        """Convert the record to a CSV row format."""
        return [
            self.start_time,
            self.method,
            self.url,
            self.status_code or '',
            f"{self.duration_ms:.2f}",
            f"{self.ttfb_ms:.2f}",
            self.content_length,
            self.error or ''
        ]
    
    def __repr__(self):
        return (f"RequestRecord(url='{self.url}', method='{self.method}', "
                f"status_code={self.status_code}, duration_ms={self.duration_ms:.2f}, "
                f"ttfb_ms={self.ttfb_ms:.2f})")
    
    def __str__(self):
        if self.error:
            return f"{self.method} {self.url} - ERROR: {self.error} ({self.duration_ms:.2f}ms)"
        else:
            return f"{self.method} {self.url} - {self.status_code} ({self.duration_ms:.2f}ms, TTFB: {self.ttfb_ms:.2f}ms)"