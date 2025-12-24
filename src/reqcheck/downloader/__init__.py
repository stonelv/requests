import os
import requests
import hashlib
from typing import Optional
from ..config import config
from ..logging_utils import get_logger

class Downloader:
    def __init__(self):
        self.logger = get_logger()
        self.download_dir = config.download_dir or "./downloads"
        
        # Ensure download directory exists
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            self.logger.info(f"Created download directory: {self.download_dir}")
    
    def get_filename_from_url(self, url: str) -> str:
        # Extract filename from URL
        filename = url.split("/")[-1]
        if not filename or filename in ["", "/"]:
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"download_{url_hash}"
        return filename
    
    def download_file(self, url: str) -> str:
        try:
            self.logger.debug(f"Downloading file from URL: {url}")
            response = requests.get(url, stream=True, timeout=config.timeout)
            response.raise_for_status()
            
            filename = self.get_filename_from_url(url)
            filepath = os.path.join(self.download_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                self.logger.warning(f"File already exists: {filepath}. Skipping download.")
                return filepath
            
            # Download with progress tracking
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # Calculate progress
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.logger.debug(f"Download progress: {progress:.2f}% for {filename}")
            
            self.logger.info(f"Successfully downloaded: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to download file from URL: {url}. Error: {str(e)}")
            raise
    
    def download_from_result(self, result) -> Optional[str]:
        if not result.success or not result.final_url:
            self.logger.error(f"Cannot download from unsuccessful result for URL: {result.url}")
            return None
        
        try:
            return self.download_file(result.final_url)
        except Exception as e:
            self.logger.error(f"Failed to download from result for URL: {result.url}. Error: {str(e)}")
            return None

def create_downloader() -> Downloader:
    return Downloader()