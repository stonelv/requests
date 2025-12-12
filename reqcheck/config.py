"""Configuration management"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class Config:
    """Main configuration class"""
    urls_file: Path
    output_file: Optional[Path] = None
    method: str = "GET"
    timeout: float = 10.0
    max_retries: int = 3
    retry_delay: float = 1.0
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    download: bool = False
    download_dir: Path = Path("downloads")
    concurrency: int = 10
    verbose: bool = False
    show_progress: bool = True

    @classmethod
    def from_args(cls, args):
        """Create Config from command-line arguments"""
        headers = None
        if args.headers:
            with open(args.headers, "r") as f:
                headers = json.load(f)
        
        cookies = None
        if args.cookies:
            with open(args.cookies, "r") as f:
                cookies = json.load(f)
        
        return cls(
            urls_file=Path(args.urls),
            output_file=Path(args.output) if args.output else None,
            method=args.method,
            timeout=args.timeout,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
            proxy=args.proxy,
            headers=headers,
            cookies=cookies,
            download=args.download,
            download_dir=Path(args.download_dir),
            concurrency=args.concurrency,
            verbose=args.verbose,
            show_progress=not args.no_progress
        )

    def validate(self) -> None:
        """Validate configuration"""
        if not self.urls_file.exists():
            raise ValueError(f"URLs file not found: {self.urls_file}")
        
        if self.download and not self.download_dir.exists():
            self.download_dir.mkdir(parents=True, exist_ok=True)
        
        if self.concurrency < 1:
            raise ValueError("Concurrency must be at least 1")
        
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

    def __post_init__(self):
        """Post-initialization validation"""
        self.validate()