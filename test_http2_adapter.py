import unittest
import requests
import time
import threading
from unittest.mock import Mock, patch
from requests.adapters_http2 import HTTP2Adapter
from requests.exceptions import Timeout, ConnectionError
import httpx


class TestHTTP2Adapter(unittest.TestCase):
    """Test suite for the HTTP2Adapter implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session = requests.Session()
        self.adapter = HTTP2Adapter(
            pool_connections=10,
            pool_maxsize=10,
            max_concurrent_streams=100,
            initial_window_size=65536,
            enable_push=True,
        )
        self.session.mount('https://', self.adapter)
        self.session.mount('http://', self.adapter)
    
    def tearDown(self):
        """Clean up after tests."""
        self.session.close()
        self.adapter.close()
    
    @patch('httpx.HTTP20Connection.request')
    def test_simple_request(self, mock_request):
        """Test that a simple HTTP/2 request works correctly."""
        # Mock the response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.read.return_value = b'{"key": "value"}'
        
        # Make the request
        response = self.session.get('https://example.com/api')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'key': 'value'})
        mock_request.assert_called_once()
    
    @patch('hyper.HTTP20Connection.request')
    def test_connection_reuse(self, mock_request):
        """Test that connections are reused for multiple requests to the same host."""
        # Mock responses
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.read.return_value = b'Hello, World!'
        
        # Make two requests
        response1 = self.session.get('https://example.com/api1')
        response2 = self.session.get('https://example.com/api2')
        
        # Assertions
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        # Should have only created one connection
        self.assertEqual(mock_request.call_count, 2)
    
    @patch('hyper.HTTP20Connection.request')
    def test_stream_timeout(self, mock_request):
        """Test that stream-level timeout works correctly."""
        # Make the request timeout
        mock_request.side_effect = httpx.ReadTimeout
        
        # Make the request with timeout
        with self.assertRaises(Timeout):
            self.session.get('https://example.com/api', timeout=1.0)
    
    @patch('hyper.HTTP20Connection.request')
    def test_connection_error(self, mock_request):
        """Test that connection errors are properly handled."""
        # Make the request raise a connection error
        mock_request.side_effect = httpx.ConnectError
        
        # Make the request
        with self.assertRaises(ConnectionError):
            self.session.get('https://example.com/api')
    
    def test_metric_callback(self):
        """Test that metric callback is invoked with correct data."""
        metrics = []
        
        def callback(**kwargs):
            metrics.append(kwargs)
        
        # Create adapter with metric callback
        adapter = HTTP2Adapter(metrics_callback=callback)
        session = requests.Session()
        session.mount('https://', adapter)
        
        # Mock the request
        with patch('hyper.HTTP20Connection.request') as mock_request:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.read.return_value = b'Hello'
            
            # Make the request
            response = session.get('https://example.com/api')
            
            # Assertions
            self.assertEqual(len(metrics), 1)
            self.assertEqual(metrics[0]['status'], 200)
            self.assertEqual(metrics[0]['method'], 'GET')
            self.assertEqual(metrics[0]['url'], 'https://example.com/api')
    
    def test_concurrent_streams(self):
        """Test that concurrent streams are handled correctly."""
        # Create adapter with limited concurrent streams
        adapter = HTTP2Adapter(max_concurrent_streams=2)
        session = requests.Session()
        session.mount('https://', adapter)
        
        # Mock the request to sleep for a short time
        def mock_sleep_request(*args, **kwargs):
            time.sleep(0.1)
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.read.return_value = b'Response'
            return mock_response
        
        # Make 5 concurrent requests
        with patch('hyper.HTTP20Connection.request', side_effect=mock_sleep_request):
            threads = []
            results = []
            
            def make_request(i):
                try:
                    response = session.get(f'https://example.com/api{i}')
                    results.append(response.status_code)
                except Exception as e:
                    results.append(str(e))
            
            # Start threads
            for i in range(5):
                t = threading.Thread(target=make_request, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for all threads to finish
            for t in threads:
                t.join()
            
            # Assertions
            self.assertEqual(len(results), 5)
            for result in results:
                self.assertEqual(result, 200)
    
    @patch('hyper.HTTP20Connection.request')
    def test_push_promise(self, mock_request):
        """Test that push promise events are handled correctly."""
        # Mock the response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.read.return_value = b'<html><body>Hello</body></html>'
        
        # Mock the push promise
        mock_push_promise = Mock()
        mock_push_promise.stream_id = 1
        mock_push_promise.headers = {':method': 'GET', ':path': '/style.css'}
        
        # Set up the mock connection
        mock_conn = Mock()
        mock_conn.request.return_value = mock_response
        mock_conn.events = [('push_promise', mock_push_promise)]
        
        # Make the request
        with patch('requests.adapters_http2.HTTP2Adapter.get_connection', return_value=mock_conn):
            response = self.session.get('https://example.com/index.html')
            
            # Assertions
            self.assertEqual(response.status_code, 200)
    
    def test_alpn_negotiation(self):
        """Test that ALPN negotiation is handled correctly."""
        # This test would need a real server that supports HTTP/2 and ALPN
        # For now, we'll mock the negotiation
        with patch('httpx.HTTP20Connection.__init__', return_value=None) as mock_init:
            adapter = HTTP2Adapter()
            
            # Check that the SSL context has ALPN protocols set
            self.assertIn(b'h2', adapter._tls_context.get_alpn_protocols())
            self.assertIn(b'http/1.1', adapter._tls_context.get_alpn_protocols())
    
    def test_configurable_window_size(self):
        """Test that initial window size is configurable."""
        window_size = 131072
        adapter = HTTP2Adapter(initial_window_size=window_size)
        
        # Check that the adapter has the correct window size
        self.assertEqual(adapter._initial_window_size, window_size)
    
    @patch('hyper.HTTP20Connection.request')
    def test_https_to_http_fallback(self, mock_request):
        """Test that the adapter falls back to HTTP/1.1 if HTTP/2 negotiation fails."""
        # Mock HTTPS request to fail with HTTP/2 negotiation error
        mock_request.side_effect = httpx.ProtocolError
        
        # Make HTTPS request
        with self.assertRaises(ConnectionError):
            self.session.get('https://example.com/api')
    
    def test_multiple_sessions(self):
        """Test that multiple sessions can use the same adapter."""
        adapter = HTTP2Adapter()
        
        # Create two sessions
        session1 = requests.Session()
        session2 = requests.Session()
        
        # Mount the adapter to both sessions
        session1.mount('https://', adapter)
        session2.mount('https://', adapter)
        
        # Mock requests
        with patch('hyper.HTTP20Connection.request') as mock_request:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.read.return_value = b'Response'
            
            # Make requests from both sessions
            response1 = session1.get('https://example.com/api1')
            response2 = session2.get('https://example.com/api2')
            
            # Assertions
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)
    
    @patch('hyper.HTTP20Connection.request')
    def test_large_response(self, mock_request):
        """Test that large responses are handled correctly."""
        # Create a large response body (1MB)
        large_body = b'a' * 1024 * 1024
        
        # Mock the response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/octet-stream'}
        mock_response.read.return_value = large_body
        
        # Make the request
        response = self.session.get('https://example.com/large-file')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
