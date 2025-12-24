import unittest
import os
import tempfile
import json
import csv
from unittest.mock import Mock, patch, MagicMock
from src.reqcheck.config import Config, config
from src.reqcheck.logging_utils import Logger, init_logger, get_logger
from src.reqcheck.requestor import Requestor, RequestResult
from src.reqcheck.downloader import Downloader
from src.reqcheck.exporters import Exporter
from src.reqcheck.runner import Runner

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_parse_args(self):
        # Test parsing command line arguments
        test_args = ["https://example.com", "https://google.com", "-f", "test_urls.txt", "-o", "output.json", "-t", "5", "-c", "5", "-r", "2", "-d", "0.5", "-b", "1.5", "-p", "http://proxy:8080", "--format", "json", "--download", "--download-dir", "./downloads", "-v", "-q"]
        with patch('sys.argv', ['reqcheck'] + test_args):
            config = Config()
            config.parse_args()
            self.assertEqual(config.urls, ["https://example.com", "https://google.com"])
            self.assertEqual(config.urls_file, "test_urls.txt")
            self.assertEqual(config.output_file, "output.json")
            self.assertEqual(config.timeout, 5)
            self.assertEqual(config.concurrency, 5)
            self.assertEqual(config.retries, 2)
            self.assertEqual(config.retry_delay, 0.5)
            self.assertEqual(config.retry_backoff, 1.5)
            self.assertEqual(config.proxy, "http://proxy:8080")
            self.assertEqual(config.output_format, "json")
            self.assertEqual(config.download_mode, True)
            self.assertEqual(config.download_dir, "./downloads")
            self.assertEqual(config.verbose, True)
            self.assertEqual(config.quiet, True)
    
    def test_config_validation(self):
        config = Config()
        config.concurrency = 0
        with self.assertRaises(ValueError):
            config.validate()

class TestLogger(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_logger_init(self):
        logger = Logger(verbose=True)
        self.assertEqual(logger.verbose, True)
    
    def test_logger_output(self):
        from io import StringIO
        with patch('sys.stdout', new=StringIO()) as fake_output:
            logger = Logger(verbose=True)
            logger.info("Test info message")
            output = fake_output.getvalue()
            self.assertIn("INFO", output)
            self.assertIn("Test info message", output)

class TestRequestor(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_request_result(self):
        # Test RequestResult creation and attributes
        result = RequestResult(url='http://example.com')
        result.status_code = 200
        result.final_url = 'http://example.com'
        result.elapsed = 1.0
        result.redirected = False
        result.timed_out = False
        result.content_length = 100
        result.headers = {'Content-Type': 'text/html'}
        result.error = None
        result.success = True
        self.assertEqual(result.url, 'http://example.com')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.final_url, 'http://example.com')
        self.assertEqual(result.elapsed, 1.0)
        self.assertEqual(result.redirected, False)
        self.assertEqual(result.timed_out, False)
        self.assertEqual(result.content_length, 100)
        self.assertEqual(result.headers, {'Content-Type': 'text/html'})
        self.assertEqual(result.error, None)
        self.assertEqual(result.success, True)
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = 'http://example.com'
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.history = []
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        
        requestor = Requestor()
        result = requestor.send_request('http://example.com')
        self.assertEqual(result.success, True)
        self.assertEqual(result.status_code, 200)

class TestDownloader(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_get_filename_from_url(self):
        downloader = Downloader()
        filename = downloader.get_filename_from_url('http://example.com/file.txt')
        self.assertEqual(filename, 'file.txt')
    
    def test_get_filename_from_url_without_ext(self):
        downloader = Downloader()
        filename = downloader.get_filename_from_url('http://example.com/file')
        self.assertEqual(filename, 'file')

class TestExporter(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_convert_result_to_dict(self):
        result = RequestResult(url='http://example.com')
        result.status_code = 200
        result.final_url = 'http://example.com'
        result.elapsed = 1.0
        result.redirected = False
        result.timed_out = False
        result.content_length = 100
        result.headers = {'Content-Type': 'text/html'}
        result.error = None
        result.success = True
        exporter = Exporter()
        result_dict = exporter.convert_result_to_dict(result)
        self.assertEqual(result_dict['url'], 'http://example.com')
        self.assertEqual(result_dict['status_code'], 200)

class TestRunner(unittest.TestCase):
    def setUp(self):
        # Initialize logger before each test
        init_logger()
    
    def test_read_urls_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('http://example.com\n')
            f.write('http://google.com\n')
        
        runner = Runner()
        runner.urls_file = f.name
        urls = runner.read_urls_from_file()
        self.assertEqual(len(urls), 2)
        
        os.unlink(f.name)
    
    def test_collect_urls(self):
        runner = Runner()
        runner.urls = ['http://example.com']
        runner.urls_file = None
        urls = runner.collect_urls()
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], 'http://example.com')

if __name__ == '__main__':
    unittest.main()