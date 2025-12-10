import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from .adapters import HTTPAdapter
from .models import Response
from .hooks import default_hooks


class Stats:
    """
    线程安全的统计类，用于记录 HTTP 请求的指标信息
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # 总请求数
        self._total_requests = 0
        
        # 总错误数（状态码 >= 400）
        self._total_errors = 0
        
        # 状态码分布
        self._status_codes: Dict[int, int] = defaultdict(int)
        
        # 耗时列表（毫秒）
        self._response_times: List[float] = []
        
        # 请求开始时间
        self._start_time = time.time()

    def record(self, status_code: int, response_time_ms: float) -> None:
        """
        记录单个请求的指标
        :param status_code: HTTP 状态码
        :param response_time_ms: 请求耗时（毫秒）
        """
        with self._lock:
            self._total_requests += 1
            self._status_codes[status_code] += 1
            self._response_times.append(response_time_ms)
            
            if status_code >= 400:
                self._total_errors += 1

    def get_total_requests(self) -> int:
        """获取总请求数"""
        with self._lock:
            return self._total_requests

    def get_total_errors(self) -> int:
        """获取总错误数"""
        with self._lock:
            return self._total_errors

    def get_status_distribution(self) -> Dict[int, int]:
        """获取状态码分布"""
        with self._lock:
            return dict(self._status_codes)

    def get_response_times(self) -> List[float]:
        """获取所有请求耗时列表"""
        with self._lock:
            return list(self._response_times)

    def get_error_rate(self) -> float:
        """获取错误率"""
        with self._lock:
            if self._total_requests == 0:
                return 0.0
            return self._total_errors / self._total_requests * 100

    def get_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要信息
        :return: 包含完整统计信息的字典
        """
        with self._lock:
            times = self._response_times.copy()
            total = self._total_requests
            
            summary = {
                "total_requests": total,
                "total_errors": self._total_errors,
                "error_rate": f"{self.get_error_rate():.2f}%",
                "uptime_seconds": time.time() - self._start_time,
                "status_distribution": dict(self._status_codes),
                "response_time": {}
            }
            
            if times:
                summary["response_time"].update({
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "avg_ms": sum(times) / len(times),
                    "p50_ms": self._calculate_percentile(times, 50),
                    "p95_ms": self._calculate_percentile(times, 95),
                    "p99_ms": self._calculate_percentile(times, 99),
                    "count": len(times)
                })
            else:
                summary["response_time"] = {
                    "min_ms": 0,
                    "max_ms": 0,
                    "avg_ms": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "count": 0
                }
            
            return summary

    def print_summary(self) -> None:
        """打印格式化的统计摘要"""
        summary = self.get_summary()
        
        print("=" * 60)
        print("Requests Metrics Summary")
        print("=" * 60)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Error Rate: {summary['error_rate']}")
        print(f"Uptime: {summary['uptime_seconds']:.2f}s")
        print("\nStatus Code Distribution:")
        for status_code, count in sorted(summary['status_distribution'].items()):
            print(f"  {status_code}: {count} requests")
        print("\nResponse Time Statistics (ms):")
        rt = summary['response_time']
        print(f"  Min: {rt['min_ms']:.2f}")
        print(f"  Max: {rt['max_ms']:.2f}")
        print(f"  Avg: {rt['avg_ms']:.2f}")
        print(f"  P50: {rt['p50_ms']:.2f}")
        print(f"  P95: {rt['p95_ms']:.2f}")
        print(f"  P99: {rt['p99_ms']:.2f}")
        print(f"  Samples: {rt['count']}")
        print("=" * 60)

    def reset(self) -> None:
        """重置所有统计数据"""
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._status_codes.clear()
            self._response_times.clear()
            self._start_time = time.time()

    @staticmethod
    def _calculate_percentile(values: List[float], percentile: int) -> float:
        """
        计算指定百分位数
        :param values: 数值列表
        :param percentile: 百分位数（0-100）
        :return: 计算结果
        """
        if not values:
            return 0.0
        
        sorted_vals = sorted(values)
        index = int(percentile / 100 * (len(sorted_vals) - 1))
        return sorted_vals[index]


class MetricsAdapter(HTTPAdapter):
    """
    带有指标统计功能的 HTTP Adapter
    不改变原有 HTTPAdapter 的行为，仅在请求发送前后记录指标
    """
    def __init__(self, stats: Stats, **kwargs):
        """
        :param stats: Stats 实例，用于记录指标
        :param kwargs: 传递给父类 HTTPAdapter 的参数
        """
        super().__init__(**kwargs)
        self.stats = stats

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None) -> Response:
        """
        重写 send 方法，记录请求耗时和状态码
        """
        start_time = time.time()
        
        try:
            response = super().send(request, stream, timeout, verify, cert, proxies)
            status_code = response.status_code
        except Exception as e:
            # 处理请求异常，将状态码记为 0
            status_code = 0
            raise
        finally:
            # 计算耗时（毫秒）
            response_time_ms = (time.time() - start_time) * 1000
            self.stats.record(status_code, response_time_ms)
        
        return response
