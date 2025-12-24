import argparse
import configparser
import os
from typing import Optional, Dict, Any

class Config:
    def __init__(self):
        self.urls: List[str] = []
        self.urls_file: Optional[str] = None
        self.output_file: Optional[str] = None
        self.output_format: str = "json"
        self.concurrency: int = 10
        self.timeout: int = 10
        self.retries: int = 3
        self.retry_delay: float = 1.0
        self.retry_backoff: float = 2.0
        self.proxy: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.download_dir: Optional[str] = None
        self.download_mode: bool = False
        self.verbose: bool = False
        self.quiet: bool = False

    def parse_args(self):
        parser = argparse.ArgumentParser(description="reqcheck - A command-line tool for checking URLs")
        
        # Basic options
        parser.add_argument("urls", nargs="*", help="URLs to check (can be multiple)")
        parser.add_argument("-f", "--file", help="File containing URLs to check (one per line)")
        parser.add_argument("-o", "--output", help="Output file path")
        parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
        parser.add_argument("-c", "--concurrency", type=int, default=10, help="Number of concurrent requests (default: 10)")
        parser.add_argument("-r", "--retries", type=int, default=3, help="Number of retries for failed requests (default: 3)")
        parser.add_argument("-d", "--delay", type=float, default=1.0, help="Initial retry delay in seconds (default: 1.0)")
        parser.add_argument("-b", "--backoff", type=float, default=2.0, help="Retry backoff factor (default: 2.0)")
        parser.add_argument("-p", "--proxy", help="Proxy URL (e.g., http://proxy.example.com:8080)")
        parser.add_argument("-H", "--header", action="append", help="Custom headers (e.g., 'Authorization: Bearer token')")
        
        # Output options
        parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format (default: json)")
        
        # Download mode
        parser.add_argument("--download", action="store_true", help="Download mode: save responses to files")
        parser.add_argument("--download-dir", help="Directory to save downloaded files (default: ./downloads)")
        
        # Logging options
        parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
        parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode: only show errors")
        
        args = parser.parse_args()
        
        # Update config from command line arguments
        if args.urls:
            self.urls = args.urls
        if args.file:
            self.urls_file = args.file
        if args.output:
            self.output_file = args.output
        if args.timeout:
            self.timeout = args.timeout
        if args.concurrency:
            self.concurrency = args.concurrency
        if args.retries:
            self.retries = args.retries
        if args.delay:
            self.retry_delay = args.delay
        if args.backoff:
            self.retry_backoff = args.backoff
        if args.proxy:
            self.proxy = args.proxy
        if args.format:
            self.output_format = args.format
        if args.download:
            self.download_mode = True
        if args.download_dir:
            self.download_dir = args.download_dir
        if args.verbose:
            self.verbose = True
        if args.quiet:
            self.quiet = True
        
        # Parse headers
        if args.header:
            for header in args.header:
                key, value = header.split(":", 1)
                self.headers[key.strip()] = value.strip()
        
        return args
    
    def parse_config(self, config_file: str):
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if "reqcheck" in config:
            section = config["reqcheck"]
            self.urls_file = section.get("urls_file", self.urls_file)
            self.output_file = section.get("output_file", self.output_file)
            self.output_format = section.get("output_format", self.output_format)
            self.concurrency = section.getint("concurrency", self.concurrency)
            self.timeout = section.getint("timeout", self.timeout)
            self.retries = section.getint("retries", self.retries)
            self.retry_delay = section.getfloat("retry_delay", self.retry_delay)
            self.retry_backoff = section.getfloat("retry_backoff", self.retry_backoff)
            self.proxy = section.get("proxy", self.proxy)
            self.download_dir = section.get("download_dir", self.download_dir)
            self.download_mode = section.getboolean("download_mode", self.download_mode)
            self.verbose = section.getboolean("verbose", self.verbose)
            self.quiet = section.getboolean("quiet", self.quiet)
            
            # Parse headers
            if "headers" in section:
                headers_str = section["headers"]
                for header in headers_str.split("\n"):
                    header = header.strip()
                    if header and ":" in header:
                        key, value = header.split(":", 1)
                        self.headers[key.strip()] = value.strip()
    
    def validate(self):
        if not self.urls_file:
            raise ValueError("URLs file must be specified with --file or in config")
        if not os.path.exists(self.urls_file):
            raise FileNotFoundError(f"URLs file not found: {self.urls_file}")
        if self.download_mode and not self.download_dir:
            self.download_dir = "./downloads"
            os.makedirs(self.download_dir, exist_ok=True)
        if self.download_dir and not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)
        return True

# Singleton instance
config = Config()