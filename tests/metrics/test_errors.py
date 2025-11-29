#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for error counting functionality."""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.requests.metrics import Stats


def test_error_counting():
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
