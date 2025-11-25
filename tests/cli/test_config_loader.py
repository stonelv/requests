"""
Tests for config_loader.py module.
"""

import pytest
import tempfile
import os
from requests.cli.config_loader import ConfigLoader, ConfigLoaderException


class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    def test_load_valid_config(self):
        """Test loading valid configuration."""
        config_content = """
requests:
  - url: https://example.com
    method: GET
  - url: https://api.example.com
    method: POST
    headers:
      Content-Type: application/json
    json:
      key: value
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader()
            config = loader.load_config(config_file)
            
            assert "requests" in config
            assert len(config["requests"]) == 2
            assert config["requests"][0]["url"] == "https://example.com"
            assert config["requests"][0]["method"] == "GET"
            assert config["requests"][1]["url"] == "https://api.example.com"
            assert config["requests"][1]["method"] == "POST"
        finally:
            os.unlink(config_file)
    
    def test_load_config_with_variables(self):
        """Test loading configuration with variables."""
        config_content = """
variables:
  base_url: https://example.com
  api_key: secret123

requests:
  - url: ${base_url}/api/users
    method: GET
    headers:
      Authorization: Bearer ${api_key}
    data: "key=${api_key}"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader()
            config = loader.load_config(config_file)
            
            assert config["requests"][0]["url"] == "https://example.com/api/users"
            assert config["requests"][0]["headers"]["Authorization"] == "Bearer secret123"
            assert config["requests"][0]["data"] == "key=secret123"
        finally:
            os.unlink(config_file)
    
    def test_load_config_missing_requests(self):
        """Test loading configuration missing requests section."""
        config_content = """
variables:
  base_url: https://example.com
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader()
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config(config_file)
            
            assert "Configuration must contain a 'requests' list" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML file."""
        config_content = """
invalid yaml content:
  - missing colon
    invalid indentation
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader()
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config(config_file)
            
            assert "Failed to parse YAML configuration" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_load_config_nonexistent_file(self):
        """Test loading non-existent configuration file."""
        loader = ConfigLoader()
        with pytest.raises(ConfigLoaderException) as exc_info:
            loader.load_config("nonexistent.yaml")
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        config = {
            "requests": [
                {"url": "https://example.com", "method": "GET"},
                {"url": "https://api.example.com", "method": "POST"}
            ]
        }
        
        loader = ConfigLoader()
        loader._validate_config(config)  # Should not raise
    
    def test_validate_config_empty_requests(self):
        """Test validating configuration with empty requests list."""
        config = {"requests": []}
        
        loader = ConfigLoader()
        with pytest.raises(ConfigLoaderException) as exc_info:
            loader._validate_config(config)
        
        assert "Configuration must contain at least one request" in str(exc_info.value)
    
    def test_validate_config_missing_url(self):
        """Test validating configuration with missing URL."""
        config = {
            "requests": [
                {"method": "GET"}  # Missing URL
            ]
        }
        
        loader = ConfigLoader()
        with pytest.raises(ConfigLoaderException) as exc_info:
            loader._validate_config(config)
        
        assert "Each request must have a 'url'" in str(exc_info.value)
    
    def test_validate_config_missing_method(self):
        """Test validating configuration with missing method."""
        config = {
            "requests": [
                {"url": "https://example.com"}  # Missing method
            ]
        }
        
        loader = ConfigLoader()
        with pytest.raises(ConfigLoaderException) as exc_info:
            loader._validate_config(config)
        
        assert "Each request must have a 'method'" in str(exc_info.value)
    
    def test_interpolate_variables_simple(self):
        """Test simple variable interpolation."""
        loader = ConfigLoader()
        result = loader._interpolate_variables(
            "Hello ${name}!",
            {"name": "World"}
        )
        assert result == "Hello World!"
    
    def test_interpolate_variables_multiple(self):
        """Test multiple variable interpolation."""
        loader = ConfigLoader()
        result = loader._interpolate_variables(
            "${greeting} ${name}, welcome to ${place}!",
            {"greeting": "Hello", "name": "Alice", "place": "Earth"}
        )
        assert result == "Hello Alice, welcome to Earth!"
    
    def test_interpolate_variables_nested_data(self):
        """Test variable interpolation in nested data structures."""
        loader = ConfigLoader()
        data = {
            "url": "${base_url}/api/${endpoint}",
            "headers": {
                "Authorization": "Bearer ${token}",
                "X-Custom": "${custom_value}"
            },
            "data": "key=${value}"
        }
        
        variables = {
            "base_url": "https://api.example.com",
            "endpoint": "users",
            "token": "secret123",
            "custom_value": "test",
            "value": "data123"
        }
        
        result = loader._interpolate_variables(data, variables)
        
        assert result["url"] == "https://api.example.com/api/users"
        assert result["headers"]["Authorization"] == "Bearer secret123"
        assert result["headers"]["X-Custom"] == "test"
        assert result["data"] == "key=data123"
    
    def test_interpolate_variables_undefined(self):
        """Test interpolation with undefined variables."""
        loader = ConfigLoader()
        result = loader._interpolate_variables(
            "Hello ${name}!",
            {}  # Empty variables
        )
        assert result == "Hello ${name}!"  # Should leave undefined variables as-is
    
    def test_interpolate_variables_no_variables(self):
        """Test interpolation when no variables are present."""
        loader = ConfigLoader()
        result = loader._interpolate_variables(
            "Hello World!",
            {"name": "World"}
        )
        assert result == "Hello World!"
    
    def test_process_request_with_defaults(self):
        """Test processing request with default values."""
        request = {
            "url": "https://example.com"
            # Missing method, should default to GET
        }
        
        loader = ConfigLoader()
        processed = loader._process_request(request)
        
        assert processed["url"] == "https://example.com"
        assert processed["method"] == "GET"  # Should default to GET
        assert processed["timeout"] == 30.0  # Should use default timeout
    
    def test_process_request_with_custom_values(self):
        """Test processing request with custom values."""
        request = {
            "url": "https://example.com",
            "method": "POST",
            "timeout": 60.0,
            "retries": 5,
            "retry_backoff": 3.0
        }
        
        loader = ConfigLoader()
        processed = loader._process_request(request)
        
        assert processed["url"] == "https://example.com"
        assert processed["method"] == "POST"
        assert processed["timeout"] == 60.0
        assert processed["retries"] == 5
        assert processed["retry_backoff"] == 3.0