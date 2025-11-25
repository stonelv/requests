"""Test cache management functionality."""

import json
import tempfile
import os
from pathlib import Path

import pytest

from webcache_explorer.cache import CacheManager, CacheEntry
from webcache_explorer.crawler import FetchResult
from webcache_explorer.config import Config


class TestCacheManager:
    """Test CacheManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        config = Config()
        config.data_dir = str(temp_dir / "data")
        config.index_file = "index.json"
        return config
    
    @pytest.fixture
    def cache_manager(self, config):
        """Create test cache manager."""
        return CacheManager(config)
    
    def test_cache_manager_initialization(self, config, temp_dir):
        """Test cache manager initialization."""
        cache_manager = CacheManager(config)
        
        assert cache_manager.config == config
        assert cache_manager.data_dir.exists()
        assert isinstance(cache_manager.index, dict)
    
    def test_store_successful_fetch(self, cache_manager):
        """Test storing successful fetch result."""
        fetch_result = FetchResult(
            url='https://example.com',
            success=True,
            content='<html><body>Test content</body></html>',
            status_code=200,
            content_type='text/html',
            fetch_time=1.5,
            content_hash='abc123'
        )
        
        success = cache_manager.store(fetch_result)
        
        assert success is True
        assert 'https://example.com' in cache_manager.index
        
        entry = cache_manager.index['https://example.com']
        assert entry.url == 'https://example.com'
        assert entry.content_hash == 'abc123'
        assert entry.status_code == 200
        assert entry.content_type == 'text/html'
        assert entry.fetch_time == 1.5
        assert entry.error_message is None
    
    def test_store_failed_fetch(self, cache_manager):
        """Test storing failed fetch result."""
        fetch_result = FetchResult(
            url='https://example.com',
            success=False,
            error_message='Connection timeout',
            fetch_time=30.0
        )
        
        success = cache_manager.store(fetch_result)
        
        assert success is True
        assert 'https://example.com' in cache_manager.index
        
        entry = cache_manager.index['https://example.com']
        assert entry.url == 'https://example.com'
        assert entry.success is False  # This is implicit from error_message
        assert entry.error_message == 'Connection timeout'
        assert entry.content_hash == ''
    
    def test_retrieve_successful_entry(self, cache_manager):
        """Test retrieving successful cache entry."""
        # First store a successful fetch
        content = '<html><body>Test content</body></html>'
        fetch_result = FetchResult(
            url='https://example.com',
            success=True,
            content=content,
            status_code=200,
            content_type='text/html',
            fetch_time=1.5,
            content_hash='abc123'
        )
        
        cache_manager.store(fetch_result)
        
        # Retrieve it
        retrieved = cache_manager.retrieve('https://example.com')
        
        assert retrieved is not None
        assert retrieved['url'] == 'https://example.com'
        assert retrieved['status_code'] == 200
        assert retrieved['content_type'] == 'text/html'
        assert retrieved['fetch_time'] == 1.5
        assert retrieved['content_hash'] == 'abc123'
        assert retrieved['content'] == content
        assert retrieved['success'] is True
    
    def test_retrieve_failed_entry(self, cache_manager):
        """Test retrieving failed cache entry."""
        # Store a failed fetch
        fetch_result = FetchResult(
            url='https://example.com',
            success=False,
            error_message='Connection timeout',
            fetch_time=30.0
        )
        
        cache_manager.store(fetch_result)
        
        # Retrieve it
        retrieved = cache_manager.retrieve('https://example.com')
        
        assert retrieved is not None
        assert retrieved['url'] == 'https://example.com'
        assert retrieved['error_message'] == 'Connection timeout'
        assert retrieved['content'] is None
        assert retrieved['success'] is False
    
    def test_retrieve_nonexistent_entry(self, cache_manager):
        """Test retrieving non-existent cache entry."""
        retrieved = cache_manager.retrieve('https://nonexistent.com')
        assert retrieved is None
    
    def test_get_failed_urls(self, cache_manager):
        """Test getting list of failed URLs."""
        # Store some successful and failed fetches
        success_result = FetchResult(
            url='https://success.com',
            success=True,
            content='content',
            status_code=200,
            fetch_time=1.0,
            content_hash='hash1'
        )
        
        fail_result = FetchResult(
            url='https://fail.com',
            success=False,
            error_message='Timeout',
            fetch_time=30.0
        )
        
        cache_manager.store(success_result)
        cache_manager.store(fail_result)
        
        failed_urls = cache_manager.get_failed_urls()
        
        assert len(failed_urls) == 1
        assert 'https://fail.com' in failed_urls
        assert 'https://success.com' not in failed_urls
    
    def test_get_successful_urls(self, cache_manager):
        """Test getting list of successful URLs."""
        # Store some successful and failed fetches
        success_result = FetchResult(
            url='https://success.com',
            success=True,
            content='content',
            status_code=200,
            fetch_time=1.0,
            content_hash='hash1'
        )
        
        fail_result = FetchResult(
            url='https://fail.com',
            success=False,
            error_message='Timeout',
            fetch_time=30.0
        )
        
        cache_manager.store(success_result)
        cache_manager.store(fail_result)
        
        successful_urls = cache_manager.get_successful_urls()
        
        assert len(successful_urls) == 1
        assert 'https://success.com' in successful_urls
        assert 'https://fail.com' not in successful_urls
    
    def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        # Store some entries
        for i in range(3):
            fetch_result = FetchResult(
                url=f'https://example{i}.com',
                success=True,
                content=f'content{i}',
                status_code=200,
                fetch_time=1.0 + i,
                content_hash=f'hash{i}'
            )
            cache_manager.store(fetch_result)
        
        # Add a failed entry
        fail_result = FetchResult(
            url='https://fail.com',
            success=False,
            error_message='Timeout',
            fetch_time=30.0
        )
        cache_manager.store(fail_result)
        
        stats = cache_manager.get_stats()
        
        assert stats['total_entries'] == 4
        assert stats['successful_entries'] == 3
        assert stats['failed_entries'] == 1
        assert stats['success_rate'] == 0.75
        assert stats['total_size_bytes'] > 0
        assert stats['total_size_mb'] > 0
        assert stats['average_fetch_time'] > 0
    
    def test_search_urls(self, cache_manager):
        """Test searching URLs."""
        # Store some entries
        urls = ['https://python.org', 'https://javascript.com', 'https://python-tutorial.net']
        for url in urls:
            fetch_result = FetchResult(
                url=url,
                success=True,
                content='content',
                status_code=200,
                fetch_time=1.0,
                content_hash='hash'
            )
            cache_manager.store(fetch_result)
        
        # Search for URLs containing 'python'
        results = cache_manager.search_urls('python')
        
        assert len(results) == 2
        assert 'https://python.org' in results
        assert 'https://python-tutorial.net' in results
        assert 'https://javascript.com' not in results
    
    def test_remove_entry(self, cache_manager):
        """Test removing cache entry."""
        # Store an entry
        fetch_result = FetchResult(
            url='https://example.com',
            success=True,
            content='content',
            status_code=200,
            fetch_time=1.0,
            content_hash='hash'
        )
        
        cache_manager.store(fetch_result)
        assert 'https://example.com' in cache_manager.index
        
        # Remove it
        success = cache_manager.remove('https://example.com')
        
        assert success is True
        assert 'https://example.com' not in cache_manager.index
    
    def test_remove_nonexistent_entry(self, cache_manager):
        """Test removing non-existent cache entry."""
        success = cache_manager.remove('https://nonexistent.com')
        assert success is False
    
    def test_clear_cache(self, cache_manager):
        """Test clearing all cache."""
        # Store some entries
        for i in range(3):
            fetch_result = FetchResult(
                url=f'https://example{i}.com',
                success=True,
                content=f'content{i}',
                status_code=200,
                fetch_time=1.0,
                content_hash=f'hash{i}'
            )
            cache_manager.store(fetch_result)
        
        assert len(cache_manager.index) == 3
        
        # Clear cache
        cache_manager.clear()
        
        assert len(cache_manager.index) == 0
    
    def test_export_index(self, cache_manager, temp_dir):
        """Test exporting cache index."""
        # Store an entry
        fetch_result = FetchResult(
            url='https://example.com',
            success=True,
            content='content',
            status_code=200,
            fetch_time=1.0,
            content_hash='hash'
        )
        cache_manager.store(fetch_result)
        
        # Export index
        output_file = temp_dir / "export.json"
        cache_manager.export_index(str(output_file))
        
        # Verify export
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'export_time' in data
        assert 'stats' in data
        assert 'entries' in data
        assert len(data['entries']) == 1
        assert 'https://example.com' in data['entries']