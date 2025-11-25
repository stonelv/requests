"""Test CLI functionality."""

import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from webcache_explorer.cli import main
from webcache_explorer.config import Config


class TestCLI:
    """Test CLI commands."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def urls_file(self, temp_dir):
        """Create test URLs file."""
        urls_file = temp_dir / "urls.txt"
        urls_file.write_text("https://httpbin.org/html\nhttps://httpbin.org/json")
        return urls_file
    
    @pytest.fixture
    def config_file(self, temp_dir):
        """Create test config file."""
        config_file = temp_dir / "config.toml"
        config_content = """
        [fetching]
        max_workers = 2
        timeout = 10
        max_retries = 2
        retry_delay = 1.0
        
        [storage]
        data_dir = "data"
        index_file = "index.json"
        
        [processing]
        max_content_size = 10485760
        
        [logging]
        level = "INFO"
        file = "webcache_explorer.log"
        """
        config_file.write_text(config_content)
        return config_file
    
    def test_fetch_command(self, urls_file, config_file, temp_dir):
        """Test fetch command."""
        with patch('sys.argv', ['webcache_explorer', 'fetch', '--urls', str(urls_file), '--config', str(config_file)]):
            with patch('webcache_explorer.cli.WebCrawler') as mock_crawler_class:
                mock_crawler = MagicMock()
                mock_crawler_class.return_value = mock_crawler
                mock_crawler.fetch_urls.return_value = [
                    {
                        'url': 'https://httpbin.org/html',
                        'success': True,
                        'content': '<html>Test content</html>',
                        'status_code': 200,
                        'fetch_time': 1.0,
                        'content_hash': 'hash1'
                    },
                    {
                        'url': 'https://httpbin.org/json',
                        'success': True,
                        'content': '{"test": "data"}',
                        'status_code': 200,
                        'fetch_time': 0.5,
                        'content_hash': 'hash2'
                    }
                ]
                
                # Mock CacheManager
                with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                    mock_cache = MagicMock()
                    mock_cache_class.return_value = mock_cache
                    mock_cache.get_stats.return_value = {
                        'total_entries': 2,
                        'successful_entries': 2,
                        'failed_entries': 0,
                        'success_rate': 1.0
                    }
                    
                    main()
                    
                    # Verify WebCrawler was called
                    mock_crawler_class.assert_called_once()
                    mock_crawler.fetch_urls.assert_called_once()
                    
                    # Verify CacheManager was called
                    mock_cache_class.assert_called_once()
                    mock_cache.store.assert_called()
                    mock_cache.get_stats.assert_called_once()
    
    def test_refetch_command(self, urls_file, config_file):
        """Test refetch command."""
        with patch('sys.argv', ['webcache_explorer', 'refetch', '--urls', str(urls_file), '--config', str(config_file)]):
            with patch('webcache_explorer.cli.WebCrawler') as mock_crawler_class:
                mock_crawler = MagicMock()
                mock_crawler_class.return_value = mock_crawler
                mock_crawler.fetch_urls.return_value = [
                    {
                        'url': 'https://httpbin.org/html',
                        'success': True,
                        'content': '<html>Updated content</html>',
                        'status_code': 200,
                        'fetch_time': 1.0,
                        'content_hash': 'new_hash1'
                    }
                ]
                
                with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                    mock_cache = MagicMock()
                    mock_cache_class.return_value = mock_cache
                    
                    main()
                    
                    # Verify WebCrawler was called with force_refetch=True
                    mock_crawler_class.assert_called_once_with(force_refetch=True)
                    mock_crawler.fetch_urls.assert_called_once()
    
    def test_add_url_command(self, config_file):
        """Test add-url command."""
        with patch('sys.argv', ['webcache_explorer', 'add-url', 'https://example.com', '--config', str(config_file)]):
            with patch('webcache_explorer.cli.WebCrawler') as mock_crawler_class:
                mock_crawler = MagicMock()
                mock_crawler_class.return_value = mock_crawler
                mock_crawler.fetch_url.return_value = {
                    'url': 'https://example.com',
                    'success': True,
                    'content': '<html>Example content</html>',
                    'status_code': 200,
                    'fetch_time': 1.0,
                    'content_hash': 'hash123'
                }
                
                with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                    mock_cache = MagicMock()
                    mock_cache_class.return_value = mock_cache
                    
                    main()
                    
                    # Verify WebCrawler was called
                    mock_crawler_class.assert_called_once()
                    mock_crawler.fetch_url.assert_called_once_with('https://example.com')
                    
                    # Verify CacheManager was called
                    mock_cache_class.assert_called_once()
                    mock_cache.store.assert_called_once()
    
    def test_search_command(self, config_file):
        """Test search command."""
        with patch('sys.argv', ['webcache_explorer', 'search', 'python programming', '--config', str(config_file)]):
            with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache
                
                # Mock cache entries
                mock_entries = [
                    {
                        'url': 'https://python.org',
                        'content': 'Python is a programming language.',
                        'title': 'Python Programming Language',
                        'status_code': 200,
                        'fetch_time': 1.0,
                        'content_hash': 'hash1'
                    },
                    {
                        'url': 'https://javascript.com',
                        'content': 'JavaScript is a programming language.',
                        'title': 'JavaScript Programming',
                        'status_code': 200,
                        'fetch_time': 1.2,
                        'content_hash': 'hash2'
                    }
                ]
                
                # Mock get_successful_urls and retrieve
                mock_cache.get_successful_urls.return_value = ['https://python.org', 'https://javascript.com']
                mock_cache.retrieve.side_effect = lambda url: next(
                    (entry for entry in mock_entries if entry['url'] == url), None
                )
                
                with patch('webcache_explorer.cli.TextProcessor') as mock_processor_class:
                    mock_processor = MagicMock()
                    mock_processor_class.return_value = mock_processor
                    
                    # Mock search results
                    from webcache_explorer.text_processor import SearchResult
                    mock_results = [
                        SearchResult(
                            url='https://python.org',
                            title='Python Programming Language',
                            relevance_score=0.95,
                            summary='Python is a programming language.'
                        )
                    ]
                    mock_processor.search_content.return_value = mock_results
                    
                    main()
                    
                    # Verify CacheManager was called
                    mock_cache_class.assert_called_once()
                    mock_cache.get_successful_urls.assert_called_once()
                    
                    # Verify TextProcessor was called
                    mock_processor_class.assert_called_once()
                    mock_processor.search_content.assert_called_once()
    
    def test_stats_command(self, config_file):
        """Test stats command."""
        with patch('sys.argv', ['webcache_explorer', 'stats', '--config', str(config_file)]):
            with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache
                mock_cache.get_stats.return_value = {
                    'total_entries': 10,
                    'successful_entries': 8,
                    'failed_entries': 2,
                    'success_rate': 0.8,
                    'total_size_bytes': 1024000,
                    'total_size_mb': 0.98,
                    'average_fetch_time': 1.5
                }
                
                main()
                
                # Verify CacheManager was called
                mock_cache_class.assert_called_once()
                mock_cache.get_stats.assert_called_once()
    
    def test_show_command(self, config_file):
        """Test show command."""
        with patch('sys.argv', ['webcache_explorer', 'show', 'https://example.com', '--config', str(config_file)]):
            with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache
                
                # Mock cache entry
                mock_entry = {
                    'url': 'https://example.com',
                    'content': '<html><body>Example content</body></html>',
                    'title': 'Example Page',
                    'status_code': 200,
                    'fetch_time': 1.0,
                    'content_hash': 'hash123'
                }
                mock_cache.retrieve.return_value = mock_entry
                
                main()
                
                # Verify CacheManager was called
                mock_cache_class.assert_called_once()
                mock_cache.retrieve.assert_called_once_with('https://example.com')
    
    def test_export_command(self, config_file):
        """Test export command."""
        export_file = config_file.parent / "export.json"
        
        with patch('sys.argv', ['webcache_explorer', 'export', str(export_file), '--config', str(config_file)]):
            with patch('webcache_explorer.cli.CacheManager') as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache
                
                main()
                
                # Verify CacheManager was called
                mock_cache_class.assert_called_once()
                mock_cache.export_index.assert_called_once_with(str(export_file))
    
    def test_help_command(self):
        """Test help command."""
        with patch('sys.argv', ['webcache_explorer', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should exit with code 0 (success)
            assert exc_info.value.code == 0
    
    def test_invalid_command(self):
        """Test invalid command."""
        with patch('sys.argv', ['webcache_explorer', 'invalid_command']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should exit with non-zero code (error)
            assert exc_info.value.code != 0