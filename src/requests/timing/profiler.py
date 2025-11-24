"""
Profiler Session that extends the standard Session with automatic timing capabilities.
"""

import csv
import os
from collections import deque
from typing import Dict, List, Optional, Any

from ..sessions import Session
from .adapter import TimingAdapter
from .record import RequestRecord


class ProfilerSession(Session):
    """
    A Session subclass that automatically uses TimingAdapter for all HTTP requests
    and maintains a circular buffer of request timing records.
    
    Features:
    - Automatic timing of all HTTP requests
    - Circular buffer with configurable maximum size (default: 200)
    - Statistical analysis of request performance
    - CSV export functionality
    - Status code distribution analysis
    
    This session maintains all the functionality of the standard Session while
    adding transparent timing capabilities that don't affect the normal API usage.
    """
    
    def __init__(self, max_records: int = 200, *args, **kwargs):
        """
        Initialize the ProfilerSession.
        
        Args:
            max_records: Maximum number of timing records to keep in memory (default: 200)
            *args, **kwargs: Arguments passed to the parent Session
        """
        super().__init__(*args, **kwargs)
        self.max_records = max_records
        self._records_buffer = deque(maxlen=max_records)
        self._setup_timing_adapter()
    
    def _setup_timing_adapter(self):
        """Set up the timing adapter for all HTTP/HTTPS requests."""
        # Create a timing adapter with our record callback
        timing_adapter = TimingAdapter(record_callback=self._record_request)
        
        # Mount the timing adapter for both HTTP and HTTPS
        self.mount('http://', timing_adapter)
        self.mount('https://', timing_adapter)
    
    def _record_request(self, record: RequestRecord):
        """
        Callback function to store timing records.
        
        Args:
            record: The RequestRecord to store
        """
        self._records_buffer.append(record)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistical analysis of all recorded requests.
        
        Returns:
            Dictionary containing:
            - count: Total number of requests
            - avg_duration_ms: Average request duration in milliseconds
            - min_duration_ms: Minimum request duration
            - max_duration_ms: Maximum request duration
            - avg_ttfb_ms: Average time to first byte
            - min_ttfb_ms: Minimum time to first byte
            - max_ttfb_ms: Maximum time to first byte
            - status_code_distribution: Dictionary of status code counts
            - error_count: Number of failed requests
            - success_rate: Percentage of successful requests (2xx status codes)
        """
        if not self._records_buffer:
            return {
                'count': 0,
                'avg_duration_ms': 0,
                'min_duration_ms': 0,
                'max_duration_ms': 0,
                'avg_ttfb_ms': 0,
                'min_ttfb_ms': 0,
                'max_ttfb_ms': 0,
                'status_code_distribution': {},
                'error_count': 0,
                'success_rate': 0.0
            }
        
        # Calculate duration statistics
        durations = [r.duration_ms for r in self._records_buffer if r.error is None]
        ttfbs = [r.ttfb_ms for r in self._records_buffer if r.error is None]
        
        # Status code distribution
        status_dist = {}
        error_count = 0
        success_count = 0
        
        for record in self._records_buffer:
            if record.error:
                error_count += 1
            elif record.status_code:
                status_dist[record.status_code] = status_dist.get(record.status_code, 0) + 1
                if 200 <= record.status_code < 300:
                    success_count += 1
        
        total_requests = len(self._records_buffer)
        
        stats = {
            'count': total_requests,
            'error_count': error_count,
            'success_rate': (success_count / total_requests * 100) if total_requests > 0 else 0.0,
            'status_code_distribution': status_dist
        }
        
        # Add duration statistics if we have successful requests
        if durations:
            stats.update({
                'avg_duration_ms': sum(durations) / len(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'avg_ttfb_ms': sum(ttfbs) / len(ttfbs) if ttfbs else 0,
                'min_ttfb_ms': min(ttfbs) if ttfbs else 0,
                'max_ttfb_ms': max(ttfbs) if ttfbs else 0
            })
        else:
            stats.update({
                'avg_duration_ms': 0,
                'min_duration_ms': 0,
                'max_duration_ms': 0,
                'avg_ttfb_ms': 0,
                'min_ttfb_ms': 0,
                'max_ttfb_ms': 0
            })
        
        return stats
    
    def export_csv(self, path: str, include_errors: bool = True) -> bool:
        """
        Export timing records to a CSV file.
        
        Args:
            path: Path to the output CSV file
            include_errors: Whether to include failed requests in the export
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Filter records if needed
            records_to_export = self._records_buffer if include_errors else [
                r for r in self._records_buffer if r.error is None
            ]
            
            if not records_to_export:
                return False
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'timestamp', 'method', 'url', 'status_code', 
                    'duration_ms', 'ttfb_ms', 'content_length', 'error'
                ])
                
                # Write data rows
                for record in records_to_export:
                    writer.writerow(record.to_csv_row())
            
            return True
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    def get_records(self) -> List[RequestRecord]:
        """
        Get a copy of all timing records.
        
        Returns:
            List of RequestRecord objects
        """
        return list(self._records_buffer)
    
    def clear_records(self):
        """Clear all timing records."""
        self._records_buffer.clear()
    
    @property
    def record_count(self) -> int:
        """Get the number of timing records."""
        return len(self._records_buffer)
    
    def __len__(self):
        """Return the number of timing records."""
        return len(self._records_buffer)


def attach_profiler(session: Session, max_records: int = 200) -> ProfilerSession:
    """
    Attach timing capabilities to an existing Session.
    
    This function creates a new ProfilerSession that wraps the provided session,
    maintaining all its configuration while adding timing capabilities.
    
    Args:
        session: The existing Session to enhance with timing
        max_records: Maximum number of timing records to keep
        
    Returns:
        A new ProfilerSession with timing capabilities
        
    Example:
        >>> import requests
        >>> from requests.timing import attach_profiler
        >>> 
        >>> # Create a regular session
        >>> session = requests.Session()
        >>> session.headers.update({'User-Agent': 'MyApp/1.0'})
        >>> 
        >>> # Attach timing capabilities
        >>> profiler_session = attach_profiler(session)
        >>> 
        >>> # Use it like a normal session, but with timing
        >>> response = profiler_session.get('https://httpbin.org/get')
        >>> print(profiler_session.get_stats())
    """
    # Create a new ProfilerSession with the specified max_records
    profiler_session = ProfilerSession(max_records=max_records)
    
    # Copy all attributes from the original session
    for attr_name in dir(session):
        if attr_name.startswith('_'):
            continue
        try:
            attr_value = getattr(session, attr_name)
            if not callable(attr_value):
                setattr(profiler_session, attr_name, attr_value)
        except AttributeError:
            # Some attributes might not be accessible, skip them
            continue
    
    # Copy the adapters from the original session
    profiler_session.adapters.clear()
    for prefix, adapter in session.adapters.items():
        profiler_session.mount(prefix, adapter)
    
    # Set up timing adapter for the profiler session
    profiler_session._setup_timing_adapter()
    
    return profiler_session