"""
Requests Timing Extension - A lightweight profiling extension for HTTP requests.

This extension provides timing capabilities for HTTP requests, including:
- Request duration measurement
- Time to first byte (TTFB) measurement
- Status code tracking
- Content length tracking
- Statistical analysis of requests
- CSV export functionality
"""

from .adapter import TimingAdapter
from .profiler import ProfilerSession, attach_profiler
from .record import RequestRecord

__all__ = ['TimingAdapter', 'ProfilerSession', 'attach_profiler', 'RequestRecord']