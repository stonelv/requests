"""
Integration tests for metrics functionality
"""

import time
import pytest
from unittest.mock import Mock, patch
from requests.metrics import Stats, MetricsAdapter
from requests.models import Response, Request
from requests.exceptions import RequestException


class TestMetricsIntegration:
    """Integration tests for metrics functionality."""
    
    def test_multiple_requests_metrics(self):
        """Test metrics collection across multiple requests."""
        adapter = MetricsAdapter()
        
        # Mock different response scenarios
        success_response = Mock(spec=Response)
        success_response.status_code = 200
        
        not_found_response = Mock(spec=Response)
        not_found_response.status_code = 404
        
        server_error_response = Mock(spec=Response)
        server_error_response.status_code = 500
        
        with patch('requests.adapters.HTTPAdapter.send') as mock_send:
            # Simulate different response scenarios
            mock_send.side_effect = [
                success_response,
                success_response,
                not_found_response,
                server_error_response,
                RequestException("Timeout")
            ]
            
            request = Mock(spec=Request)
            request.url = "http://example.com"
            
            # Make requests
            adapter.send(request)  # 200
            adapter.send(request)  # 200
            adapter.send(request)  # 404
            adapter.send(request)  # 500
            
            with pytest.raises(RequestException):
                adapter.send(request)  # Error
            
            # Verify final metrics
            assert adapter.stats.total_requests == 5
            assert adapter.stats.total_errors == 1
            assert adapter.stats.status_distribution[200] == 2
            assert adapter.stats.status_distribution[404] == 1
            assert adapter.stats.status_distribution[500] == 1
            assert len(adapter.stats.response_times) == 5
    
    def test_response_time_accuracy(self):
        """Test that response times are accurately recorded."""
        adapter = MetricsAdapter()
        
        # Mock response with controlled delay
        def mock_send_with_delay(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            response = Mock(spec=Response)
            response.status_code = 200
            return response
        
        with patch('requests.adapters.HTTPAdapter.send', side_effect=mock_send_with_delay):
            request = Mock(spec=Request)
            request.url = "http://example.com"
            
            start_time = time.time()
            adapter.send(request)
            actual_time = time.time() - start_time
            
            # Verify response time is recorded
            assert len(adapter.stats.response_times) == 1
            recorded_time = adapter.stats.response_times[0]
            
            # Allow some tolerance for timing
            assert 0.09 <= recorded_time <= 0.11
            assert abs(recorded_time - actual_time) < 0.02
    
    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        stats = Stats()
        
        # Record response times
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for rt in response_times:
            stats.record(status_code=200, response_time=rt)
        
        summary = stats.get_summary()
        
        assert summary['total_requests'] == 10
        assert summary['total_errors'] == 0
        assert summary['success_rate'] == 100.0
        assert summary['avg_response_time'] == 0.55
        assert summary['min_response_time'] == 0.1
        assert summary['max_response_time'] == 1.0
        # Allow some tolerance for percentile calculation
        assert 0.5 <= summary['p50_response_time'] <= 0.6
        assert 0.9 <= summary['p95_response_time'] <= 1.0
        assert 0.9 <= summary['p99_response_time'] <= 1.0