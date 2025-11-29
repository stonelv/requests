#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for basic Stats functionality."""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.requests.metrics import Stats


def test_basic_counting():
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
