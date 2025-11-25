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
            loader = ConfigLoader(config_file)
            config = loader.load_config()
            
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
            loader = ConfigLoader(config_file)
            loader.load_config()
            processed_requests = loader.process_requests()
            
            assert processed_requests[0]["url"] == "https://example.com/api/users"
            assert processed_requests[0]["headers"]["Authorization"] == "Bearer secret123"
            assert processed_requests[0]["data"] == "key=secret123"
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
            loader = ConfigLoader(config_file)
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config()
            
            assert "Configuration must contain 'requests' list" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML configuration."""
        config_content = """
invalid yaml content:
  - missing colon
    invalid indentation
  invalid_key: {
    unclosed_brace: true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config()
            
            assert "Invalid YAML format" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_load_config_empty_requests(self):
        """Test loading configuration with empty requests list."""
        config_content = """
requests: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config()
            
            assert "'requests' list cannot be empty" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            # Validation happens automatically during load_config
            assert loader.config is not None
            assert "requests" in loader.config
        finally:
            os.unlink(config_file)
    
    def test_validate_config_empty_requests(self):
        """Test validating configuration with empty requests list."""
        # Create a temporary config file for testing
        config_content = """
requests: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config()
            
            assert "'requests' list cannot be empty" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_validate_config_missing_url(self):
        """Test validating configuration with missing URL."""
        # Create a temporary config file with invalid request (missing URL)
        config_content = """
requests:
  - method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            with pytest.raises(ConfigLoaderException) as exc_info:
                loader.load_config()
            
            assert "Request 0 must have a 'url'" in str(exc_info.value)
        finally:
            os.unlink(config_file)
    
    def test_validate_config_missing_method(self):
        """Test validating configuration with missing method."""
        # Create a temporary config file with invalid request (missing method)
        config_content = """
requests:
  - url: https://example.com
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            # Should not raise an exception, method should default to GET
            assert loader.config["requests"][0]["method"] == "GET"
        finally:
            os.unlink(config_file)
    
    def test_interpolate_variables_simple(self):
        """Test simple variable interpolation."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            result = loader._interpolate_string(
                "Hello ${name}!",
                {"name": "World"}
            )
            assert result == "Hello World!"
        finally:
            os.unlink(config_file)
    
    def test_interpolate_variables_multiple(self):
        """Test multiple variable interpolation."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            result = loader._interpolate_string(
                "${greeting} ${name}, welcome to ${place}!",
                {"greeting": "Hello", "name": "Alice", "place": "Earth"}
            )
            assert result == "Hello Alice, welcome to Earth!"
        finally:
            os.unlink(config_file)
    
    def test_interpolate_variables_nested_data(self):
        """Test variable interpolation in nested data structures."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
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
        finally:
            os.unlink(config_file)
    
    def test_interpolate_variables_undefined(self):
        """Test interpolation with undefined variables."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            result = loader._interpolate_string(
                "Hello ${name}!",
                {}  # Empty variables
            )
            assert result == "Hello ${name}!"  # Should leave undefined variables as-is
        finally:
            os.unlink(config_file)
    
    def test_interpolate_variables_no_variables(self):
        """Test interpolation when no variables are present."""
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            result = loader._interpolate_string(
                "Hello World!",
                {"name": "World"}
            )
            assert result == "Hello World!"
        finally:
            os.unlink(config_file)
    
    def test_process_request_with_defaults(self):
        """Test processing request with default values."""
        request = {
            "url": "https://example.com"
            # Missing method, should default to GET
        }
        
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            loader._validate_request(request, 0)
            
            assert request["url"] == "https://example.com"
            assert request["method"] == "GET"  # Should default to GET
            assert request["timeout"] == 30.0  # Should use default timeout
        finally:
            os.unlink(config_file)
    
    def test_process_request_with_custom_values(self):
        """Test processing request with custom values."""
        request = {
            "url": "https://example.com",
            "method": "POST",
            "timeout": 60.0,
            "retries": 5,
            "retry_backoff": 3.0
        }
        
        # Create a temporary config file for testing
        config_content = """
requests:
  - url: https://example.com
    method: GET
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            loader = ConfigLoader(config_file)
            loader.load_config()
            loader._validate_request(request, 0)
            
            assert request["url"] == "https://example.com"
            assert request["method"] == "POST"
            assert request["timeout"] == 60.0
            assert request["retries"] == 5
            assert request["retry_backoff"] == 3.0
        finally:
            os.unlink(config_file)