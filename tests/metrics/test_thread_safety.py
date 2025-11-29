"""
Tests for thread safety functionality
"""

import threading
import pytest
from requests.metrics import Stats


class TestStatsThreadSafety:
    """Test cases for thread safety of Stats class."""
    
    def test_thread_safety(self):
        """Test thread safety of Stats class."""
        stats = Stats()
        num_threads = 10
        requests_per_thread = 100
        
        def worker():
            for i in range(requests_per_thread):
                if i % 10 == 0:  # 10% errors
                    stats.record(error=True)
                else:
                    status = 200 if i % 2 == 0 else 201
                    stats.record(status_code=status, response_time=0.01)
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify totals
        expected_total = num_threads * requests_per_thread
        expected_errors = num_threads * (requests_per_thread // 10)
        expected_success = expected_total - expected_errors
        
        assert stats.total_requests == expected_total
        assert stats.total_errors == expected_errors
        assert stats.status_distribution[200] + stats.status_distribution[201] == expected_success