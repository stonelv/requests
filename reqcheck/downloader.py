"""File downloader with progress bar"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from tqdm import tqdm

from .logging_utils import get_logger
from .requestor import Requestor

logger = get_logger(__name__)


class Downloader:
    """Handles file downloading with progress tracking"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.requestor = Requestor(
            method="GET",
            timeout=config["timeout"],
            max_retries=config["max_retries"],
            retry_delay=config["retry_delay"],
            proxy=config["proxy"],
            headers=config["headers"],
            cookies=config["cookies"]
        )
        self.download_dir = Path(config["download_dir"])
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)
        
        if not filename:
            filename = "index.html"
        
        # Add random suffix if file exists
        counter = 1
        original_filename = filename
        while (self.download_dir / filename).exists():
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{counter}{ext}"
            counter += 1
        
        return filename
    
    def download(self, url: str, show_progress: bool = True) -> Dict[str, Any]:
        """Download file with progress bar"""
        filename = self.get_filename_from_url(url)
        output_path = self.download_dir / filename
        
        result = {
            "url": url,
            "filename": str(output_path),
            "success": False,
            "error": None,
            "content_length": None,
            "elapsed": None
        }
        
        try:
            response = self.requestor.session.get(
                url,
                timeout=self.config["timeout"],
                headers=self.config["headers"],
                cookies=self.config["cookies"],
                stream=True
            )
            response.raise_for_status()
            
            # Get content length
            content_length = None
            if "Content-Length" in response.headers:
                try:
                    content_length = int(response.headers["Content-Length"])
                    result["content_length"] = content_length
                except ValueError:
                    pass
            
            # Download with progress bar
            if show_progress and content_length:
                with tqdm(
                    total=content_length,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=filename,
                    leave=False
                ) as progress:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(len(chunk))
            else:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            result["success"] = True
            logger.info(f"Downloaded: {url} -> {output_path}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Download failed: {url} -> {output_path}")
            
        return result
    
    def close(self) -> None:
        """Close the requestor session"""
        self.requestor.close()