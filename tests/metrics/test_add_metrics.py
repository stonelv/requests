#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for add_metrics function."""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import requests
from requests.adapters import HTTPAdapter
from src.requests.metrics import add_metrics, MetricsAdapter


def test_add_metrics():
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


def test_add_metrics_with_custom_adapter():
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
