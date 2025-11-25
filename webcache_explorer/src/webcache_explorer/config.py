"""Configuration management for WebCache Explorer."""

import logging
import os
from pathlib import Path
from typing import Dict, Any
import toml


class Config:
    """Configuration manager for WebCache Explorer."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._setup_logging()
    
    def _find_config_file(self) -> str:
        """Find configuration file in standard locations."""
        possible_paths = [
            "config/config.toml",
            "../config/config.toml",
            "../../config/config.toml",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Create default config if none found
        return "config/config.toml"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return toml.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logging.warning(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'fetching': {
                'max_workers': 10,
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1
            },
            'storage': {
                'data_dir': 'data',
                'index_file': 'index.json',
                'max_content_size': 10485760  # 10MB
            },
            'processing': {
                'max_search_results': 50,
                'min_keyword_length': 2
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'webcache.log'
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = log_config.get('file', 'webcache.log')
        
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            section: Configuration section.
            key: Configuration key. If None, returns entire section.
            default: Default value if key not found.
            
        Returns:
            Configuration value.
        """
        section_data = self.config.get(section, {})
        if key is None:
            return section_data
        return section_data.get(key, default)
    
    @property
    def max_workers(self) -> int:
        """Maximum number of worker threads."""
        return self.get('fetching', 'max_workers', 10)
    
    @property
    def timeout(self) -> int:
        """Request timeout in seconds."""
        return self.get('fetching', 'timeout', 30)
    
    @property
    def max_retries(self) -> int:
        """Maximum number of retries."""
        return self.get('fetching', 'max_retries', 3)
    
    @property
    def retry_delay(self) -> int:
        """Delay between retries in seconds."""
        return self.get('fetching', 'retry_delay', 1)
    
    @property
    def data_dir(self) -> str:
        """Data directory path."""
        return self.get('storage', 'data_dir', 'data')
    
    @property
    def index_file(self) -> str:
        """Index file path."""
        return self.get('storage', 'index_file', 'index.json')
    
    @property
    def max_content_size(self) -> int:
        """Maximum content size in bytes."""
        return self.get('storage', 'max_content_size', 10485760)
    
    @property
    def max_search_results(self) -> int:
        """Maximum number of search results."""
        return self.get('processing', 'max_search_results', 50)
    
    @property
    def min_keyword_length(self) -> int:
        """Minimum keyword length for search."""
        return self.get('processing', 'min_keyword_length', 2)