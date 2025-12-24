import unittest
import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open

# 添加reqcheck目录到Python路径
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reqcheck.config import Config
from reqcheck.logging_utils import Logger
from reqcheck.requestor import Requestor
from reqcheck.downloader import Downloader
from reqcheck.exporters import Exporter
from reqcheck.runner import Runner

class TestConfig(unittest.TestCase):
    """测试配置模块"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        self.assertEqual(config.concurrent, 10)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.retries, 3)
        self.assertEqual(config.backoff_factor, 0.5)
        self.assertFalse(config.download_mode)

    def test_config_validation(self):
        """测试配置验证"""
        config = Config()
        config.input_file = 'test.txt'
        config.concurrent = 0
        self.assertFalse(config.validate())
        
        config.concurrent = 10
        config.timeout = 0
        self.assertFalse(config.validate())
        
        config.timeout = 30
        config.retries = -1
        self.assertFalse(config.validate())
        
        config.retries = 3
        config.backoff_factor = -0.5
        self.assertFalse(config.validate())
        
        config.backoff_factor = 0.5
        self.assertTrue(config.validate())

class TestLogger(unittest.TestCase):
    """测试日志工具模块"""
    
    def test_logger_init(self):
        """测试日志初始化"""
        logger = Logger(verbose=True, debug=False)
        self.assertTrue(logger.verbose_enabled())
        self.assertFalse(logger.debug_enabled())
        
        logger = Logger(verbose=False, debug=True)
        self.assertFalse(logger.verbose_enabled())
        self.assertTrue(logger.debug_enabled())

    def test_logger_methods(self):
        """测试日志方法"""
        logger = Logger(verbose=True, debug=True)
        # 测试日志方法不抛出异常
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')
        logger.critical('critical message')

class TestRequestor(unittest.TestCase):
    """测试请求器模块"""
    
    @patch('requests.Session')
    def test_requestor_init(self, mock_session):
        """测试请求器初始化"""
        config = Config()
        config.proxy = 'http://proxy:8080'
        config.user_agent = 'test-agent'
        
        requestor = Requestor(config)
        
        # 验证会话配置
        mock_session.return_value.mount.assert_called()
        self.assertEqual(mock_session.return_value.proxies, {
            'http': 'http://proxy:8080',
            'https': 'http://proxy:8080'
        })
        mock_session.return_value.headers.__setitem__.assert_called_with('User-Agent', 'test-agent')

class TestDownloader(unittest.TestCase):
    """测试下载器模块"""
    
    def test_get_filename(self):
        """测试文件名生成"""
        config = Config()
        downloader = Downloader(config)
        
        # 测试正常URL
        filename = downloader.get_filename('https://example.com/file.txt')
        self.assertEqual(filename, 'file.txt')
        
        # 测试没有扩展名的URL
        filename = downloader.get_filename('https://example.com/file')
        self.assertEqual(filename, 'unknown.bin')
        
        # 测试内容类型
        filename = downloader.get_filename('https://example.com/file', 'text/html')
        self.assertEqual(filename, 'unknown.html')

class TestExporter(unittest.TestCase):
    """测试导出器模块"""
    
    def test_export_csv(self):
        """测试CSV导出"""
        config = Config()
        config.output_file = 'test.csv'
        config.output_format = 'csv'
        
        results = [
            {
                'url': 'https://example.com',
                'status_code': 200,
                'final_url': 'https://example.com',
                'duration': 1.5,
                'redirected': False,
                'timed_out': False,
                'content_length': 1000,
                'headers': {'Content-Type': 'text/html'},
                'error': None,
                'retries': 0
            }
        ]
        
        exporter = Exporter(config)
        output_file = exporter.export(results)
        
        self.assertEqual(output_file, 'test.csv')
        self.assertTrue(os.path.exists('test.csv'))
        
        # 清理
        os.remove('test.csv')

    def test_export_json(self):
        """测试JSON导出"""
        config = Config()
        config.output_file = 'test.json'
        config.output_format = 'json'
        
        results = [
            {
                'url': 'https://example.com',
                'status_code': 200,
                'final_url': 'https://example.com',
                'duration': 1.5,
                'redirected': False,
                'timed_out': False,
                'content_length': 1000,
                'headers': {'Content-Type': 'text/html'},
                'error': None,
                'retries': 0
            }
        ]
        
        exporter = Exporter(config)
        output_file = exporter.export(results)
        
        self.assertEqual(output_file, 'test.json')
        self.assertTrue(os.path.exists('test.json'))
        
        # 验证JSON内容
        with open('test.json', 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status_code'], 200)
        
        # 清理
        os.remove('test.json')

class TestRunner(unittest.TestCase):
    """测试运行器模块"""
    
    def test_read_urls(self):
        """测试读取URL列表"""
        config = Config()
        config.input_file = 'urls.txt'
        logger = Logger()
        
        runner = Runner(config, logger)
        
        # 创建临时URL文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('https://example.com\n')
            f.write('https://example.org\n')
            f.write('# comment\n')
            f.write('   https://example.net   \n')
        
        config.input_file = f.name
        urls = runner._read_urls()
        
        self.assertEqual(len(urls), 3)
        self.assertEqual(urls[0], 'https://example.com')
        self.assertEqual(urls[1], 'https://example.org')
        self.assertEqual(urls[2], 'https://example.net')
        
        # 清理
        os.unlink(f.name)

if __name__ == '__main__':
    unittest.main()
