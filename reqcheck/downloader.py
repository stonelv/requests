import os
import time
import requests
from typing import Optional, Dict, Any
from tqdm import tqdm
from .config import Config

class Downloader:
    """文件下载器类"""
    
    def __init__(self, config: Config, logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        
        # 配置代理
        if self.config.proxies:
            self.session.proxies = self.config.proxies
        
        # 设置默认headers
        if self.config.headers:
            self.session.headers.update(self.config.headers)
        
        # 创建下载目录
        os.makedirs(self.config.download_dir, exist_ok=True)
    
    def _get_filename(self, response: requests.Response, url: str) -> str:
        """从响应头或URL中获取文件名"""
        # 尝试从Content-Disposition获取文件名
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1]
            filename = filename.strip('"').strip("'")
            return filename
        
        # 从URL路径中提取文件名
        filename = url.split('/')[-1]
        if not filename:
            filename = f"download_{int(time.time())}"
        
        return filename
    
    def download_file(self, url: str) -> Dict[str, Any]:
        """下载文件并返回下载信息"""
        result = {
            "url": url,
            "file_path": None,
            "file_size": 0,
            "downloaded_size": 0,
            "download_time": 0.0,
            "success": False,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            with self.session.get(url, stream=True, timeout=self.config.timeout) as response:
                response.raise_for_status()
                
                # 获取文件大小
                file_size = int(response.headers.get('Content-Length', 0))
                result["file_size"] = file_size
                
                # 获取文件名
                filename = self._get_filename(response, url)
                file_path = os.path.join(self.config.download_dir, filename)
                
                # 处理重名文件
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(file_path):
                    file_path = os.path.join(self.config.download_dir, f"{base}_{counter}{ext}")
                    counter += 1
                
                result["file_path"] = file_path
                
                # 下载文件并显示进度条
                downloaded_size = 0
                with open(file_path, 'wb') as f, tqdm(
                    total=file_size,
                    unit='B',
                    unit_scale=True,
                    desc=filename,
                    leave=False
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            pbar.update(len(chunk))
                
                result["downloaded_size"] = downloaded_size
                result["success"] = True
                
        except requests.exceptions.Timeout:
            result["error"] = "下载超时"
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP错误: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"连接错误: {str(e)}"
        except Exception as e:
            result["error"] = f"下载失败: {str(e)}"
        finally:
            result["download_time"] = time.time() - start_time
        
        return result
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()