import time
import threading
from collections import defaultdict
from requests.adapters import HTTPAdapter
from requests.models import Response


class Stats:
    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._status_counts = defaultdict(int)
        self._latencies = []

    def record(self, status_code: int, latency: float):
        with self._lock:
            self._total_requests += 1
            self._status_counts[status_code] += 1
            self._latencies.append(latency)
            if 400 <= status_code < 600:
                self._total_errors += 1

    def get_total_requests(self) -> int:
        with self._lock:
            return self._total_requests

    def get_total_errors(self) -> int:
        with self._lock:
            return self._total_errors

    def get_status_distribution(self) -> dict:
        with self._lock:
            return dict(self._status_counts)

    def get_latencies(self) -> list:
        with self._lock:
            return list(self._latencies)

    def get_summary(self) -> dict:
        with self._lock:
            if not self._latencies:
                return {
                    "total_requests": 0,
                    "total_errors": 0,
                    "status_distribution": {},
                    "avg_latency": 0,
                    "min_latency": 0,
                    "max_latency": 0
                }
            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "status_distribution": dict(self._status_counts),
                "avg_latency": sum(self._latencies) / len(self._latencies),
                "min_latency": min(self._latencies),
                "max_latency": max(self._latencies)
            }

    def reset(self):
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._status_counts.clear()
            self._latencies = []


class MetricsAdapter(HTTPAdapter):
    def __init__(self, stats: Stats, adapter: HTTPAdapter = None):
        # Initialize the underlying adapter first
        self._stats = stats
        self._adapter = adapter or HTTPAdapter()
        # Call super() to initialize the parent class
        super().__init__()

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        start_time = time.time()
        try:
            response = self._adapter.send(request, stream, timeout, verify, cert, proxies)
        except Exception as e:
            # Handle exceptions as errors
            self._stats.record(500, time.time() - start_time)
            raise
        finally:
            latency = time.time() - start_time
            if 'response' in locals():
                self._stats.record(response.status_code, latency)
        return response

    def init_poolmanager(self, *args, **kwargs) -> None:
        """Delegate to underlying adapter's pool manager."""
        if hasattr(self, '_adapter'):
            self._adapter.init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs) -> None:
        """Delegate to underlying adapter's proxy manager."""
        if hasattr(self, '_adapter'):
            self._adapter.proxy_manager_for(*args, **kwargs)
