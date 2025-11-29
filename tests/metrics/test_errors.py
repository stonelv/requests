"""
Tests for error counting functionality
"""

import pytest
from requests.metrics import Stats


class TestStatsErrors:
    """Test cases for error counting functionality."""
    
    def test_error_counting(self):
        """Test error counting functionality."""
        stats = Stats()
        
        # Record some successful and failed requests
        stats.record(status_code=200, response_time=0.1)
        stats.record(error=True)  # Network error
        stats.record(status_code=500, response_time=0.2)
        stats.record(error=True)  # Timeout error
        
        assert stats.total_requests == 4
        assert stats.total_errors == 2
        assert stats.status_distribution[200] == 1
        assert stats.status_distribution[500] == 1