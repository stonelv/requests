"""
Tests for MetricsAdapter functionality
"""

import pytest
from unittest.mock import Mock, patch
from requests.metrics import Stats, MetricsAdapter
from requests.adapters import HTTPAdapter
from requests.models import Response, Request
from requests.exceptions import RequestException


class TestMetricsAdapter:
    """Test cases for MetricsAdapter class."""
    
    def test_adapter_initialization(self):
        """Test MetricsAdapter initialization."""
        adapter = MetricsAdapter()
        
        assert isinstance(adapter._adapter, HTTPAdapter)
        assert isinstance(adapter._stats, Stats)
        assert adapter.stats is adapter._stats
    
    def test_adapter_with_custom_adapter(self):
        """Test MetricsAdapter with custom HTTPAdapter."""
        custom_adapter = HTTPAdapter()
        adapter = MetricsAdapter(adapter=custom_adapter)
        
        assert adapter._adapter is custom_adapter
        assert isinstance(adapter._stats, Stats)
    
    def test_adapter_with_custom_stats(self):
        """Test MetricsAdapter with custom Stats."""
        custom_stats = Stats()
        adapter = MetricsAdapter(stats=custom_stats)
        
        assert adapter._stats is custom_stats
        assert isinstance(adapter._adapter, HTTPAdapter)
    
    @patch('requests.adapters.HTTPAdapter.send')
    def test_successful_request_metrics(self, mock_send):
        """Test metrics collection for successful requests."""
        # Create mock response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_send.return_value = mock_response
        
        adapter = MetricsAdapter()
        request = Mock(spec=Request)
        request.url = "http://example.com"
        
        # Make request
        response = adapter.send(request)
        
        # Verify response
        assert response is mock_response
        
        # Verify metrics
        assert adapter.stats.total_requests == 1
        assert adapter.stats.total_errors == 0
        assert adapter.stats.status_distribution[200] == 1
        assert len(adapter.stats.response_times) == 1
        assert adapter.stats.response_times[0] >= 0
    
    @patch('requests.adapters.HTTPAdapter.send')
    def test_error_request_metrics(self, mock_send):
        """Test metrics collection for failed requests."""
        mock_send.side_effect = RequestException("Network error")
        
        adapter = MetricsAdapter()
        request = Mock(spec=Request)
        request.url = "http://example.com"
        
        # Make request and expect exception
        with pytest.raises(RequestException):
            adapter.send(request)
        
        # Verify metrics
        assert adapter.stats.total_requests == 1
        assert adapter.stats.total_errors == 1
        assert len(adapter.stats.status_distribution) == 0
        assert len(adapter.stats.response_times) == 1
    
    @patch('requests.adapters.HTTPAdapter.send')
    def test_general_exception_metrics(self, mock_send):
        """Test metrics collection for general exceptions."""
        mock_send.side_effect = ValueError("Unexpected error")
        
        adapter = MetricsAdapter()
        request = Mock(spec=Request)
        request.url = "http://example.com"
        
        # Make request and expect exception
        with pytest.raises(ValueError):
            adapter.send(request)
        
        # Verify metrics
        assert adapter.stats.total_requests == 1
        assert adapter.stats.total_errors == 1
        assert len(adapter.stats.status_distribution) == 0
        assert len(adapter.stats.response_times) == 1
    
    def test_adapter_delegation(self):
        """Test that MetricsAdapter delegates to underlying adapter."""
        custom_adapter = Mock(spec=HTTPAdapter)
        # Add the method we want to test to the mock's spec
        custom_adapter.some_method = Mock(return_value="method_result")
        adapter = MetricsAdapter(adapter=custom_adapter)
        
        # Test attribute delegation
        custom_adapter.some_attribute = "test_value"
        assert adapter.some_attribute == "test_value"
        
        # Test method delegation
        result = adapter.some_method("arg1", "arg2")
        custom_adapter.some_method.assert_called_once_with("arg1", "arg2")
        assert result == "method_result"
    
    def test_adapter_close(self):
        """Test that close method is properly delegated."""
        custom_adapter = Mock(spec=HTTPAdapter)
        adapter = MetricsAdapter(adapter=custom_adapter)
        
        adapter.close()
        custom_adapter.close.assert_called_once()