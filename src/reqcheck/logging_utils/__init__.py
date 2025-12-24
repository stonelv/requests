import logging
import sys
from typing import Optional

class Logger:
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet
        self.logger = logging.getLogger("reqcheck")
        self._setup_logging()
    
    def _setup_logging(self):
        # Remove existing handlers to avoid duplicate logging
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Set log level
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        elif self.quiet:
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        self.logger.addHandler(handler)
        
        # Disable propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str):
        if self.verbose:
            self.logger.debug(message)
    
    def info(self, message: str):
        if not self.quiet:
            self.logger.info(message)
    
    def warning(self, message: str):
        if not self.quiet:
            self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)

# Singleton instance
logger: Optional[Logger] = None

def init_logger(verbose: bool = False, quiet: bool = False):
    global logger
    logger = Logger(verbose, quiet)
    return logger

def get_logger() -> Logger:
    if not logger:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")
    return logger