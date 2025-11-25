import os
import tomllib
from typing import Dict, Any, Optional

class Config:
    """Configuration class for WebCache Explorer."""
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = config_path
        self.data_dir: str = "data"
        self.concurrency: int = 5
        self.timeout: int = 10
        self.retries: int = 3
        
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from TOML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'rb') as f:
                config_data = tomllib.load(f)
                
            self.data_dir = config_data.get("data_dir", self.data_dir)
            self.concurrency = config_data.get("concurrency", self.concurrency)
            self.timeout = config_data.get("timeout", self.timeout)
            self.retries = config_data.get("retries", self.retries)

def load_config(config_path: str = "config.toml") -> Config:
    """Load configuration from file and return Config object."""
    return Config(config_path)
