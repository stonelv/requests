#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Metrics module for requests library.

This module provides a MetricsAdapter that wraps around an HTTPAdapter
and records various metrics for requests made through it, as well as a
thread-safe Stats class to store and retrieve these metrics.
"""

__all__ = ['MetricsAdapter', 'Stats', 'add_metrics']

import time
import threading
from typing import Dict, List, Optional, Tuple
from requests.adapters import HTTPAdapter
from requests.models import Response
from requests.sessions import Session


class Stats:
    """A thread-safe statistics class to record and retrieve request metrics.

    This class tracks:
    - Total number of requests
    - Total number of errors
    - Status code distribution
    - Request latencies
    - Request timestamps
    """

    def __init__(self) -> None:
        """Initialize an empty Stats instance."""
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._status_distribution: Dict[int, int] = {}
        self._latencies: List[float] = []
        self._timestamps: List[float] = []
        self._lock: threading.RLock = threading.RLock()

    def record(self, status_code: int, latency: float, timestamp: Optional[float] = None) -> None:
        """Record a request's metrics.

        Args:
            status_code: The HTTP status code of the response. Status code 0 indicates a failed/exception request.
            latency: The time taken to complete the request in seconds.
            timestamp: The timestamp of the request (defaults to current time if not provided).
        """
        with self._lock:
            # Update total requests
            self._total_requests += 1

            # Update status code distribution
            if status_code in self._status_distribution:
                self._status_distribution[status_code] += 1
            else:
                self._status_distribution[status_code] = 1

            # Update error count if status code is 0 (failed request) or 4xx/5xx
            if status_code == 0 or (400 <= status_code < 600):
                self._total_errors += 1

            # Record latency and timestamp
            self._latencies.append(latency)
            self._timestamps.append(timestamp or time.time())

    @property
    def total_requests(self) -> int:
        """Get the total number of requests recorded."""
        with self._lock:
            return self._total_requests

    @property
    def total_errors(self) -> int:
        """Get the total number of requests that resulted in errors (4xx or 5xx)."""
        with self._lock:
            return self._total_errors

    @property
    def status_distribution(self) -> Dict[int, int]:
        """Get the distribution of status codes."""
        with self._lock:
            return self._status_distribution.copy()

    @property
    def latencies(self) -> List[float]:
        """Get the list of request latencies in seconds."""
        with self._lock:
            return self._latencies.copy()

    @property
    def timestamps(self) -> List[float]:
        """Get the list of request timestamps."""
        with self._lock:
            return self._timestamps.copy()

    def summary(self) -> Dict[str, float]:
        """Generate a summary of the recorded metrics.

        Returns:
            A dictionary containing summary statistics:
            - total_requests: Total number of requests
            - total_errors: Total number of errors
            - error_rate: Percentage of requests that resulted in errors
            - avg_latency: Average latency in seconds
            - min_latency: Minimum latency in seconds
            - max_latency: Maximum latency in seconds
            - p50_latency: 50th percentile latency in seconds
            - p95_latency: 95th percentile latency in seconds
            - p99_latency: 99th percentile latency in seconds
        """
        with self._lock:
            if not self._total_requests:
                return {
                    'total_requests': 0,
                    'total_errors': 0,
                    'error_rate': 0.0,
                    'avg_latency': 0.0,
                    'min_latency': 0.0,
                    'max_latency': 0.0,
                    'p50_latency': 0.0,
                    'p95_latency': 0.0,
                    'p99_latency': 0.0
                }

            # Calculate error rate
            error_rate = (self._total_errors / self._total_requests) * 100

            # Calculate latency statistics
            sorted_latencies = sorted(self._latencies)
            avg_latency = sum(sorted_latencies) / len(sorted_latencies)
            min_latency = sorted_latencies[0]
            max_latency = sorted_latencies[-1]

            # Calculate percentiles
            n = len(sorted_latencies)
            # Calculate p50 (median)
            if n % 2 == 0:
                p50 = (sorted_latencies[n//2 - 1] + sorted_latencies[n//2]) / 2
            else:
                p50 = sorted_latencies[n//2]
            # Calculate p95 and p99
            p95 = sorted_latencies[int(n * 0.95)]
            p99 = sorted_latencies[int(n * 0.99)]

            return {
                'total_requests': self._total_requests,
                'total_errors': self._total_errors,
                'error_rate': round(error_rate, 2),
                'avg_latency': round(avg_latency, 4),
                'min_latency': round(min_latency, 4),
                'max_latency': round(max_latency, 4),
                'p50_latency': round(p50, 4),
                'p95_latency': round(p95, 4),
                'p99_latency': round(p99, 4)
            }

    def reset(self) -> None:
        """Reset all recorded metrics."""
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._status_distribution = {}
            self._latencies = []
            self._timestamps = []


class MetricsAdapter(HTTPAdapter):
    """An HTTPAdapter that wraps another HTTPAdapter and records metrics.

    This adapter delegates all requests to the underlying HTTPAdapter
    but records metrics (status code, latency, etc.) before and after
    each request.
    """

    def __init__(self, adapter: HTTPAdapter, stats: Stats) -> None:
        """Initialize a MetricsAdapter instance.

        Args:
            adapter: The underlying HTTPAdapter to use for making requests.
            stats: The Stats instance to use for recording metrics.
        """
        super().__init__()
        self._adapter = adapter
        self._stats = stats

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None) -> Response:
        """Send a request using the underlying adapter and record metrics.

        Args:
            request: The PreparedRequest to send.
            stream: Whether to stream the response content.
            timeout: The timeout for the request.
            verify: Whether to verify the server's TLS certificate.
            cert: The client certificate to use for mutual TLS.
            proxies: The proxies to use for the request.

        Returns:
            The Response object from the underlying adapter.

        Note:
            If the request fails with an exception, it will be recorded with status code 0.
        """
        # Record start time
        start_time = time.time()

        try:
            # Delegate to the underlying adapter
            response = self._adapter.send(
                request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies
            )

            # Calculate latency
            latency = time.time() - start_time

            # Record metrics
            self._stats.record(response.status_code, latency, start_time)

            return response

        except Exception as e:
            # Calculate latency for failed requests
            latency = time.time() - start_time

            # Record metrics for failed requests (use 0 as status code)
            self._stats.record(0, latency, start_time)

            # Re-raise the exception
            raise


def add_metrics(session: Session, adapter: Optional[HTTPAdapter] = None) -> Stats:
    """Add metrics tracking to a requests Session.

    This function creates a Stats instance and a MetricsAdapter that
    wraps around the default HTTPAdapter (or a provided adapter) and
    mounts it to the session.

    Args:
        session: The requests Session to add metrics to.
        adapter: The HTTPAdapter to wrap (defaults to HTTPAdapter() if not provided).

    Returns:
        The Stats instance used for recording metrics.
    """
    # Create stats instance
    stats = Stats()

    # Use provided adapter or create a new one
    underlying_adapter = adapter or HTTPAdapter()

    # Create metrics adapter
    metrics_adapter = MetricsAdapter(underlying_adapter, stats)

    # Mount the metrics adapter to the session
    session.mount('http://', metrics_adapter)
    session.mount('https://', metrics_adapter)
    
    return stats