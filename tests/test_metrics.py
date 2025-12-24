"""
Tests for metrics module.
"""

import pytest
import threading
import time

from requests.metrics import Stats, MetricsAdapter
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from requests import Response


class MockAdapter(HTTPAdapter):
    """Mock HTTP adapter for testing."""
    def __init__(self, status_code=200, delay=0.0):
        super().__init__()
        self.status_code = status_code
        self.delay = delay
    
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        time.sleep(self.delay)
        response = Response()
        response.status_code = self.status_code
        response.url = request.url
        return response


def test_basic_counting():
    """Test basic counting functionality."""
    stats = Stats()
    
    # Record some requests
    stats.record(200, 0.1)
    stats.record(200, 0.2)
    stats.record(404, 0.15)
    
    assert stats.total_requests == 3
    assert stats.total_errors == 1
    assert stats.status_distribution == {200: 2, 404: 1}
    assert len(stats.latencies) == 3


def test_status_distribution():
    """Test status code distribution."""
    stats = Stats()
    
    # Record various status codes
    stats.record(200, 0.1)
    stats.record(201, 0.2)
    stats.record(301, 0.15)
    stats.record(400, 0.25)
    stats.record(500, 0.3)
    
    assert stats.status_distribution == {
        200: 1,
        201: 1,
        301: 1,
        400: 1,
        500: 1
    }
    assert stats.total_errors == 2  # 400 and 500


def test_error_counting():
    """Test error counting (status >= 400)."""
    stats = Stats()
    
    # Record successful and error requests
    stats.record(200, 0.1)
    stats.record(301, 0.2)
    stats.record(400, 0.15)
    stats.record(404, 0.25)
    stats.record(500, 0.3)
    
    assert stats.total_errors == 3  # 400, 404, 500
    assert stats.total_requests == 5


def test_thread_safety():
    """Test thread safety of Stats class."""
    stats = Stats()
    
    def record_request():
        for i in range(100):
            status_code = 200 if i % 2 == 0 else 404
            stats.record(status_code, 0.001)
    
    # Create 10 threads
    threads = [threading.Thread(target=record_request) for _ in range(10)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    # Verify totals
    assert stats.total_requests == 1000
    assert stats.total_errors == 500
    assert stats.status_distribution == {200: 500, 404: 500}


def test_reset():
    """Test reset functionality."""
    stats = Stats()
    
    # Record some requests
    stats.record(200, 0.1)
    stats.record(404, 0.15)
    stats.record(500, 0.2)
    
    # Verify initial state
    assert stats.total_requests == 3
    assert stats.total_errors == 2
    assert len(stats.latencies) == 3
    
    # Reset
    stats.reset()
    
    # Verify reset state
    assert stats.total_requests == 0
    assert stats.total_errors == 0
    assert stats.status_distribution == {}
    assert len(stats.latencies) == 0


def test_metrics_adapter_basic():
    """Test MetricsAdapter basic functionality."""
    # Create mock adapter
    mock_adapter = MockAdapter(status_code=200, delay=0.01)
    
    # Create metrics adapter
    metrics_adapter = MetricsAdapter(mock_adapter)
    
    # Create prepared request
    request = PreparedRequest()
    request.method = 'GET'
    request.url = 'http://example.com'
    
    # Send request
    response = metrics_adapter.send(request)
    
    # Verify response
    assert response.status_code == 200
    
    # Verify metrics
    assert metrics_adapter.stats.total_requests == 1
    assert metrics_adapter.stats.total_errors == 0
    assert metrics_adapter.stats.status_distribution == {200: 1}
    assert len(metrics_adapter.stats.latencies) == 1
    assert metrics_adapter.stats.latencies[0] >= 0.01  # At least the delay


def test_metrics_adapter_error():
    """Test MetricsAdapter with error responses."""
    # Create mock adapter with 500 status
    mock_adapter = MockAdapter(status_code=500, delay=0.01)
    
    # Create metrics adapter
    metrics_adapter = MetricsAdapter(mock_adapter)
    
    # Create prepared request
    request = PreparedRequest()
    request.method = 'GET'
    request.url = 'http://example.com'
    
    # Send request
    response = metrics_adapter.send(request)
    
    # Verify response
    assert response.status_code == 500
    
    # Verify metrics
    assert metrics_adapter.stats.total_requests == 1
    assert metrics_adapter.stats.total_errors == 1
    assert metrics_adapter.stats.status_distribution == {500: 1}
