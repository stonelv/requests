import asyncio
import aiohttp
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class Runner:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.concurrent = config.concurrent
        self.requestor = None
        self.downloader = None
        
    def _read_urls(self) -> List[str]:
        if not self.config.input_file:
            return []
        
        urls = []
        with open(self.config.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        
        return urls

    async def _process_url(self, session, url: str) -> Dict[str, Any]:
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
            async with session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=True
            ) as response:
                result['status_code'] = response.status
                result['final_url'] = str(response.url)
                result['duration'] = time.time() - start_time
                result['redirected'] = len(response.history) > 0
                
                if 'Content-Length' in response.headers:
                    result['content_length'] = int(response.headers['Content-Length'])
                
                # 保存关键响应头
                key_headers = ['Content-Type', 'Server', 'Date', 'Cache-Control']
                result['headers'] = {k: v for k, v in response.headers.items() if k in key_headers}
                
                # 保存响应内容（如果是下载模式）
                if self.config.download_mode:
                    result['content'] = await response.read()
                    
        except asyncio.TimeoutError:
            result['timed_out'] = True
            result['error'] = 'Timeout'
        except aiohttp.ClientError as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
        
        return result

    async def _run_async(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        
        # 配置会话
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(limit=self.concurrent)
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': self.config.user_agent}
        ) as session:
            # 设置代理
            if self.config.proxy:
                session.proxy = self.config.proxy
            
            # 创建任务列表
            tasks = [self._process_url(session, url) for url in urls]
            
            # 显示进度条
            with tqdm(total=len(tasks), desc='处理URL', unit='url') as pbar:
                for future in asyncio.as_completed(tasks):
                    result = await future
                    results.append(result)
                    pbar.update(1)
        
        return results

    def run(self) -> List[Dict[str, Any]]:
        urls = self._read_urls()
        if not urls:
            self.logger.warning('没有找到有效的URL')
            return []
        
        self.logger.info(f'开始处理 {len(urls)} 个URL，并发数: {self.concurrent}')
        
        try:
            # 运行异步任务
            results = asyncio.run(self._run_async(urls))
            
            # 下载模式下保存文件
            if self.config.download_mode:
                from .downloader import Downloader
                with Downloader(self.config) as downloader:
                    for result in results:
                        if 'content' in result and result['content']:
                            try:
                                file_path = downloader.save_content(
                                    result['url'],
                                    result['content'],
                                    result['headers']
                                )
                                if file_path:
                                    result['downloaded_file'] = file_path
                                    self.logger.info(f'已保存: {file_path}')
                            except Exception as e:
                                self.logger.error(f'保存文件失败: {e}')
            
            return results
        except Exception as e:
            self.logger.error(f'运行出错: {e}')
            return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
