"""
Tests for status code distribution functionality
"""

import pytest
from requests.metrics import Stats


class TestStatsStatus:
    """Test cases for status code distribution tracking."""
    
    def test_status_distribution(self):
        """Test status code distribution tracking."""
        stats = Stats()
        
        # Record various status codes
        status_codes = [200, 200, 201, 404, 500, 200, 301]
        for code in status_codes:
            stats.record(status_code=code, response_time=0.1)
        
        distribution = stats.status_distribution
        assert distribution[200] == 3
        assert distribution[201] == 1
        assert distribution[404] == 1
        assert distribution[500] == 1
        assert distribution[301] == 1
        assert sum(distribution.values()) == 7