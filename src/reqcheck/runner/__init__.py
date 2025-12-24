import asyncio
import time
from typing import List, Callable, Awaitable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from ..config import config
from ..logging_utils import get_logger
from ..requestor import RequestResult, create_requestor
from ..downloader import create_downloader
from ..exporters import create_exporter

class Runner:
    def __init__(self):
        self.logger = get_logger()
        self.requestor = create_requestor()
        self.downloader = create_downloader()
        self.exporter = create_exporter()
        self.concurrency = config.concurrency
        self.urls = config.urls
        self.urls_file = config.urls_file
    
    def read_urls_from_file(self) -> List[str]:
        if not self.urls_file:
            return []
        
        try:
            with open(self.urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            self.logger.info(f"Successfully read {len(urls)} URLs from {self.urls_file}")
            return urls
        except Exception as e:
            self.logger.error(f"Failed to read URLs from file: {str(e)}")
            raise
    
    def collect_urls(self) -> List[str]:
        urls = []
        
        # Add URLs from command line
        if self.urls:
            urls.extend(self.urls)
        
        # Add URLs from file
        if self.urls_file:
            urls.extend(self.read_urls_from_file())
        
        if not urls:
            self.logger.error("No URLs provided. Please specify URLs via command line or --urls-file.")
            raise ValueError("No URLs provided")
        
        # Remove duplicates
        unique_urls = list(set(urls))
        if len(unique_urls) != len(urls):
            self.logger.warning(f"Removed {len(urls) - len(unique_urls)} duplicate URLs")
        
        return unique_urls
    
    def run(self) -> List[RequestResult]:
        urls = self.collect_urls()
        self.logger.info(f"Starting to check {len(urls)} URLs with concurrency {self.concurrency}")
        
        results = []
        total = len(urls)
        successful = 0
        failed = 0
        timed_out = 0
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(self.requestor.send_request, url): url for url in urls}
            
            with tqdm(total=total, desc="Checking URLs", unit="url") as pbar:
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.success:
                            successful += 1
                            if result.timed_out:
                                timed_out += 1
                        else:
                            failed += 1
                        
                        # Update progress bar
                        pbar.update(1)
                        
                        # Log result
                        if result.success:
                            self.logger.info(f"Success: {url} - Status: {result.status_code}, Time: {result.elapsed:.2f}s")
                        else:
                            self.logger.error(f"Failed: {url} - Error: {result.error}")
                        
                        # Download if needed
                        if config.download_mode and result.success:
                            try:
                                self.downloader.download_from_result(result)
                            except Exception as e:
                                self.logger.error(f"Failed to download {url}: {str(e)}")
                    except Exception as e:
                        self.logger.error(f"Exception while processing {url}: {str(e)}")
                        failed += 1
                        result = RequestResult(url=url)
                        result.status_code = None
                        result.final_url = None
                        result.elapsed = 0
                        result.redirected = False
                        result.timed_out = False
                        result.content_length = 0
                        result.headers = {}
                        result.error = str(e)
                        result.success = False
                        results.append(result)
        
        # Export results
        if self.exporter:
            try:
                self.exporter.export(results)
            except Exception as e:
                self.logger.error(f"Failed to export results: {str(e)}")
        
        # Print summary
        self.logger.info("\n" + "="*50)
        self.logger.info(f"Summary:")
        self.logger.info(f"Total URLs: {total}")
        self.logger.info(f"Successful: {successful}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Timed out: {timed_out}")
        self.logger.info("="*50)
        
        return results

def create_runner() -> Runner:
    return Runner()