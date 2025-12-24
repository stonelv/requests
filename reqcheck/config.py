import argparse
import json
import sys
from typing import Dict, Optional, List

class Config:
    def __init__(self):
        self.input_file: Optional[str] = None
        self.output_file: Optional[str] = None
        self.output_format: str = 'csv'
        self.concurrent: int = 10
        self.timeout: int = 30
        self.retries: int = 3
        self.backoff_factor: float = 0.5
        self.proxy: Optional[str] = None
        self.headers: Optional[Dict[str, str]] = None
        self.user_agent: str = 'reqcheck/1.0'
        self.download_mode: bool = False
        self.download_dir: str = 'downloads'
        self.verbose: bool = False
        self.debug: bool = False

    @classmethod
    def from_args(cls) -> 'Config':
        parser = argparse.ArgumentParser(description='reqcheck - 批量URL检查工具')
        
        parser.add_argument('-i', '--input', help='URL列表文件路径')
        parser.add_argument('-o', '--output', help='输出文件路径')
        parser.add_argument('-f', '--format', choices=['csv', 'json'], default='csv', help='输出格式')
        parser.add_argument('-c', '--concurrent', type=int, default=10, help='并发请求数')
        parser.add_argument('-t', '--timeout', type=int, default=30, help='超时时间（秒）')
        parser.add_argument('-r', '--retries', type=int, default=3, help='重试次数')
        parser.add_argument('-b', '--backoff', type=float, default=0.5, help='指数退避因子')
        parser.add_argument('-p', '--proxy', help='代理服务器（http://host:port）')
        parser.add_argument('-H', '--header', action='append', help='自定义请求头（格式: Key: Value）')
        parser.add_argument('-u', '--user-agent', help='自定义User-Agent')
        parser.add_argument('-d', '--download', action='store_true', help='下载模式，保存响应内容')
        parser.add_argument('-D', '--download-dir', default='downloads', help='下载文件保存目录')
        parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
        parser.add_argument('-V', '--debug', action='store_true', help='调试模式')
        
        args = parser.parse_args()
        
        config = cls()
        config.input_file = args.input
        config.output_file = args.output
        config.output_format = args.format
        config.concurrent = args.concurrent
        config.timeout = args.timeout
        config.retries = args.retries
        config.backoff_factor = args.backoff
        config.proxy = args.proxy
        config.download_mode = args.download
        config.download_dir = args.download_dir
        config.verbose = args.verbose
        config.debug = args.debug
        
        if args.user_agent:
            config.user_agent = args.user_agent
        
        if args.header:
            config.headers = {}
            for header in args.header:
                if ':' in header:
                    key, value = header.split(':', 1)
                    config.headers[key.strip()] = value.strip()
        
        return config

    @classmethod
    def from_config_file(cls, config_file: str) -> 'Config':
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        config = cls()
        config.input_file = config_data.get('input_file')
        config.output_file = config_data.get('output_file')
        config.output_format = config_data.get('output_format', 'csv')
        config.concurrent = config_data.get('concurrent', 10)
        config.timeout = config_data.get('timeout', 30)
        config.retries = config_data.get('retries', 3)
        config.backoff_factor = config_data.get('backoff_factor', 0.5)
        config.proxy = config_data.get('proxy')
        config.headers = config_data.get('headers')
        config.user_agent = config_data.get('user_agent', 'reqcheck/1.0')
        config.download_mode = config_data.get('download_mode', False)
        config.download_dir = config_data.get('download_dir', 'downloads')
        config.verbose = config_data.get('verbose', False)
        config.debug = config_data.get('debug', False)
        
        return config

    def validate(self) -> bool:
        if not self.input_file:
            print('错误：必须提供输入文件路径', file=sys.stderr)
            return False
        
        if self.concurrent <= 0:
            print('错误：并发请求数必须大于0', file=sys.stderr)
            return False
        
        if self.timeout <= 0:
            print('错误：超时时间必须大于0', file=sys.stderr)
            return False
        
        if self.retries < 0:
            print('错误：重试次数不能为负数', file=sys.stderr)
            return False
        
        if self.backoff_factor < 0:
            print('错误：退避因子不能为负数', file=sys.stderr)
            return False
        
        return True

    def to_dict(self) -> Dict:
        return {
            'input_file': self.input_file,
            'output_file': self.output_file,
            'output_format': self.output_format,
            'concurrent': self.concurrent,
            'timeout': self.timeout,
            'retries': self.retries,
            'backoff_factor': self.backoff_factor,
            'proxy': self.proxy,
            'headers': self.headers,
            'user_agent': self.user_agent,
            'download_mode': self.download_mode,
            'download_dir': self.download_dir,
            'verbose': self.verbose,
            'debug': self.debug
        }

    def __repr__(self) -> str:
        return f'Config({self.to_dict()})'