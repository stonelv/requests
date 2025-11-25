"""
Tests for parser.py module.
"""

import pytest
import argparse
from requests.cli.parser import (
    create_parser, parse_args, parse_headers, parse_form_data, validate_args
)


class TestParser:
    """Test cases for argument parser."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "rhttp"
    
    def test_parse_args_basic(self):
        """Test basic argument parsing."""
        args = parse_args(["https://example.com"])
        assert args.url == "https://example.com"
        assert args.method == "GET"
        assert args.timeout == 30.0
        assert args.retries == 0
        assert args.retry_backoff == 1.0
    
    def test_parse_args_with_method(self):
        """Test argument parsing with custom method."""
        args = parse_args(["https://example.com", "--method", "POST"])
        assert args.method == "POST"
    
    def test_parse_args_with_headers(self):
        """Test argument parsing with headers."""
        args = parse_args([
            "https://example.com",
            "-H", "Content-Type: application/json",
            "-H", "User-Agent: TestAgent"
        ])
        assert args.headers["Content-Type"] == "application/json"
        assert args.headers["User-Agent"] == "TestAgent"
    
    def test_parse_args_with_data(self):
        """Test argument parsing with form data."""
        args = parse_args([
            "https://example.com",
            "--data", "key1=value1&key2=value2"
        ])
        assert args.data["key1"] == "value1"
        assert args.data["key2"] == "value2"
    
    def test_parse_args_with_json(self):
        """Test argument parsing with JSON data."""
        args = parse_args([
            "https://example.com",
            "--json", '{"key": "value"}'
        ])
        assert args.json == '{"key": "value"}'
    
    def test_parse_args_with_auth(self):
        """Test argument parsing with basic auth."""
        args = parse_args([
            "https://example.com",
            "--auth", "user:pass"
        ])
        assert args.auth == "user:pass"
    
    def test_parse_args_with_bearer(self):
        """Test argument parsing with bearer token."""
        args = parse_args([
            "https://example.com",
            "--bearer", "token123"
        ])
        assert args.bearer == "token123"
    
    def test_parse_args_with_timeout(self):
        """Test argument parsing with custom timeout."""
        args = parse_args([
            "https://example.com",
            "--timeout", "60.0"
        ])
        assert args.timeout == 60.0
    
    def test_parse_args_with_retries(self):
        """Test argument parsing with retries."""
        args = parse_args([
            "https://example.com",
            "--retries", "3"
        ])
        assert args.retries == 3
    
    def test_parse_args_with_retry_backoff(self):
        """Test argument parsing with retry backoff."""
        args = parse_args([
            "https://example.com",
            "--retry-backoff", "2.0"
        ])
        assert args.retry_backoff == 2.0
    
    def test_parse_args_with_save(self):
        """Test argument parsing with save option."""
        args = parse_args([
            "https://example.com",
            "--save", "response.json"
        ])
        assert args.save == "response.json"
    
    def test_parse_args_with_show(self):
        """Test argument parsing with show option."""
        args = parse_args([
            "https://example.com",
            "--show", "headers"
        ])
        assert args.show == "headers"
    
    def test_parse_args_with_color(self):
        """Test argument parsing with color options."""
        args = parse_args([
            "https://example.com",
            "--color"
        ])
        assert args.color is True
        
        args = parse_args([
            "https://example.com",
            "--no-color"
        ])
        assert args.color is False
    
    def test_parse_args_with_batch(self):
        """Test argument parsing with batch mode."""
        args = parse_args([
            "--batch", "config.yaml"
        ])
        assert args.batch == "config.yaml"
        assert args.url is None
    
    def test_parse_args_missing_url(self):
        """Test argument parsing without URL (should fail)."""
        with pytest.raises(SystemExit):
            parse_args([])
    
    def test_parse_args_url_and_batch_conflict(self):
        """Test argument parsing with both URL and batch (should fail)."""
        with pytest.raises(SystemExit):
            parse_args(["https://example.com", "--batch", "config.yaml"])
    
    def test_parse_headers_valid(self):
        """Test header parsing."""
        headers = ["Content-Type: application/json", "User-Agent: Test"]
        result = parse_headers(headers)
        assert result["Content-Type"] == "application/json"
        assert result["User-Agent"] == "Test"
    
    def test_parse_headers_invalid_format(self):
        """Test header parsing with invalid format."""
        with pytest.raises(ValueError):
            parse_headers(["InvalidHeader"])
    
    def test_parse_form_data_valid(self):
        """Test form data parsing."""
        data = "key1=value1&key2=value2"
        result = parse_form_data(data)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
    
    def test_parse_form_data_invalid_format(self):
        """Test form data parsing with invalid format."""
        with pytest.raises(ValueError):
            parse_form_data("invalid_data")
    
    def test_validate_args_valid(self):
        """Test argument validation with valid args."""
        args = argparse.Namespace(
            retries=3,
            retry_backoff=2.0,
            timeout=60.0,
            batch="config.yaml"
        )
        validate_args(args)  # Should not raise
    
    def test_validate_args_invalid_retries(self):
        """Test argument validation with invalid retries."""
        args = argparse.Namespace(
            retries=-1,
            retry_backoff=1.0,
            timeout=30.0,
            batch=None
        )
        with pytest.raises(ValueError):
            validate_args(args)
    
    def test_validate_args_invalid_retry_backoff(self):
        """Test argument validation with invalid retry backoff."""
        args = argparse.Namespace(
            retries=0,
            retry_backoff=-1.0,
            timeout=30.0,
            batch=None
        )
        with pytest.raises(ValueError):
            validate_args(args)
    
    def test_validate_args_invalid_timeout(self):
        """Test argument validation with invalid timeout."""
        args = argparse.Namespace(
            retries=0,
            retry_backoff=1.0,
            timeout=0,
            batch=None
        )
        with pytest.raises(ValueError):
            validate_args(args)
    
    def test_validate_args_invalid_batch_file(self):
        """Test argument validation with invalid batch file."""
        args = argparse.Namespace(
            retries=0,
            retry_backoff=1.0,
            timeout=30.0,
            batch="config.txt"
        )
        with pytest.raises(ValueError):
            validate_args(args)