import time
import random
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import Config
from .logging_utils import log_debug

class Requestor:
    """HTTP请求处理类"""
    
    def __init__(self, config: Config, logger):
        self.config = config
        self.logger = logger
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试策略的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # 设置默认超时
        session.timeout = self.config.timeout
        
        # 设置代理
        if self.config.proxies:
            session.proxies = self.config.proxies
        
        # 设置默认headers
        if self.config.headers:
            session.headers.update(self.config.headers)
        
        # 设置cookies
        if self.config.cookies:
            session.cookies.update(self.config.cookies)
        
        return session
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算指数退避延迟"""
        if attempt <= 0:
            return 0.0
        
        delay = self.config.backoff_factor * (2 ** (attempt - 1))
        # 添加随机抖动
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def make_request(self, url: str) -> Dict[str, Any]:
        """发送HTTP请求并返回结果"""
        result = {
            "url": url,
            "final_url": None,
            "status_code": None,
            "error": None,
            "response_time": 0.0,
            "redirected": False,
            "timeout": False,
            "content_length": 0,
            "headers": {},
            "retries": 0
        }
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=self.config.method,
                url=url,
                timeout=self.config.timeout
            )
            
            result["final_url"] = response.url
            result["status_code"] = response.status_code
            result["redirected"] = response.is_redirect or response.is_permanent_redirect
            
            # 获取内容长度
            if "Content-Length" in response.headers:
                result["content_length"] = int(response.headers["Content-Length"])
            
            # 保存响应头摘要
            result["headers"] = {
                "server": response.headers.get("Server", ""),
                "content_type": response.headers.get("Content-Type", ""),
                "last_modified": response.headers.get("Last-Modified", ""),
                "etag": response.headers.get("ETag", "")
            }
            
        except requests.exceptions.Timeout:
            result["error"] = "请求超时"
            result["timeout"] = True
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP错误: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"连接错误: {str(e)}"
        except requests.exceptions.RequestException as e:
            result["error"] = f"请求异常: {str(e)}"
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"
        finally:
            result["response_time"] = time.time() - start_time
        
        return result
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()