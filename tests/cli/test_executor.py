"""
Tests for executor.py module.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from requests.cli.executor import (
    RequestExecutor, RequestExecutorException, create_executor,
    parse_auth, is_success_status_code, get_status_code_category
)


class TestRequestExecutor:
    """Test cases for RequestExecutor."""
    
    def test_create_executor(self):
        """Test executor creation."""
        executor = create_executor(timeout=60.0, retries=3, retry_backoff=2.0)
        assert executor.timeout == 60.0
        assert executor.retries == 3
        assert executor.retry_backoff == 2.0
    
    @patch('requests.Session.request')
    def test_execute_request_success(self, mock_request):
        """Test successful request execution."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        executor = create_executor()
        response = executor.execute_request("https://example.com")
        
        assert response == mock_response
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_execute_request_with_retries(self, mock_request):
        """Test request execution with retries."""
        # Mock responses - first two fail, third succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_request.side_effect = [
            requests.Timeout("Timeout"),
            requests.ConnectionError("Connection failed"),
            mock_response_success
        ]
        
        executor = create_executor(retries=2, retry_backoff=0.1)
        response = executor.execute_request("https://example.com")
        
        assert response == mock_response_success
        assert mock_request.call_count == 3
    
    @patch('requests.Session.request')
    def test_execute_request_all_retries_fail(self, mock_request):
        """Test request execution when all retries fail."""
        mock_request.side_effect = requests.Timeout("Timeout")
        
        executor = create_executor(retries=2, retry_backoff=0.1)
        
        with pytest.raises(RequestExecutorException) as exc_info:
            executor.execute_request("https://example.com")
        
        assert "Request failed after 3 attempts" in str(exc_info.value)
        assert mock_request.call_count == 3
    
    def test_prepare_request_params_basic(self):
        """Test basic request parameter preparation."""
        executor = create_executor()
        params = executor._prepare_request_params(
            url="https://example.com",
            method="GET",
            headers=None,
            data=None,
            json_data=None,
            file_path=None,
            auth=None,
            bearer_token=None
        )
        
        assert params["method"] == "GET"
        assert params["url"] == "https://example.com"
        assert params["timeout"] == 30.0
    
    def test_prepare_request_params_with_headers(self):
        """Test request parameter preparation with headers."""
        executor = create_executor()
        headers = {"Content-Type": "application/json"}
        params = executor._prepare_request_params(
            url="https://example.com",
            method="POST",
            headers=headers,
            data=None,
            json_data=None,
            file_path=None,
            auth=None,
            bearer_token=None
        )
        
        assert params["headers"] == headers
        assert params["method"] == "POST"
    
    def test_prepare_request_params_with_auth(self):
        """Test request parameter preparation with basic auth."""
        executor = create_executor()
        params = executor._prepare_request_params(
            url="https://example.com",
            method="GET",
            headers=None,
            data=None,
            json_data=None,
            file_path=None,
            auth=("user", "pass"),
            bearer_token=None
        )
        
        assert "auth" in params
        assert params["auth"].username == "user"
        assert params["auth"].password == "pass"
    
    def test_prepare_request_params_with_bearer_token(self):
        """Test request parameter preparation with bearer token."""
        executor = create_executor()
        params = executor._prepare_request_params(
            url="https://example.com",
            method="GET",
            headers=None,
            data=None,
            json_data=None,
            file_path=None,
            auth=None,
            bearer_token="token123"
        )
        
        assert params["headers"]["Authorization"] == "Bearer token123"
    
    def test_prepare_request_params_with_json_data(self):
        """Test request parameter preparation with JSON data."""
        executor = create_executor()
        json_data = {"key": "value"}
        params = executor._prepare_request_params(
            url="https://example.com",
            method="POST",
            headers=None,
            data=None,
            json_data=json_data,
            file_path=None,
            auth=None,
            bearer_token=None
        )
        
        assert params["json"] == json_data
    
    def test_prepare_request_params_with_form_data(self):
        """Test request parameter preparation with form data."""
        executor = create_executor()
        data = "key1=value1&key2=value2"
        params = executor._prepare_request_params(
            url="https://example.com",
            method="POST",
            headers=None,
            data=data,
            json_data=None,
            file_path=None,
            auth=None,
            bearer_token=None
        )
        
        assert params["data"] == data
    
    @patch('builtins.open')
    def test_prepare_request_params_with_file(self, mock_open):
        """Test request parameter preparation with file upload."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        executor = create_executor()
        params = executor._prepare_request_params(
            url="https://example.com",
            method="POST",
            headers=None,
            data=None,
            json_data=None,
            file_path="test.txt",
            auth=None,
            bearer_token=None
        )
        
        assert "files" in params
        assert "file" in params["files"]
    
    def test_prepare_request_params_file_not_found(self):
        """Test request parameter preparation with non-existent file."""
        executor = create_executor()
        
        with pytest.raises(RequestExecutorException) as exc_info:
            executor._prepare_request_params(
                url="https://example.com",
                method="POST",
                headers=None,
                data=None,
                json_data=None,
                file_path="nonexistent.txt",
                auth=None,
                bearer_token=None
            )
        
        assert "Failed to read file" in str(exc_info.value)


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_parse_auth_valid(self):
        """Test parsing valid auth string."""
        username, password = parse_auth("user:pass")
        assert username == "user"
        assert password == "pass"
    
    def test_parse_auth_with_colon_in_password(self):
        """Test parsing auth string with colon in password."""
        username, password = parse_auth("user:pass:with:colons")
        assert username == "user"
        assert password == "pass:with:colons"
    
    def test_parse_auth_invalid_format(self):
        """Test parsing invalid auth string."""
        with pytest.raises(ValueError) as exc_info:
            parse_auth("invalid_auth")
        
        assert "Authentication must be in format" in str(exc_info.value)
    
    def test_is_success_status_code(self):
        """Test success status code checking."""
        assert is_success_status_code(200) is True
        assert is_success_status_code(201) is True
        assert is_success_status_code(299) is True
        assert is_success_status_code(300) is False
        assert is_success_status_code(404) is False
        assert is_success_status_code(500) is False
    
    def test_get_status_code_category(self):
        """Test status code category determination."""
        assert get_status_code_category(100) == "Informational"
        assert get_status_code_category(200) == "Success"
        assert get_status_code_category(201) == "Success"
        assert get_status_code_category(300) == "Redirection"
        assert get_status_code_category(400) == "Client Error"
        assert get_status_code_category(500) == "Server Error"
        assert get_status_code_category(999) == "Unknown"