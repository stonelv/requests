#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for thread safety of Stats class."""

import pytest
import threading
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.requests.metrics import Stats


def test_thread_safety():
    """Test that Stats is thread-safe."""
    stats = Stats()
    num_threads = 10
    num_requests_per_thread = 100

    def record_requests():
        for i in range(num_requests_per_thread):
            status_code = 200 if i % 2 == 0 else 404
            latency = 0.1 + (i * 0.001)
            stats.record(status_code, latency)

    # Create and start threads
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=record_requests)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify total requests
    assert stats.total_requests == num_threads * num_requests_per_thread

    # Verify status distribution
    assert stats.status_distribution[200] == (num_threads * num_requests_per_thread) // 2
    assert stats.status_distribution[404] == (num_threads * num_requests_per_thread) // 2

    # Verify error count
    assert stats.total_errors == (num_threads * num_requests_per_thread) // 2

    # Verify latencies count
    assert len(stats.latencies) == num_threads * num_requests_per_thread
