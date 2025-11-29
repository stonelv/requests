#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for reset functionality of Stats class."""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.requests.metrics import Stats


def test_reset():
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
