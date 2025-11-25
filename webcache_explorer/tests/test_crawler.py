"""Test web crawler functionality."""

import pytest
import responses
from unittest.mock import Mock, patch

from webcache_explorer.crawler import WebCrawler, FetchResult
from webcache_explorer.config import Config


class TestWebCrawler:
    """Test WebCrawler class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def crawler(self, config):
        """Create test crawler."""
        return WebCrawler(config)
    
    def test_crawler_initialization(self, config):
        """Test crawler initialization."""
        crawler = WebCrawler(config)
        assert crawler.config == config
        assert crawler.session is not None
    
    def test_validate_url(self, crawler):
        """Test URL validation."""
        # Valid URLs
        assert crawler.validate_url('https://example.com') is True
        assert crawler.validate_url('http://test.org/path') is True
        assert crawler.validate_url('https://sub.domain.com:8080/path?query=value') is True
        
        # Invalid URLs
        assert crawler.validate_url('not-a-url') is False
        assert crawler.validate_url('ftp://example.com') is False  # Only HTTP/HTTPS supported
        assert crawler.validate_url('') is False
        assert crawler.validate_url('example.com') is False  # Missing scheme
    
    @responses.activate
    def test_fetch_single_url_success(self, crawler):
        """Test successful single URL fetch."""
        url = 'https://example.com'
        content = '<html><body>Test content</body></html>'
        
        responses.add(
            responses.GET,
            url,
            body=content,
            status=200,
            content_type='text/html'
        )
        
        result = crawler.fetch_url(url)
        
        assert result.success is True
        assert result.url == url
        assert result.status_code == 200
        assert result.content == content
        assert result.content_type == 'text/html'
        assert result.error_message is None
        assert result.fetch_time > 0
        assert result.content_hash is not None
    
    @responses.activate
    def test_fetch_single_url_timeout(self, crawler):
        """Test URL fetch with timeout."""
        url = 'https://example.com'
        
        responses.add(
            responses.GET,
            url,
            body=Exception('Connection timeout')
        )
        
        result = crawler.fetch_url(url)
        
        assert result.success is False
        assert result.url == url
        assert 'timeout' in result.error_message.lower()
        assert result.content is None
    
    @responses.activate
    def test_fetch_single_url_404(self, crawler):
        """Test URL fetch with 404 error."""
        url = 'https://example.com/notfound'
        
        responses.add(
            responses.GET,
            url,
            status=404
        )
        
        result = crawler.fetch_url(url)
        
        assert result.success is True  # 404 is still a successful HTTP response
        assert result.url == url
        assert result.status_code == 404
        assert result.error_message is None
    
    @responses.activate
    def test_fetch_multiple_urls(self, crawler):
        """Test fetching multiple URLs concurrently."""
        urls = [
            'https://example1.com',
            'https://example2.com',
            'https://example3.com'
        ]
        
        for i, url in enumerate(urls):
            responses.add(
                responses.GET,
                url,
                body=f'<html><body>Content {i+1}</body></html>',
                status=200,
                content_type='text/html'
            )
        
        results = crawler.fetch_urls(urls, show_progress=False)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success is True
            assert result.url == urls[i]
            assert result.status_code == 200
            assert f'Content {i+1}' in result.content
    
    def test_content_hash_calculation(self, crawler):
        """Test content hash calculation."""
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"
        
        hash1 = crawler._calculate_content_hash(content1)
        hash2 = crawler._calculate_content_hash(content2)
        hash3 = crawler._calculate_content_hash(content3)
        
        assert hash1 == hash2  # Same content should have same hash
        assert hash1 != hash3  # Different content should have different hash
        assert len(hash1) == 64  # SHA256 hash length
    
    def test_close(self, crawler):
        """Test crawler cleanup."""
        crawler.close()
        # Should not raise any exceptions