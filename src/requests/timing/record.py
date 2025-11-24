from datetime import datetime
from dataclasses import dataclass

@dataclass
class TimingRecord:
    """
    Data class to hold timing information for a single request.
    
    Attributes:
        start_time (datetime): The start time of the request
        duration_ms (float): Total duration of the request in milliseconds
        ttfb_ms (float): Time to first byte in milliseconds
        status_code (int): HTTP status code of the response
        content_length (int): Length of the response content in bytes
        url (str): The URL of the request
    """
    start_time: datetime
    duration_ms: float
    ttfb_ms: float
    status_code: int
    content_length: int
    url: str
    
    def to_dict(self) -> dict:
        """Convert the record to a dictionary for easy serialization."""
        return {
            'start_time': self.start_time.isoformat(),
            'duration_ms': round(self.duration_ms, 2),
            'ttfb_ms': round(self.ttfb_ms, 2),
            'status_code': self.status_code,
            'content_length': self.content_length,
            'url': self.url
        }
