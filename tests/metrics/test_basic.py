"""
Tests for basic Stats functionality
"""

import pytest
from requests.metrics import Stats


class TestStatsBasic:
    """Test cases for basic Stats functionality."""
    
    def test_basic_counting(self):
        """Test basic request counting functionality."""
        stats = Stats()
        
        # Record some successful requests
        stats.record(status_code=200, response_time=0.1)
        stats.record(status_code=200, response_time=0.2)
        stats.record(status_code=404, response_time=0.05)
        
        assert stats.total_requests == 3
        assert stats.total_errors == 0
        assert stats.status_distribution[200] == 2
        assert stats.status_distribution[404] == 1
        assert len(stats.response_times) == 3
    
    def test_string_representation(self):
        """Test string representation of Stats."""
        stats = Stats()
        stats.record(status_code=200, response_time=0.1)
        stats.record(status_code=404, response_time=0.05)
        
        str_repr = str(stats)
        assert "Total Requests: 2" in str_repr
        assert "Total Errors: 0" in str_repr
        assert "Success Rate: 100.00%" in str_repr
        assert "200: 1" in str_repr
        assert "404: 1" in str_repr