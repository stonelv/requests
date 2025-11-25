# -*- coding: utf-8 -*-
"""Test for the main module of rhttp tool."""
import sys
from unittest import mock
import pytest
from requests.cli.main import main


class TestMain:
    @mock.patch('sys.argv', ['rhttp', 'http://example.com'])
    @mock.patch('requests.cli.main.execute_request')
    def test_single_request_success(self, mock_execute_request):
        """Test single request mode with successful response."""
        # Mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.text = 'Test response'
        
        # Mock execute_request to return response and elapsed time
        mock_execute_request.return_value = (mock_response, 0.1, 1)
        
        # Run main function
        exit_code = main()
        
        # Verify exit code
        assert exit_code == 0
    
    @mock.patch('sys.argv', ['rhttp', 'http://example.com', '--retries', '3', '--method', 'POST', '--data', 'param1=value1'])
    @mock.patch('requests.cli.main.execute_request')
    def test_single_request_with_retries(self, mock_execute_request):
        """Test single request mode with retries."""
        # Mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.text = 'Test response'
        
        # Mock execute_request to return response and elapsed time
        mock_execute_request.return_value = (mock_response, 0.5, 2)  # 1 retry used
        
        # Run main function
        exit_code = main()
        
        # Verify exit code
        assert exit_code == 0
    
    @mock.patch('sys.argv', ['rhttp', '--batch', 'test_config.yaml'])
    @mock.patch('requests.cli.main.load_config')
    @mock.patch('requests.cli.main.interpolate_variables')
    @mock.patch('requests.cli.main.execute_request')
    def test_batch_mode_success(self, mock_execute_request, mock_interpolate, mock_load_config):
        """Test batch mode with all successful requests."""
        # Mock config
        mock_config = {
            'requests': [
                {'url': 'http://example.com', 'method': 'GET'},
                {'url': 'http://example.org', 'method': 'POST'}
            ]
        }
        mock_load_config.return_value = mock_config
        mock_interpolate.return_value = mock_config['requests']
        
        # Mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.reason = 'OK'
        mock_response.text = 'Test response'
        
        # Mock execute_request to return response and elapsed time
        mock_execute_request.return_value = (mock_response, 0.2, 1)
        
        # Run main function
        exit_code = main()
        
        # Verify exit code
        assert exit_code == 0
    
    @mock.patch('sys.argv', ['rhttp', '--batch', 'test_config.yaml'])
    @mock.patch('requests.cli.main.load_config')
    @mock.patch('requests.cli.main.interpolate_variables')
    @mock.patch('requests.cli.main.execute_request')
    def test_batch_mode_with_failure(self, mock_execute_request, mock_interpolate, mock_load_config):
        """Test batch mode with some failed requests."""
        # Mock config
        mock_config = {
            'requests': [
                {'url': 'http://example.com', 'method': 'GET'},
                {'url': 'http://example.invalid', 'method': 'POST'}
            ]
        }
        mock_load_config.return_value = mock_config
        mock_interpolate.return_value = mock_config['requests']
        
        # Mock successful response for first request
        mock_response_success = mock.Mock()
        mock_response_success.status_code = 200
        mock_response_success.reason = 'OK'
        mock_response_success.text = 'Test response'
        
        # Mock failure for second request
        mock_execute_request.side_effect = [
            (mock_response_success, 0.2, 1),
            Exception('Connection error')
        ]
        
        # Run main function
        exit_code = main()
        
        # Verify exit code (11 for partial failure)
        assert exit_code == 11