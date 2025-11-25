"""
Tests for main.py module.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from requests.cli.main import (
    main, handle_single_request, handle_batch_mode,
    build_request_params, build_request_params_from_config,
    EXIT_SUCCESS, EXIT_ARGUMENT_ERROR, EXIT_REQUEST_ERROR, EXIT_BATCH_ERROR
)


class TestMainModule:
    """Test cases for main module."""
    
    def test_exit_codes(self):
        """Test exit code constants."""
        assert EXIT_SUCCESS == 0
        assert EXIT_ARGUMENT_ERROR == 2
        assert EXIT_REQUEST_ERROR == 10
        assert EXIT_BATCH_ERROR == 11
    
    @patch('requests.cli.main.create_parser')
    @patch('requests.cli.main.handle_single_request')
    def test_main_single_request_mode(self, mock_handle_single, mock_create_parser):
        """Test main function in single request mode."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.batch = None
        mock_args.url = "https://example.com"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        
        mock_handle_single.return_value = EXIT_SUCCESS
        
        result = main()
        
        assert result == EXIT_SUCCESS
        mock_handle_single.assert_called_once_with(mock_args)
    
    @patch('requests.cli.main.create_parser')
    @patch('requests.cli.main.handle_batch_mode')
    def test_main_batch_mode(self, mock_handle_batch, mock_create_parser):
        """Test main function in batch mode."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.batch = "config.yaml"
        mock_args.url = None
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        
        mock_handle_batch.return_value = EXIT_SUCCESS
        
        result = main()
        
        assert result == EXIT_SUCCESS
        mock_handle_batch.assert_called_once_with(mock_args)
    
    @patch('requests.cli.main.create_parser')
    def test_main_no_args(self, mock_create_parser):
        """Test main function with no arguments."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.batch = None
        mock_args.url = None
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        
        result = main()
        
        assert result == EXIT_ARGUMENT_ERROR
    
    @patch('requests.cli.main.create_parser')
    def test_main_argument_error(self, mock_create_parser):
        """Test main function with argument parsing error."""
        mock_parser = Mock()
        mock_parser.parse_args.side_effect = SystemExit(2)
        mock_create_parser.return_value = mock_parser
        
        result = main()
        
        assert result == EXIT_ARGUMENT_ERROR
    
    @patch('requests.cli.main.create_executor')
    @patch('requests.cli.main.ReportGenerator')
    def test_handle_single_request_success(self, mock_report_gen_class, mock_create_executor):
        """Test handling single successful request."""
        mock_args = Mock()
        mock_args.url = "https://example.com"
        mock_args.method = "GET"
        mock_args.headers = None
        mock_args.data = None
        mock_args.json = None
        mock_args.file = None
        mock_args.auth = None
        mock_args.bearer = None
        mock_args.timeout = 30.0
        mock_args.retries = 3
        mock_args.retry_backoff = 2.0
        mock_args.save = None
        mock_args.show = "all"
        mock_args.color = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        mock_executor = Mock()
        mock_executor.execute_request.return_value = mock_response
        mock_create_executor.return_value = mock_executor
        
        mock_report_gen = Mock()
        mock_report_gen_class.return_value = mock_report_gen
        
        result = handle_single_request(mock_args)
        
        assert result == EXIT_SUCCESS
        mock_executor.execute_request.assert_called_once()
        mock_report_gen.print_request_summary.assert_called_once()
        mock_report_gen.print_response_details.assert_called_once()
    
    @patch('requests.cli.main.create_executor')
    @patch('requests.cli.main.ReportGenerator')
    def test_handle_single_request_failure(self, mock_report_gen_class, mock_create_executor):
        """Test handling single failed request."""
        mock_args = Mock()
        mock_args.url = "https://example.com"
        mock_args.method = "GET"
        mock_args.headers = None
        mock_args.data = None
        mock_args.json = None
        mock_args.file = None
        mock_args.auth = None
        mock_args.bearer = None
        mock_args.timeout = 30.0
        mock_args.retries = 3
        mock_args.retry_backoff = 2.0
        mock_args.save = None
        mock_args.show = "all"
        mock_args.color = True
        
        mock_executor = Mock()
        from requests.cli.executor import RequestExecutorException
        mock_executor.execute_request.side_effect = RequestExecutorException("Request failed")
        mock_create_executor.return_value = mock_executor
        
        mock_report_gen = Mock()
        mock_report_gen_class.return_value = mock_report_gen
        
        result = handle_single_request(mock_args)
        
        assert result == EXIT_REQUEST_ERROR
        mock_executor.execute_request.assert_called_once()
        mock_report_gen.print_request_summary.assert_called_once()
        # Should not print response details for failed request
        mock_report_gen.print_response_details.assert_not_called()
    
    @patch('requests.cli.main.ConfigLoader')
    @patch('requests.cli.main.create_executor')
    @patch('requests.cli.main.ReportGenerator')
    def test_handle_batch_mode_success(self, mock_report_gen_class, mock_create_executor, mock_config_loader_class):
        """Test handling batch mode with all successful requests."""
        mock_args = Mock()
        mock_args.batch = "config.yaml"
        mock_args.color = True
        
        mock_config = {
            "requests": [
                {"url": "https://example.com", "method": "GET"},
                {"url": "https://api.example.com", "method": "POST"}
            ]
        }
        
        mock_loader = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_config_loader_class.return_value = mock_loader
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response2 = Mock()
        mock_response2.status_code = 201
        
        mock_executor = Mock()
        mock_executor.execute_request.side_effect = [mock_response1, mock_response2]
        mock_create_executor.return_value = mock_executor
        
        mock_report_gen = Mock()
        mock_report_gen_class.return_value = mock_report_gen
        
        result = handle_batch_mode(mock_args)
        
        assert result == EXIT_SUCCESS
        assert mock_executor.execute_request.call_count == 2
        assert mock_report_gen.print_request_summary.call_count == 2
        mock_report_gen.print_batch_summary.assert_called_once()
    
    @patch('requests.cli.main.ConfigLoader')
    @patch('requests.cli.main.create_executor')
    @patch('requests.cli.main.ReportGenerator')
    def test_handle_batch_mode_with_failures(self, mock_report_gen_class, mock_create_executor, mock_config_loader_class):
        """Test handling batch mode with some failed requests."""
        mock_args = Mock()
        mock_args.batch = "config.yaml"
        mock_args.color = True
        
        mock_config = {
            "requests": [
                {"url": "https://example.com", "method": "GET"},
                {"url": "https://failing.example.com", "method": "POST"}
            ]
        }
        
        mock_loader = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_config_loader_class.return_value = mock_loader
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        
        from requests.cli.executor import RequestExecutorException
        mock_executor = Mock()
        mock_executor.execute_request.side_effect = [mock_response1, RequestExecutorException("Failed")]
        mock_create_executor.return_value = mock_executor
        
        mock_report_gen = Mock()
        mock_report_gen_class.return_value = mock_report_gen
        
        result = handle_batch_mode(mock_args)
        
        assert result == EXIT_BATCH_ERROR  # Should return error code when there are failures
        assert mock_executor.execute_request.call_count == 2
        assert mock_report_gen.print_request_summary.call_count == 2
        mock_report_gen.print_batch_summary.assert_called_once()
    
    @patch('requests.cli.main.ConfigLoader')
    def test_handle_batch_mode_config_error(self, mock_config_loader_class):
        """Test handling batch mode with configuration error."""
        mock_args = Mock()
        mock_args.batch = "config.yaml"
        mock_args.color = True
        
        from requests.cli.config_loader import ConfigLoaderException
        mock_loader = Mock()
        mock_loader.load_config.side_effect = ConfigLoaderException("Invalid config")
        mock_config_loader_class.return_value = mock_loader
        
        result = handle_batch_mode(mock_args)
        
        assert result == EXIT_ARGUMENT_ERROR
    
    def test_build_request_params_basic(self):
        """Test building request parameters from arguments."""
        mock_args = Mock()
        mock_args.url = "https://example.com"
        mock_args.method = "POST"
        mock_args.headers = None
        mock_args.data = None
        mock_args.json = None
        mock_args.file = None
        mock_args.auth = None
        mock_args.bearer = None
        mock_args.timeout = 60.0
        mock_args.retries = 5
        mock_args.retry_backoff = 3.0
        
        params = build_request_params(mock_args)
        
        assert params["url"] == "https://example.com"
        assert params["method"] == "POST"
        assert params["timeout"] == 60.0
        assert params["retries"] == 5
        assert params["retry_backoff"] == 3.0
    
    def test_build_request_params_with_auth(self):
        """Test building request parameters with authentication."""
        mock_args = Mock()
        mock_args.url = "https://example.com"
        mock_args.method = "GET"
        mock_args.headers = None
        mock_args.data = None
        mock_args.json = None
        mock_args.file = None
        mock_args.auth = "user:pass"
        mock_args.bearer = None
        mock_args.timeout = 30.0
        mock_args.retries = 3
        mock_args.retry_backoff = 2.0
        
        params = build_request_params(mock_args)
        
        assert params["url"] == "https://example.com"
        assert params["auth"] == ("user", "pass")
    
    def test_build_request_params_with_bearer(self):
        """Test building request parameters with bearer token."""
        mock_args = Mock()
        mock_args.url = "https://example.com"
        mock_args.method = "GET"
        mock_args.headers = None
        mock_args.data = None
        mock_args.json = None
        mock_args.file = None
        mock_args.auth = None
        mock_args.bearer = "token123"
        mock_args.timeout = 30.0
        mock_args.retries = 3
        mock_args.retry_backoff = 2.0
        
        params = build_request_params(mock_args)
        
        assert params["url"] == "https://example.com"
        assert params["bearer_token"] == "token123"
    
    def test_build_request_params_from_config(self):
        """Test building request parameters from configuration."""
        config_request = {
            "url": "https://example.com",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "json": {"key": "value"},
            "timeout": 45.0,
            "retries": 2,
            "retry_backoff": 1.5
        }
        
        params = build_request_params_from_config(config_request)
        
        assert params["url"] == "https://example.com"
        assert params["method"] == "POST"
        assert params["headers"] == {"Content-Type": "application/json"}
        assert params["json_data"] == {"key": "value"}
        assert params["timeout"] == 45.0
        assert params["retries"] == 2
        assert params["retry_backoff"] == 1.5
    
    def test_build_request_params_from_config_with_defaults(self):
        """Test building request parameters from configuration with defaults."""
        config_request = {
            "url": "https://example.com",
            "method": "GET"
            # Missing optional parameters
        }
        
        params = build_request_params_from_config(config_request)
        
        assert params["url"] == "https://example.com"
        assert params["method"] == "GET"
        assert params["timeout"] == 30.0  # Default timeout
        assert params["retries"] == 3  # Default retries
        assert params["retry_backoff"] == 2.0  # Default backoff