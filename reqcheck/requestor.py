import requests
import time
import random
from typing import Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class Requestor:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=config.retries,
            backoff_factor=config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET']
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 配置代理
        if config.proxy:
            self.session.proxies = {
                'http': config.proxy,
                'https': config.proxy
            }
        
        # 配置默认请求头
        self.session.headers['User-Agent'] = config.user_agent
        if config.headers:
            self.session.headers.update(config.headers)

    def request(self, url: str) -> Dict[str, Any]:
        start_time = time.time()
        result = {
            'url': url,
            'status_code': None,
            'final_url': None,
            'duration': 0.0,
            'redirected': False,
            'timed_out': False,
            'content_length': None,
            'headers': {},
            'error': None,
            'retries': 0
        }
        
        try:
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=True
            )
            
            result['status_code'] = response.status_code
            result['final_url'] = response.url
            result['duration'] = time.time() - start_time
            result['redirected'] = len(response.history) > 0
            
            if 'Content-Length' in response.headers:
                result['content_length'] = int(response.headers['Content-Length'])
            
            # 保存关键响应头
            key_headers = ['Content-Type', 'Server', 'Date', 'Cache-Control']
            result['headers'] = {k: v for k, v in response.headers.items() if k in key_headers}
            
            # 保存响应内容（如果是下载模式）
            if self.config.download_mode:
                result['content'] = response.content
            
        except requests.exceptions.Timeout:
            result['timed_out'] = True
            result['error'] = 'Timeout'
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
        
        return result

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
