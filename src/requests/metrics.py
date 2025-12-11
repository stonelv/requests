import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
from requests.models import Response
from requests import Request


class Stats:
    """
    线程安全的统计类，记录请求的各种指标
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._status_codes: Dict[int, int] = defaultdict(int)
        self._latencies: List[float] = []
        self._start_time = time.time()

    def record(self, status_code: int, latency: float) -> None:
        """
        记录单个请求的统计信息
        """
        with self._lock:
            self._total_requests += 1
            self._status_codes[status_code] += 1
            self._latencies.append(latency)
            if status_code == 0 or status_code >= 400:
                self._total_errors += 1

    @property
    def total_requests(self) -> int:
        """总请求数"""
        with self._lock:
            return self._total_requests

    @property
    def total_errors(self) -> int:
        """总错误数（状态码 >= 400）"""
        with self._lock:
            return self._total_errors

    @property
    def status_distribution(self) -> Dict[int, int]:
        """状态码分布"""
        with self._lock:
            return dict(self._status_codes)

    @property
    def latencies(self) -> List[float]:
        """所有请求的耗时列表"""
        with self._lock:
            return self._latencies.copy()

    def summary(self) -> Dict[str, Any]:
        """
        生成统计摘要
        """
        with self._lock:
            latencies = self._latencies.copy()
            total = self._total_requests
            if not latencies:
                avg_latency = 0.0
                p50 = 0.0
                p95 = 0.0
                p99 = 0.0
            else:
                avg_latency = sum(latencies) / len(latencies)
                sorted_latencies = sorted(latencies)
                p50 = sorted_latencies[int(0.5 * len(sorted_latencies))]
                p95 = sorted_latencies[int(0.95 * len(sorted_latencies))]
                p99 = sorted_latencies[int(0.99 * len(sorted_latencies))]

            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "error_rate": self._total_errors / max(total, 1),
                "status_distribution": dict(self._status_codes),
                "avg_latency": avg_latency,
                "p50_latency": p50,
                "p95_latency": p95,
                "p99_latency": p99,
                "min_latency": min(latencies) if latencies else 0.0,
                "max_latency": max(latencies) if latencies else 0.0,
                "uptime": time.time() - self._start_time
            }

    def reset(self) -> None:
        """
        重置所有统计信息
        """
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._status_codes.clear()
            self._latencies.clear()
            self._start_time = time.time()


class MetricsAdapter(HTTPAdapter):
    """
    带有统计功能的 HTTP 适配器
    """
    def __init__(self, stats: Stats, *args: Any, **kwargs: Any) -> None:
        self._stats = stats
        super().__init__(*args, **kwargs)

    def send(self, request: Request, stream: bool = False, timeout: Optional[float] = None,
             verify: bool = True, cert: Optional[Tuple[str, str]] = None, proxies: Optional[Dict[str, str]] = None) -> Response:
        """
        发送请求并记录统计信息
        """
        start_time = time.time()
        try:
            response = super().send(request, stream, timeout, verify, cert, proxies)
        except Exception as e:
            # 记录错误请求，状态码用 0 表示
            latency = time.time() - start_time
            self._stats.record(0, latency)
            raise
        else:
            latency = time.time() - start_time
            self._stats.record(response.status_code, latency)
            return response