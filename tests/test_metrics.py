#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Metrics module."""

import pytest
import threading
import time
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import requests
from requests.models import Response
from requests.adapters import HTTPAdapter
from src.requests.metrics import add_metrics, MetricsAdapter, Stats


class TestStats:
    """Test the Stats class functionality."""

    def test_basic_counting(self):
        """Test basic counting of requests and errors."""
        stats = Stats()

        # Record successful requests
        stats.record(200, 0.1)
        stats.record(201, 0.2)

        # Record error requests
        stats.record(400, 0.3)
        stats.record(500, 0.4)

        # Verify counts
        assert stats.total_requests == 4
        assert stats.total_errors == 2

        # Verify status distribution
        assert stats.status_distribution == {200: 1, 201: 1, 400: 1, 500: 1}

        # Verify latencies
        assert stats.latencies == [0.1, 0.2, 0.3, 0.4]

        # Verify summary
        summary = stats.summary()
        assert summary['total_requests'] == 4
        assert summary['total_errors'] == 2
        assert summary['error_rate'] == 50.0
        assert summary['avg_latency'] == 0.25
        assert summary['min_latency'] == 0.1
        assert summary['max_latency'] == 0.4
        assert summary['p50_latency'] == 0.25
        assert summary['p95_latency'] == 0.4
        assert summary['p99_latency'] == 0.4

    def test_status_distribution(self):
        """Test status code distribution tracking."""
        stats = Stats()

        # Record various status codes
        stats.record(200, 0.1)
        stats.record(200, 0.2)
        stats.record(201, 0.3)
        stats.record(404, 0.4)
        stats.record(404, 0.5)
        stats.record(404, 0.6)
        stats.record(500, 0.7)

        # Verify status distribution
        assert stats.status_distribution == {200: 2, 201: 1, 404: 3, 500: 1}

    def test_error_counting(self):
        """Test error counting (4xx and 5xx status codes)."""
        stats = Stats()

        # Record non-error status codes
        stats.record(100, 0.1)
        stats.record(200, 0.2)
        stats.record(300, 0.3)

        # Record error status codes
        stats.record(400, 0.4)
        stats.record(404, 0.5)
        stats.record(500, 0.6)
        stats.record(503, 0.7)

        # Verify error count
        assert stats.total_errors == 4

    def test_thread_safety(self):
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

    def test_reset(self):
        """Test that resetting clears all metrics."""
        stats = Stats()

        # Record some metrics
        stats.record(200, 0.1)
        stats.record(404, 0.2)
        stats.record(500, 0.3)

        # Verify metrics are present
        assert stats.total_requests == 3
        assert stats.total_errors == 2
        assert len(stats.status_distribution) == 3
        assert len(stats.latencies) == 3

        # Reset stats
        stats.reset()

        # Verify metrics are cleared
        assert stats.total_requests == 0
        assert stats.total_errors == 0
        assert stats.status_distribution == {}
        assert stats.latencies == []
        assert stats.timestamps == []

        # Verify summary after reset
        summary = stats.summary()
        assert summary['total_requests'] == 0
        assert summary['total_errors'] == 0
        assert summary['error_rate'] == 0.0
        assert summary['avg_latency'] == 0.0


class TestMetricsAdapter:
    """Test the MetricsAdapter functionality."""

    def test_send_records_metrics(self):
        """Test that MetricsAdapter records metrics when sending requests."""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200

        # Create mock adapter
        mock_adapter = Mock(spec=HTTPAdapter)
        mock_adapter.send.return_value = mock_response

        # Create stats and metrics adapter
        stats = Stats()
        metrics_adapter = MetricsAdapter(mock_adapter, stats)

        # Create mock request
        mock_request = Mock()

        # Send request
        response = metrics_adapter.send(mock_request)

        # Verify adapter was called
        mock_adapter.send.assert_called_once_with(
            mock_request, stream=False, timeout=None, verify=True, cert=None, proxies=None
        )

        # Verify response is returned
        assert response == mock_response

        # Verify metrics were recorded
        assert stats.total_requests == 1
        assert stats.status_distribution == {200: 1}
        assert stats.total_errors == 0
        assert len(stats.latencies) == 1
        assert len(stats.timestamps) == 1

    def test_send_records_errors(self):
        """Test that MetricsAdapter records metrics for failed requests."""
        # Create mock adapter that raises an exception
        mock_adapter = Mock(spec=HTTPAdapter)
        mock_adapter.send.side_effect = Exception("Request failed")

        # Create stats and metrics adapter
        stats = Stats()
        metrics_adapter = MetricsAdapter(mock_adapter, stats)

        # Create mock request
        mock_request = Mock()

        # Send request and expect exception
        with pytest.raises(Exception, match="Request failed"):
            metrics_adapter.send(mock_request)

        # Verify metrics were recorded for failed request
        assert stats.total_requests == 1
        assert stats.status_distribution == {0: 1}  # 0 indicates failed request
        assert stats.total_errors == 1
        assert len(stats.latencies) == 1
        assert len(stats.timestamps) == 1


class TestAddMetrics:
    """Test the add_metrics function."""

    def test_add_metrics(self):
        """Test that add_metrics correctly adds metrics to a session."""
        # Create a session
        session = requests.Session()

        # Add metrics to the session
        stats = add_metrics(session)

        # Verify that the session has the metrics adapter mounted
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters

        # Verify the adapter is a MetricsAdapter
        http_adapter = session.adapters['http://']
        https_adapter = session.adapters['https://']
        assert isinstance(http_adapter, MetricsAdapter)
        assert isinstance(https_adapter, MetricsAdapter)

        # Verify both adapters use the same stats instance
        assert http_adapter._stats is stats
        assert https_adapter._stats is stats

        # Verify the underlying adapter is an HTTPAdapter
        assert isinstance(http_adapter._adapter, HTTPAdapter)
        assert isinstance(https_adapter._adapter, HTTPAdapter)

    def test_add_metrics_with_custom_adapter(self):
        """Test that add_metrics works with a custom adapter."""
        # Create a session
        session = requests.Session()

        # Create a custom adapter
        custom_adapter = HTTPAdapter(max_retries=3)

        # Add metrics to the session with the custom adapter
        stats = add_metrics(session, custom_adapter)

        # Verify the underlying adapter is the custom adapter
        http_adapter = session.adapters['http://']
        https_adapter = session.adapters['https://']
        assert http_adapter._adapter is custom_adapter
        assert https_adapter._adapter is custom_adapter


if __name__ == '__main__':
    pytest.main([__file__])