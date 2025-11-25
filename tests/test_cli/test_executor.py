# -*- coding: utf-8 -*-
"""Test cases for rhttp executor module."""
import unittest
import requests
from unittest.mock import Mock, patch
from requests.cli.executor import execute_request, prepare_request


class TestExecutor(unittest.TestCase):
    """Test cases for executor module functions."""

    @patch('requests.Session.request')
    def test_execute_request_success(self, mock_request):
        """Test successful request execution."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"key": "value"}'
        mock_request.return_value = mock_response
        
        # Execute request
        response, elapsed_time = execute_request(
            url='http://example.com',
            method='GET'
        )
        
        # Assertions
        mock_request.assert_called_once_with(
            method='GET',
            url='http://example.com',
            headers=None,
            data=None,
            json=None,
            files=None,
            timeout=30.0
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(elapsed_time, 0.0)

    @patch('requests.Session.request')
    def test_execute_request_with_retries(self, mock_request):
        """Test request execution with retries."""
        # Mock failed responses followed by successful response
        mock_request.side_effect = [
            requests.RequestException('Connection error'),
            requests.RequestException('Connection error'),
            Mock(status_code=200, reason='OK')
        ]
        
        # Execute request with 2 retries
        response, elapsed_time = execute_request(
            url='http://example.com',
            method='GET',
            retries=2,
            retry_backoff=1.0
        )
        
        # Assertions
        self.assertEqual(mock_request.call_count, 3)  # 2 retries + 1 successful
        self.assertEqual(response.status_code, 200)

    @patch('requests.Session')
    def test_execute_request_basic_auth(self, mock_session_class):
        """Test request with basic authentication."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Execute request with auth
        response, elapsed_time = execute_request(
            url='http://example.com',
            method='GET',
            auth=('user', 'pass')
        )
        
        # Check that session.auth was set
        self.assertTrue(mock_session.auth is not None)
        self.assertEqual(mock_session.auth.username, 'user')
        self.assertEqual(mock_session.auth.password, 'pass')

    @patch('requests.Session.request')
    def test_execute_request_bearer_auth(self, mock_request):
        """Test request with bearer token authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Execute request with bearer token
        response, elapsed_time = execute_request(
            url='http://example.com',
            method='GET',
            bearer='token123'
        )
        
        # Check that Authorization header was set
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertIn('headers', call_args)
        self.assertEqual(call_args['headers']['Authorization'], 'Bearer token123')

    def test_prepare_request_form_data(self):
        """Test preparing request with form data."""
        req_params = prepare_request(
            url='http://example.com',
            method='POST',
            data='param1=value1&param2=value2'
        )
        
        self.assertEqual(req_params['method'], 'POST')
        self.assertEqual(req_params['data'], {'param1': 'value1', 'param2': 'value2'})

    def test_prepare_request_json_data(self):
        """Test preparing request with JSON data."""
        req_params = prepare_request(
            url='http://example.com',
            method='POST',
            json='{"key": "value"}'
        )
        
        self.assertEqual(req_params['method'], 'POST')
        self.assertEqual(req_params['json'], {'key': 'value'})

    def test_prepare_request_with_auth(self):
        """Test preparing request with authentication."""
        req_params = prepare_request(
            url='http://example.com',
            auth='user:pass'
        )
        
        self.assertEqual(req_params['auth'], ('user', 'pass'))

    def test_prepare_request_with_bearer(self):
        """Test preparing request with bearer token."""
        req_params = prepare_request(
            url='http://example.com',
            bearer='token123'
        )
        
        self.assertEqual(req_params['bearer'], 'token123')


if __name__ == '__main__':
    unittest.main()
