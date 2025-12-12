"""Test cases for reqcheck"""

import json
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

import pytest

from reqcheck.config import Config
from reqcheck.requestor import Requestor
from reqcheck.exporters import CSVExporter, JSONExporter
from reqcheck.downloader import Downloader


class TestConfig:
    """Test configuration parsing"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = Config(
            urls_file=Path("examples/urls.txt"),
            output_file=Path("results.csv"),
            concurrency=10,
            max_retries=3
        )
        
        assert config.concurrency == 10
        assert config.max_retries == 3
        
        # Invalid concurrency
        with pytest.raises(ValueError):
            Config(urls_file=Path("examples/urls.txt"), concurrency=0)
        
        # Invalid max retries
        with pytest.raises(ValueError):
            Config(urls_file=Path("examples/urls.txt"), max_retries=-1)


class TestRequestor:
    """Test request handling"""
    
    @patch("requests.Session.request")
    def test_successful_request(self, mock_request):
        """Test successful HTTP request"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.history = []
        mock_response.headers = {"Content-Length": "1000"}
        mock_request.return_value = mock_response
        
        requestor = Requestor()
        result = requestor.request("https://example.com")
        
        assert result["status_code"] == 200
        assert result["final_url"] == "https://example.com"
        assert result["redirected"] is False
        assert result["timed_out"] is False
        assert result["content_length"] == 1000
        assert result["error"] is None
    
    @patch("requests.Session.request")
    def test_redirected_request(self, mock_request):
        """Test redirected request"""
        # Mock response with history
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/redirected"
        mock_response.history = [Mock()]
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        requestor = Requestor()
        result = requestor.request("https://example.com")
        
        assert result["redirected"] is True
        assert result["final_url"] == "https://example.com/redirected"
    
    @patch("requests.Session.request")
    def test_request_timeout(self, mock_request):
        """Test request timeout"""
        import requests
        mock_request.side_effect = requests.Timeout
        
        requestor = Requestor(timeout=1.0)
        result = requestor.request("https://example.com")
        
        assert result["timed_out"] is True
        assert result["error"] is not None


class TestExporters:
    """Test result exporters"""
    
    def test_csv_export(self):
        """Test CSV export"""
        results = [{
            "url": "https://example.com",
            "final_url": "https://example.com",
            "status_code": 200,
            "elapsed": 0.5,
            "redirected": False,
            "timed_out": False,
            "content_length": 1000,
            "error": None
        }]
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        exporter = CSVExporter(tmp_path)
        exporter.export(results)
        
        assert tmp_path.exists()
        
        # Cleanup
        tmp_path.unlink()
    
    def test_json_export(self):
        """Test JSON export"""
        results = [{
            "url": "https://example.com",
            "final_url": "https://example.com",
            "status_code": 200,
            "elapsed": 0.5,
            "redirected": False,
            "timed_out": False,
            "content_length": 1000,
            "error": None
        }]
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        exporter = JSONExporter(tmp_path)
        exporter.export(results)
        
        assert tmp_path.exists()
        
        # Verify JSON content
        with open(tmp_path, "r") as f:
            data = json.load(f)
        
        assert data[0]["url"] == "https://example.com"
        assert data[0]["status_code"] == 200
        
        # Cleanup
        tmp_path.unlink()


class TestDownloader:
    """Test downloader"""
    
    def test_get_filename_from_url(self):
        """Test filename extraction from URL"""
        downloader = Downloader({
            "download_dir": "downloads",
            "timeout": 10.0,
            "max_retries": 3,
            "retry_delay": 1.0,
            "proxy": None,
            "headers": None,
            "cookies": None
        })
        
        # Normal URL
        filename = downloader.get_filename_from_url("https://example.com/file.txt")
        assert filename == "file.txt"
        
        # URL with path but no filename
        filename = downloader.get_filename_from_url("https://example.com/")
        assert filename == "index.html"
        
        # URL with query params
        filename = downloader.get_filename_from_url("https://example.com/file.txt?param=1")
        assert filename == "file.txt"


class TestRunner:
    """Test main runner"""
    
    def test_load_urls(self):
        """Test loading URLs from file"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("https://example.com\n")
            tmp.write("# Comment\n")
            tmp.write("https://google.com\n")
            tmp_path = Path(tmp.name)
        
        # Test loading
        from reqcheck.runner import load_urls
        urls = load_urls(tmp_path)
        
        assert len(urls) == 2
        assert urls[0] == "https://example.com"
        assert urls[1] == "https://google.com"
        
        # Cleanup
        tmp_path.unlink()
    
    def test_empty_url_file(self):
        """Test loading empty URL file"""
        # Create empty file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        from reqcheck.runner import load_urls
        with pytest.raises(ValueError):
            load_urls(tmp_path)
        
        # Cleanup
        tmp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])