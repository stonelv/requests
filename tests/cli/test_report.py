"""
Tests for report.py module.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from requests.cli.report import ReportGenerator, RequestResult


class TestRequestResult:
    """Test cases for RequestResult dataclass."""
    
    def test_request_result_creation(self):
        """Test RequestResult creation."""
        result = RequestResult(
            url="https://example.com",
            method="GET",
            status_code=200,
            response_time=0.5,
            error=None
        )
        
        assert result.url == "https://example.com"
        assert result.method == "GET"
        assert result.status_code == 200
        assert result.response_time == 0.5
        assert result.error is None
    
    def test_request_result_with_error(self):
        """Test RequestResult creation with error."""
        error = Exception("Connection failed")
        result = RequestResult(
            url="https://example.com",
            method="GET",
            status_code=None,
            response_time=1.0,
            error=error
        )
        
        assert result.url == "https://example.com"
        assert result.method == "GET"
        assert result.status_code is None
        assert result.response_time == 1.0
        assert result.error == error


class TestReportGenerator:
    """Test cases for ReportGenerator."""
    
    def test_create_generator_with_color(self):
        """Test ReportGenerator creation with color support."""
        generator = ReportGenerator(color=True)
        assert generator.color is True
    
    def test_create_generator_without_color(self):
        """Test ReportGenerator creation without color support."""
        generator = ReportGenerator(color=False)
        assert generator.color is False
    
    def test_print_request_summary_success(self):
        """Test printing request summary for successful request."""
        result = RequestResult(
            url="https://example.com",
            method="GET",
            status_code=200,
            response_time=0.5,
            error=None
        )
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_request_summary(result)
            
            # Check that print was called
            mock_print.assert_called()
            # Check that success message is in the output
            call_args = mock_print.call_args[0][0]
            assert "GET" in call_args
            assert "https://example.com" in call_args
            assert "200" in call_args
            assert "0.5s" in call_args
    
    def test_print_request_summary_failure(self):
        """Test printing request summary for failed request."""
        result = RequestResult(
            url="https://example.com",
            method="POST",
            status_code=None,
            response_time=1.0,
            error=Exception("Connection failed")
        )
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_request_summary(result)
            
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "POST" in call_args
            assert "https://example.com" in call_args
            assert "FAILED" in call_args
            assert "Connection failed" in call_args
    
    def test_print_response_details_with_headers(self):
        """Test printing response details with headers."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json", "Server": "nginx"}
        mock_response.text = '{"result": "success"}'
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_response_details(mock_response, show_headers=True, show_body=False)
            
            mock_print.assert_called()
            # Check that headers are printed
            call_args = str(mock_print.call_args_list)
            assert "Content-Type" in call_args
            assert "application/json" in call_args
    
    def test_print_response_details_with_body(self):
        """Test printing response details with body."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_response_details(mock_response, show_headers=False, show_body=True)
            
            mock_print.assert_called()
            # Check that body is printed
            call_args = str(mock_print.call_args_list)
            assert '{"result": "success"}' in call_args
    
    def test_print_response_details_with_all(self):
        """Test printing response details with headers and body."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_response_details(mock_response, show_headers=True, show_body=True)
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args_list)
            assert "Content-Type" in call_args
            assert '{"result": "success"}' in call_args
    
    def test_print_response_details_with_none(self):
        """Test printing response details with no details."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_response_details(mock_response, show_headers=False, show_body=False)
            
            # Should not print anything
            mock_print.assert_not_called()
    
    def test_print_batch_summary(self):
        """Test printing batch summary."""
        results = [
            RequestResult("https://example.com", "GET", 200, 0.5, None),
            RequestResult("https://api.example.com", "POST", 201, 1.0, None),
            RequestResult("https://failing.example.com", "GET", None, 2.0, Exception("Failed"))
        ]
        
        generator = ReportGenerator(color=False)
        
        with patch('builtins.print') as mock_print:
            generator.print_batch_summary(results)
            
            mock_print.assert_called()
            call_args = str(mock_print.call_args_list)
            assert "3" in call_args  # Total requests
            assert "2" in call_args  # Successful requests
            assert "1" in call_args  # Failed requests
    
    def test_save_response_to_file(self):
        """Test saving response to file."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        generator = ReportGenerator(color=False)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            generator.save_response_to_file(mock_response, temp_file)
            
            # Check that file was created and contains content
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "Status: 200" in content
                assert "Content-Type: application/json" in content
                assert '{"result": "success"}' in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_response_to_file_error(self):
        """Test saving response to file with write error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "test content"
        
        generator = ReportGenerator(color=False)
        
        # Try to save to a directory that doesn't exist
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('builtins.print') as mock_print:
                generator.save_response_to_file(mock_response, "/invalid/path/file.txt")
                
                # Should print error message
                mock_print.assert_called()
                call_args = mock_print.call_args[0][0]
                assert "Failed to save response" in call_args
    
    def test_get_status_code_category(self):
        """Test getting status code category."""
        generator = ReportGenerator()
        
        assert generator._get_status_code_category(100) == "Informational"
        assert generator._get_status_code_category(200) == "Success"
        assert generator._get_status_code_category(201) == "Success"
        assert generator._get_status_code_category(300) == "Redirection"
        assert generator._get_status_code_category(400) == "Client Error"
        assert generator._get_status_code_category(500) == "Server Error"
        assert generator._get_status_code_category(999) == "Unknown"
    
    def test_format_headers(self):
        """Test formatting headers."""
        generator = ReportGenerator()
        
        headers = {"Content-Type": "application/json", "Server": "nginx"}
        formatted = generator._format_headers(headers)
        
        assert "Content-Type: application/json" in formatted
        assert "Server: nginx" in formatted
    
    def test_format_headers_empty(self):
        """Test formatting empty headers."""
        generator = ReportGenerator()
        
        headers = {}
        formatted = generator._format_headers(headers)
        
        assert formatted == ""
    
    def test_color_codes_enabled(self):
        """Test color codes when color is enabled."""
        generator = ReportGenerator(color=True)
        
        assert generator._color_code("green") != ""
        assert generator._color_code("red") != ""
        assert generator._color_code("yellow") != ""
        assert generator._color_code("blue") != ""
        assert generator._color_code("reset") != ""
    
    def test_color_codes_disabled(self):
        """Test color codes when color is disabled."""
        generator = ReportGenerator(color=False)
        
        assert generator._color_code("green") == ""
        assert generator._color_code("red") == ""
        assert generator._color_code("yellow") == ""
        assert generator._color_code("blue") == ""
        assert generator._color_code("reset") == ""
    
    def test_format_time(self):
        """Test time formatting."""
        generator = ReportGenerator()
        
        assert generator._format_time(0.001) == "1.0ms"
        assert generator._format_time(0.1) == "100.0ms"
        assert generator._format_time(1.0) == "1.0s"
        assert generator._format_time(1.5) == "1.5s"
        assert generator._format_time(60.0) == "60.0s"