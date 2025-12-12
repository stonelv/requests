import os
import json
import yaml
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from reqcheck.config import Config
from reqcheck.requestor import Requestor
from reqcheck.downloader import Downloader
from reqcheck.exporters import JSONExporter, CSVExporter
from reqcheck.runner import Runner

class TestConfig(unittest.TestCase):
    """配置模块测试"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = Config()
        self.assertEqual(config.method, "GET")
        self.assertEqual(config.timeout, 10)
        self.assertEqual(config.concurrency, 5)
    
    def test_config_validation(self):
        """测试配置验证"""
        config = Config()
        config.output_format = "invalid"
        with self.assertRaises(ValueError):
            config.validate()
        
        config.output_format = "json"
        config.method = "INVALID"
        with self.assertRaises(ValueError):
            config.validate()
    
    def test_config_from_json(self):
        """测试从JSON配置文件加载"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump({"method": "POST", "timeout": 20}, f)
        
        config = Config.from_file(f.name)
        self.assertEqual(config.method, "POST")
        self.assertEqual(config.timeout, 20)
        
        os.unlink(f.name)
    
    def test_config_from_yaml(self):
        """测试从YAML配置文件加载"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as f:
            yaml.dump({"method": "POST", "timeout": 20}, f)
        
        config = Config.from_file(f.name)
        self.assertEqual(config.method, "POST")
        self.assertEqual(config.timeout, 20)
        
        os.unlink(f.name)

class TestRequestor(unittest.TestCase):
    """请求模块测试"""
    
    def setUp(self):
        self.config = Config()
        self.logger = MagicMock()
        self.requestor = Requestor(self.config, self.logger)
    
    def test_session_creation(self):
        """测试会话创建"""
        self.assertIsNotNone(self.requestor.session)
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request):
        """测试成功请求"""
        mock_response = MagicMock()
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.is_permanent_redirect = False
        mock_response.headers = {
            "Content-Length": "1024",
            "Server": "nginx",
            "Content-Type": "text/html"
        }
        mock_request.return_value = mock_response
        
        result = self.requestor.make_request("https://example.com")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["content_length"], 1024)
        self.assertEqual(result["headers"]["server"], "nginx")
        self.assertIsNone(result["error"])
    
    @patch('requests.Session.request')
    def test_make_request_timeout(self, mock_request):
        """测试超时请求"""
        from requests.exceptions import Timeout
        mock_request.side_effect = Timeout
        
        result = self.requestor.make_request("https://example.com")
        self.assertEqual(result["error"], "请求超时")
        self.assertTrue(result["timeout"])

class TestDownloader(unittest.TestCase):
    """下载模块测试"""
    
    def setUp(self):
        self.config = Config()
        self.logger = MagicMock()
        self.downloader = Downloader(self.config, self.logger)
    
    def test_get_filename(self):
        """测试文件名提取"""
        response = MagicMock()
        response.headers = {}
        
        filename = self.downloader._get_filename(response, "https://example.com/file.txt")
        self.assertEqual(filename, "file.txt")
        
        filename = self.downloader._get_filename(response, "https://example.com/")
        self.assertTrue(filename.startswith("download_"))

class TestExporters(unittest.TestCase):
    """导出模块测试"""
    
    def test_json_export(self):
        """测试JSON导出"""
        config = Config(output_file="test.json")
        exporter = JSONExporter(config)
        
        results = [{"url": "https://example.com", "status_code": 200}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_file = os.path.join(tmpdir, "test.json")
            exporter.export(results)
            
            self.assertTrue(os.path.exists(config.output_file))
            with open(config.output_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(len(data), 1)
    
    def test_csv_export(self):
        """测试CSV导出"""
        config = Config(output_file="test.csv")
        exporter = CSVExporter(config)
        
        results = [{"url": "https://example.com", "status_code": 200, "response_time": 0.5, "redirected": False, "timeout": False, "content_length": 1024, "headers": {"Server": "nginx"}}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_file = os.path.join(tmpdir, "test.csv")
            exporter.export(results)
            
            self.assertTrue(os.path.exists(config.output_file))
            with open(config.output_file, 'r') as f:
                content = f.read()
                self.assertIn('url', content)
                self.assertIn('final_url', content)
                self.assertIn('status_code', content)
                self.assertIn('elapsed_ms', content)
                self.assertIn('redirected', content)
                self.assertIn('timed_out', content)
                self.assertIn('content_length', content)
                self.assertIn('headers_summary', content)
    
    def test_json_export_fields(self):
        """测试JSON导出字段"""
        config = Config(output_file="test.json")
        exporter = JSONExporter(config)
        
        results = [{"url": "https://example.com", "status_code": 200, "response_time": 0.5, "redirected": False, "timeout": False, "content_length": 1024, "headers": {"Server": "nginx"}}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_file = os.path.join(tmpdir, "test.json")
            exporter.export(results)
            
            self.assertTrue(os.path.exists(config.output_file))
            with open(config.output_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]['url'], 'https://example.com')
                self.assertEqual(data[0]['elapsed_ms'], 500)
                self.assertEqual(data[0]['status_code'], 200)
                self.assertEqual(data[0]['redirected'], False)
                self.assertEqual(data[0]['timed_out'], False)
                self.assertEqual(data[0]['content_length'], 1024)
                self.assertEqual(data[0]['headers_summary'], 'Server: nginx')

class TestRunner(unittest.TestCase):
    """运行器模块测试"""
    
    def setUp(self):
        self.config = Config()
        self.logger = MagicMock()
        self.runner = Runner(self.config, self.logger)
    
    def test_read_urls(self):
        """测试读取URL文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("https://example.com\n")
            f.write("# 这是注释\n")
            f.write("https://example.org\n")
        
        self.config.input_file = f.name
        urls = self.runner._read_urls()
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://example.com")
        
        os.unlink(f.name)

if __name__ == '__main__':
    unittest.main()