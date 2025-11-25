# -*- coding: utf-8 -*-
"""Test cases for rhttp report module."""
import unittest
from unittest.mock import Mock
from requests.cli.report import format_response, generate_batch_summary, format_batch_result


class TestReport(unittest.TestCase):
    """Test cases for report module functions."""

    def test_format_response_success(self):
        """Test formatting a successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"key": "value"}'

        # Test show=body
        output = format_response(mock_response, show='body', color=False, elapsed_ms=123.45, attempts_used=1)
        self.assertIn('200 OK', output)
        self.assertIn('Elapsed: 123.45ms', output)
        self.assertIn('Retries: 0', output)
        self.assertIn('Body: 16 bytes', output)
        self.assertIn('{"key": "value"}', output)

        # Test show=headers
        output = format_response(mock_response, show='headers', color=False, elapsed_ms=123.45, attempts_used=1)
        self.assertIn('200 OK', output)
        self.assertIn('Elapsed: 123.45ms', output)
        self.assertIn('Retries: 0', output)
        self.assertIn('Headers:', output)
        self.assertIn('Content-Type: application/json', output)

        # Test show=all
        output = format_response(mock_response, show='all', color=False, elapsed_ms=123.45, attempts_used=1)
        self.assertIn('200 OK', output)
        self.assertIn('Elapsed: 123.45ms', output)
        self.assertIn('Retries: 0', output)
        self.assertIn('Headers:', output)
        self.assertIn('Content-Type: application/json', output)
        self.assertIn('Body: 16 bytes', output)
        self.assertIn('{"key": "value"}', output)

        # Test show=summary
        output = format_response(mock_response, show='summary', color=False, elapsed_ms=123.45, attempts_used=1)
        self.assertIn('200 OK', output)
        self.assertIn('Elapsed: 123.45ms', output)
        self.assertIn('Retries: 0', output)
        self.assertIn('Body: 16 bytes', output)

    def test_format_response_error(self):
        """Test formatting an error response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = 'Not Found'
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = '<html><body>Page not found</body></html>'

        output = format_response(mock_response, show='body', color=False, elapsed_ms=50.12, attempts_used=2)
        self.assertIn('404 Not Found', output)
        self.assertIn('Elapsed: 50.12ms', output)
        self.assertIn('Retries: 1', output)
        self.assertIn('Body: 40 bytes', output)
        self.assertIn('Page not found', output)

    def test_format_response_color(self):
        """Test formatting response with color."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"key": "value"}'

        output = format_response(mock_response, show='body', color=True, elapsed_ms=123.45, attempts_used=1)
        self.assertIn('200 OK', output)
        self.assertIn('Elapsed: 123.45ms', output)
        self.assertIn('Retries: 0', output)
        # Check that color codes are present (simplified check)
        self.assertIn('\x1b[', output)

    def test_generate_batch_summary(self):
        """Test generating batch summary."""
        results = [
            {'name': 'req1', 'method': 'GET', 'status_code': 200, 'reason': 'OK', 'elapsed_ms': 123.45, 'attempts_used': 1},
            {'name': 'req2', 'method': 'POST', 'status_code': 404, 'reason': 'Not Found', 'elapsed_ms': 50.12, 'attempts_used': 2},
            {'name': 'req3', 'method': 'PUT', 'status_code': 500, 'reason': 'Internal Server Error', 'elapsed_ms': 300.78, 'attempts_used': 3}
        ]

        output = generate_batch_summary(results, color=False)
        self.assertIn('Batch Summary:', output)
        self.assertIn('Total requests: 3', output)
        self.assertIn('Successful: 1', output)
        self.assertIn('Failed: 2', output)
        # Check that table headers are present
        self.assertIn('Name', output)
        self.assertIn('Method', output)
        self.assertIn('Status', output)
        self.assertIn('Time (ms)', output)
        self.assertIn('Retries Used', output)
        # Check that table rows are present
        self.assertIn('req1', output)
        self.assertIn('GET', output)
        self.assertIn('200 OK', output)
        self.assertIn('123.45', output)
        self.assertIn('0', output)

    def test_generate_batch_summary_color(self):
        """Test generating batch summary with color."""
        results = [
            {'status_code': 200, 'reason': 'OK'},
            {'status_code': 404, 'reason': 'Not Found'},
            {'status_code': 500, 'reason': 'Internal Server Error'}
        ]

        output = generate_batch_summary(results, color=True)
        self.assertIn('Batch Summary:', output)
        self.assertIn('Total requests: 3', output)
        self.assertIn('Successful: 1', output)
        self.assertIn('Failed: 2', output)
        # Check that color codes are present (simplified check)
        self.assertIn('\x1b[', output)

    def test_format_batch_result_success(self):
        """Test formatting a successful batch result."""
        result = {
            'index': 0,
            'method': 'GET',
            'url': 'http://example.com',
            'status_code': 200,
            'reason': 'OK',
            'elapsed_time': 0.123,
            'attempts_used': 1
        }

        output = format_batch_result(result, color=False)
        self.assertIn('Request 1: GET http://example.com - 200 OK', output)
        self.assertIn('Elapsed: 0.123s', output)
        self.assertIn('Retries: 0', output)

    def test_format_batch_result_error(self):
        """Test formatting an error batch result."""
        result = {
            'index': 1,
            'method': 'POST',
            'url': 'http://example.com/api',
            'status_code': 404,
            'reason': 'Not Found',
            'elapsed_time': 0.050,
            'attempts_used': 2
        }

        output = format_batch_result(result, color=False)
        self.assertIn('Request 2: POST http://example.com/api - 404 Not Found', output)
        self.assertIn('Elapsed: 0.050s', output)
        self.assertIn('Retries: 1', output)


if __name__ == '__main__':
    unittest.main()
