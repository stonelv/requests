"""
Tests for reset functionality
"""

import pytest
from requests.metrics import Stats


class TestStatsReset:
    """Test cases for reset functionality."""
    
    def test_reset(self):
        """Test reset functionality."""
        stats = Stats()
        
        # Record some data
        stats.record(status_code=200, response_time=0.1)
        stats.record(status_code=404, response_time=0.05)
        stats.record(error=True)
        
        assert stats.total_requests == 3
        assert stats.total_errors == 1
        assert len(stats.status_distribution) == 2
        assert len(stats.response_times) == 2
        
        # Reset and verify
        stats.reset()
        
        assert stats.total_requests == 0
        assert stats.total_errors == 0
        assert len(stats.status_distribution) == 0
        assert len(stats.response_times) == 0