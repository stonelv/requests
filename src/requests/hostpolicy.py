"""
Host Policy Module for Requests

This module provides host-level default headers and lightweight request statistics.
"""
import uuid
import threading
from collections import deque
from typing import Dict, Optional, Any, Deque
from datetime import timedelta


class HostStats:
    """Host statistics collector.
    
    Maintains a sliding window of recent request statistics for a host.
    """
    def __init__(self, window_size: int = 50):
        self._window_size = window_size
        self._records: Deque[Dict[str, Any]] = deque(maxlen=window_size)
        self._lock = threading.Lock()
    
    def add_record(self, elapsed_ms: float, status_code: Optional[int] = None):
        """Add a new request record.
        
        Args:
            elapsed_ms: Request duration in milliseconds
            status_code: HTTP status code (None if request failed before getting response)
        """
        # Determine status bucket
        if status_code is None:
            bucket = "error"
        elif 200 <= status_code < 300:
            bucket = "2xx"
        elif 400 <= status_code < 500:
            bucket = "4xx"
        elif 500 <= status_code < 600:
            bucket = "5xx"
        else:
            bucket = "other"
        
        with self._lock:
            self._records.append({
                "elapsed_ms": elapsed_ms,
                "bucket": bucket
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get the current statistics.
        
        Returns:
            Dict containing count, avg_ms, p95_ms, error_rate, and buckets
        """
        with self._lock:
            count = len(self._records)
            if count == 0:
                return {
                    "count": 0,
                    "avg_ms": 0.0,
                    "p95_ms": 0.0,
                    "error_rate": 0.0,
                    "buckets": {"2xx": 0, "4xx": 0, "5xx": 0, "error": 0, "other": 0}
                }
            
            # Calculate average
            total_ms = sum(record["elapsed_ms"] for record in self._records)
            avg_ms = total_ms / count
            
            # Calculate p95
            sorted_elapsed = sorted(record["elapsed_ms"] for record in self._records)
            p95_idx = int(count * 0.95) - 1 if count > 0 else 0
            p95_ms = sorted_elapsed[p95_idx]
            
            # Calculate error rate
            error_count = sum(1 for record in self._records if record["bucket"] == "error")
            error_rate = error_count / count
            
            # Calculate buckets
            buckets = {
                "2xx": 0,
                "4xx": 0,
                "5xx": 0,
                "error": 0,
                "other": 0
            }
            for record in self._records:
                buckets[record["bucket"]] += 1
            
            return {
                "count": count,
                "avg_ms": round(avg_ms, 2),
                "p95_ms": round(p95_ms, 2),
                "error_rate": round(error_rate, 4),
                "buckets": buckets
            }


class HostPolicy:
    """Host-specific policy configuration.
    
    Stores default headers and header merging rules for a host.
    """
    def __init__(self, headers: Dict[str, str] = None, override: bool = False, protected_headers: Optional[set] = None):
        self.headers = headers or {}
        self.override = override
        self.protected_headers = protected_headers or set()
    
    def merge_headers(self, request_headers: Dict[str, str]) -> Dict[str, str]:
        """Merge default headers with request headers based on policy.
        
        Args:
            request_headers: Headers from the request
            
        Returns:
            Merged headers
        """
        if not self.headers:
            return request_headers.copy()
        
        merged = request_headers.copy()
        
        for header, value in self.headers.items():
            if header in self.protected_headers:
                # Protected headers from request are not overridden
                continue
            if header not in merged or self.override:
                merged[header] = value
        
        return merged


class RequestIDInjector:
    """Request ID injector.
    
    Generates and injects UUID4 request IDs if not already present.
    """
    def __init__(self, header_name: str = "X-Request-ID"):
        self.header_name = header_name
    
    def inject(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject request ID into headers if not present.
        
        Args:
            headers: Request headers
            
        Returns:
            Headers with request ID
        """
        if self.header_name not in headers:
            headers[self.header_name] = str(uuid.uuid4())
        return headers


class HostPolicyManager:
    """Manager for host policies and statistics.
    
    Thread-safe manager that holds host-specific policies and statistics.
    """
    def __init__(self, enable_request_id: bool = False, window_size: int = 50):
        self._enable_request_id = enable_request_id
        self._window_size = window_size
        self._policies: Dict[str, HostPolicy] = {}
        self._stats: Dict[str, HostStats] = {}
        self._request_id_injector = RequestIDInjector()
        self._lock = threading.Lock()
    
    def configure_policy(self, host: str, headers: Dict[str, str] = None, override: bool = False, protected_headers: Optional[set] = None):
        """Configure a policy for a host.
        
        Args:
            host: Hostname to configure
            headers: Default headers for the host
            override: Whether to override existing request headers
            protected_headers: Headers that cannot be overridden
        """
        with self._lock:
            self._policies[host] = HostPolicy(headers, override, protected_headers)
    
    def get_policy(self, host: str) -> Optional[HostPolicy]:
        """Get the policy for a host.
        
        Args:
            host: Hostname to get policy for
            
        Returns:
            HostPolicy or None if no policy configured
        """
        with self._lock:
            return self._policies.get(host)
    
    def get_stats(self, host: str) -> Dict[str, Any]:
        """Get statistics for a host.
        
        Args:
            host: Hostname to get statistics for
            
        Returns:
            Statistics dictionary
        """
        with self._lock:
            stats = self._stats.get(host)
            if stats is None:
                return {
                    "count": 0,
                    "avg_ms": 0.0,
                    "p95_ms": 0.0,
                    "error_rate": 0.0,
                    "buckets": {"2xx": 0, "4xx": 0, "5xx": 0, "error": 0, "other": 0}
                }
        return stats.get_stats()
    
    def process_request(self, host: str, headers: Dict[str, str]) -> Dict[str, str]:
        """Process request headers for a host.
        
        Args:
            host: Hostname
            headers: Request headers
            
        Returns:
            Processed headers with default headers merged and request ID injected
        """
        processed_headers = headers.copy()
        
        # Apply host policy
        policy = self.get_policy(host)
        if policy:
            processed_headers = policy.merge_headers(processed_headers)
        
        # Inject request ID if enabled
        if self._enable_request_id:
            processed_headers = self._request_id_injector.inject(processed_headers)
        
        return processed_headers
    
    def record_response(self, host: str, elapsed_ms: float, status_code: Optional[int] = None):
        """Record a response for a host.
        
        Args:
            host: Hostname
            elapsed_ms: Request duration in milliseconds
            status_code: HTTP status code (None if request failed)
        """
        with self._lock:
            if host not in self._stats:
                self._stats[host] = HostStats(self._window_size)
        
        stats = self._stats[host]
        stats.add_record(elapsed_ms, status_code)