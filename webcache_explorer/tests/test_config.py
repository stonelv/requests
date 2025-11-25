"""Test configuration management."""

import os
import tempfile
import pytest
from pathlib import Path

from webcache_explorer.config import Config


class TestConfig:
    """Test Config class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.max_workers == 10
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1
        assert config.data_dir == 'data'
        assert config.index_file == 'index.json'
        assert config.max_content_size == 10485760
        assert config.max_search_results == 50
        assert config.min_keyword_length == 2
    
    def test_custom_config_file(self):
        """Test loading from custom config file."""
        config_content = """
[fetching]
max_workers = 20
timeout = 60

[storage]
data_dir = "custom_data"

[processing]
max_search_results = 100
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            config = Config(temp_config_path)
            
            assert config.max_workers == 20
            assert config.timeout == 60
            assert config.data_dir == 'custom_data'
            assert config.max_search_results == 100
            
        finally:
            os.unlink(temp_config_path)
    
    def test_get_method(self):
        """Test configuration get method."""
        config = Config()
        
        # Test getting section
        fetching_section = config.get('fetching')
        assert isinstance(fetching_section, dict)
        assert 'max_workers' in fetching_section
        
        # Test getting specific key
        max_workers = config.get('fetching', 'max_workers')
        assert max_workers == 10
        
        # Test getting non-existent key with default
        default_value = config.get('nonexistent', 'key', 'default')
        assert default_value == 'default'
    
    def test_missing_config_file(self):
        """Test behavior with missing config file."""
        non_existent_path = '/path/that/does/not/exist.toml'
        config = Config(non_existent_path)
        
        # Should fall back to default values
        assert config.max_workers == 10
        assert config.timeout == 30