#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for MetricsAdapter functionality."""

import pytest
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from requests.models import Response
from requests.adapters import HTTPAdapter
from src.requests.metrics import MetricsAdapter, Stats


def test_send_records_metrics():
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


def test_send_records_errors():
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
