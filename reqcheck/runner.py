import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from .config import Config
from .requestor import Requestor
from .downloader import Downloader
from .logging_utils import log_success, log_error

class Runner:
    """任务运行器类"""
    
    def __init__(self, config: Config, logger):
        self.config = config
        self.logger = logger
        self.requestor = Requestor(config, logger)
        self.downloader = Downloader(config, logger) if config.download else None
        
        # 统计信息
        self.total_urls = 0
        self.success_count = 0
        self.error_count = 0
        self.redirect_count = 0
        self.timeout_count = 0
        
    def _read_urls(self) -> List[str]:
        """从输入文件读取URL列表"""
        urls = []
        if not self.config.input_file:
            return urls
        
        with open(self.config.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        
        self.total_urls = len(urls)
        self.logger.info(f"共读取到 {self.total_urls} 个URL")
        return urls
    
    def _process_url(self, url: str) -> Dict[str, Any]:
        """处理单个URL"""
        if self.config.download:
            return self._download_url(url)
        else:
            return self._check_url(url)
    
    def _check_url(self, url: str) -> Dict[str, Any]:
        """检查URL"""
        result = self.requestor.make_request(url)
        
        # 更新统计信息
        if result.get('error'):
            self.error_count += 1
            log_error(self.logger, url, result['error'])
        else:
            status_code = result.get('status_code')
            self.success_count += 1
            log_success(self.logger, url, status_code)
            
            if result.get('redirected'):
                self.redirect_count += 1
            
            if result.get('timeout'):
                self.timeout_count += 1
        
        return result
    
    def _download_url(self, url: str) -> Dict[str, Any]:
        """下载URL"""
        result = self.downloader.download_file(url)
        
        # 更新统计信息
        if result.get('error'):
            self.error_count += 1
            log_error(self.logger, url, result['error'])
        else:
            self.success_count += 1
            self.logger.info(f"✓ {url} - 下载完成: {result['file_path']}")
        
        return result
    
    def run(self) -> List[Dict[str, Any]]:
        """运行批量任务"""
        urls = self._read_urls()
        
        if not urls:
            self.logger.warning("未找到任何URL")
            return []
        
        results = []
        
        # 使用线程池处理并发请求
        with ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
            # 提交所有任务
            futures = {executor.submit(self._process_url, url): url for url in urls}
            
            # 处理结果
            with tqdm(total=len(futures), desc="处理进度", unit="URL") as pbar:
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        url = futures[future]
                        error_result = {
                            "url": url,
                            "error": f"任务执行异常: {str(e)}"
                        }
                        results.append(error_result)
                        log_error(self.logger, url, error_result['error'])
                    finally:
                        pbar.update(1)
        
        # 打印统计信息
        self._print_statistics()
        
        return results
    
    def _print_statistics(self) -> None:
        """打印统计信息"""
        self.logger.info("\n=== 统计信息 ===")
        self.logger.info(f"总URL数: {self.total_urls}")
        self.logger.info(f"成功: {self.success_count}")
        self.logger.info(f"失败: {self.error_count}")
        self.logger.info(f"重定向: {self.redirect_count}")
        self.logger.info(f"超时: {self.timeout_count}")
        
        if self.total_urls > 0:
            success_rate = (self.success_count / self.total_urls) * 100
            self.logger.info(f"成功率: {success_rate:.2f}%")
    
    def close(self):
        """关闭资源"""
        self.requestor.close()
        if self.downloader:
            self.downloader.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()