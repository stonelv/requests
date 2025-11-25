import os
import json
import pytest
from unittest.mock import Mock, patch

from webcache_explorer.commands import fetch, add_url
from webcache_explorer.utils import sanitize_url, extract_text
from webcache_explorer.config import Config

@pytest.fixture
def config():
    """Fixture to provide a Config object."""
    return Config("test_config.toml")

def test_sanitize_url():
    """Test URL sanitization function."""
    assert sanitize_url("https://example.com/path/resource?query=value") == "example.com_path_resource_query=value"
    assert sanitize_url("http://test.com/page.html") == "test.com_page.html"
    assert sanitize_url("https://long-url.com/" + "a" * 300) == "long-url.com/" + "a" * 187  # Truncate to 200

def test_extract_text():
    """Test HTML text extraction function."""
    html = "<html><body><h1>Test Page</h1><p>This is a test.</p></body></html>"
    assert extract_text(html) == "Test PageThis is a test."
    
    html_with_tags = "<div><span>Hello</span> <b>World</b></div>"
    assert extract_text(html_with_tags) == "Hello World"
    
    empty_html = ""
    assert extract_text(empty_html) == ""

def test_config_loading():
    """Test configuration loading from file."""
    # Create test config file
    with open("test_config.toml", 'w') as f:
        f.write("""
        data_dir = "test_data"
        concurrency = 10
        timeout = 15
        retries = 5
        """)
    
    config = Config("test_config.toml")
    
    assert config.data_dir == "test_data"
    assert config.concurrency == 10
    assert config.timeout == 15
    assert config.retries == 5
    
    # Clean up
    os.remove("test_config.toml")

@patch('requests.Session.get')
def test_fetch_single_url_success(mock_get):
    """Test successful URL fetch."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Test Content</body></html>"
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Create config
    config = Config()
    
    # Test fetch
    with patch('webcache_explorer.commands.fetch.os.makedirs') as mock_makedirs, \
         patch('webcache_explorer.commands.fetch.open', mock_open()):
        fetch.fetch_urls("test_urls.txt", config)
        
        # Verify session was created with retries
        mock_get.assert_called()

@patch('requests.Session.get')
def test_fetch_single_url_failure(mock_get):
    """Test failed URL fetch."""
    # Mock response to raise exception
    mock_get.side_effect = Exception("Connection error")
    
    # Create config
    config = Config()
    
    # Test fetch
    with patch('webcache_explorer.commands.fetch.os.makedirs') as mock_makedirs, \
         patch('webcache_explorer.commands.fetch.open', mock_open()):
        fetch.fetch_urls("test_urls.txt", config)
        
        # Verify session was created with retries
        mock_get.assert_called()
