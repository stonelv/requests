#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for status code distribution tracking."""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.requests.metrics import Stats


def test_status_distribution():
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
