"""
Metrics module for Requests library.
Provides functionality to track HTTP request metrics.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from .adapters import HTTPAdapter
from .models import PreparedRequest, Response


class Stats:
    """
    Thread-safe statistics tracker for HTTP requests.
    
    Tracks:
    - Total requests
    - Status code distribution
    - Total errors
    - Request latencies
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests = 0
        self._status_distribution: Dict[int, int] = defaultdict(int)
        self._total_errors = 0
        self._latencies: List[float] = []
    
    def record(self, status_code: int, latency: float) -> None:
        """
        Record a request with its status code and latency.
        
        Args:
            status_code: HTTP status code
            latency: Request duration in seconds
        """
        with self._lock:
            self._total_requests += 1
            self._status_distribution[status_code] += 1
            self._latencies.append(latency)
            
            if status_code >= 400:
                self._total_errors += 1
    
    def summary(self) -> Dict[str, float]:
        """
        Generate a summary of collected statistics.
        
        Returns:
            Dictionary with statistical summary
        """
        with self._lock:
            if not self._latencies:
                return {
                    'total_requests': 0,
                    'total_errors': 0,
                    'status_distribution': {},
                    'avg_latency': 0.0,
                    'min_latency': 0.0,
                    'max_latency': 0.0,
                    'p50_latency': 0.0,
                    'p95_latency': 0.0,
                    'p99_latency': 0.0
                }
                
            sorted_latencies = sorted(self._latencies)
            count = len(sorted_latencies)
            
            return {
                'total_requests': self._total_requests,
                'total_errors': self._total_errors,
                'status_distribution': dict(self._status_distribution),
                'avg_latency': sum(sorted_latencies) / count,
                'min_latency': sorted_latencies[0],
                'max_latency': sorted_latencies[-1],
                'p50_latency': sorted_latencies[int(count * 0.5)] if count > 0 else 0.0,
                'p95_latency': sorted_latencies[int(count * 0.95)] if count > 0 else 0.0,
                'p99_latency': sorted_latencies[int(count * 0.99)] if count > 0 else 0.0
            }
    
    def reset(self) -> None:
        """
        Reset all statistics to initial state.
        """
        with self._lock:
            self._total_requests = 0
            self._status_distribution.clear()
            self._total_errors = 0
            self._latencies.clear()
    
    @property
    def total_requests(self) -> int:
        """Get total number of requests."""
        with self._lock:
            return self._total_requests
    
    @property
    def total_errors(self) -> int:
        """Get total number of error requests (status >= 400)."""
        with self._lock:
            return self._total_errors
    
    @property
    def status_distribution(self) -> Dict[int, int]:
        """Get status code distribution."""
        with self._lock:
            return dict(self._status_distribution)
    
    @property
    def latencies(self) -> List[float]:
        """Get list of all request latencies."""
        with self._lock:
            return list(self._latencies)


class MetricsAdapter(HTTPAdapter):
    """
    HTTP adapter that wraps an existing HTTPAdapter and tracks metrics.
    
    Args:
        adapter: The underlying HTTPAdapter to wrap
        stats: Optional Stats object to use for tracking metrics
    """
    def __init__(self, adapter: HTTPAdapter, stats: Optional[Stats] = None):
        self._adapter = adapter
        self._stats = stats or Stats()
        
        # Initialize superclass with default values
        super().__init__(
            pool_connections=getattr(adapter, '_pool_connections', 10),
            pool_maxsize=getattr(adapter, '_pool_maxsize', 10),
            max_retries=getattr(adapter, 'max_retries', 0),
            pool_block=getattr(adapter, '_pool_block', False)
        )
    
    def send(
        self, 
        request: PreparedRequest, 
        stream: bool = False, 
        timeout: Optional[float] = None, 
        verify: bool = True, 
        cert: Optional[Tuple[str, str]] = None, 
        proxies: Optional[Dict[str, str]] = None
    ) -> Response:
        """
        Send request and track metrics.
        """
        start_time = time.time()
        
        try:
            response = self._adapter.send(request, stream, timeout, verify, cert, proxies)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            latency = time.time() - start_time
            self._stats.record(status_code, latency)
        
        return response
    
    def close(self) -> None:
        """Close the underlying adapter."""
        self._adapter.close()
    
    def init_poolmanager(self, *args, **kwargs) -> None:
        """Delegate to underlying adapter's pool manager."""
        self._adapter.init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, *args, **kwargs) -> None:
        """Delegate to underlying adapter's proxy manager."""
        return self._adapter.proxy_manager_for(*args, **kwargs)
    
    @property
    def stats(self) -> Stats:
        """Get the statistics object."""
        return self._stats
