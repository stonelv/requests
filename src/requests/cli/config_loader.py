"""
Configuration loader for batch processing in rhttp CLI tool.
"""

import os
import re
from typing import Dict, List, Any, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None


class ConfigLoaderException(Exception):
    """Exception raised when configuration loading fails."""
    pass


class ConfigLoader:
    """Handles loading and processing of batch configuration files."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        
        if yaml is None:
            raise ConfigLoaderException("PyYAML is required for batch processing. Install with: pip install PyYAML")
    
    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigLoaderException(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigLoaderException(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ConfigLoaderException(f"Failed to load configuration: {str(e)}")
        
        if self.config is None:
            raise ConfigLoaderException("Configuration file is empty")
        
        self._validate_config()
        return self.config
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        if not isinstance(self.config, dict):
            raise ConfigLoaderException("Configuration must be a dictionary")
        
        if "requests" not in self.config:
            raise ConfigLoaderException("Configuration must contain 'requests' list")
        
        if not isinstance(self.config["requests"], list):
            raise ConfigLoaderException("'requests' must be a list")
        
        if len(self.config["requests"]) == 0:
            raise ConfigLoaderException("'requests' list cannot be empty")
        
        # Validate each request
        for i, request in enumerate(self.config["requests"]):
            self._validate_request(request, i)
    
    def _validate_request(self, request: Dict[str, Any], index: int) -> None:
        """Validate a single request configuration."""
        if not isinstance(request, dict):
            raise ConfigLoaderException(f"Request {index} must be a dictionary")
        
        if "url" not in request:
            raise ConfigLoaderException(f"Request {index} must have a 'url'")
        
        # Set default values
        request.setdefault("method", "GET")
        request.setdefault("timeout", 30.0)
        request.setdefault("retries", 0)
        request.setdefault("retry_backoff", 1.0)
        request.setdefault("show", "all")
        request.setdefault("color", True)
        
        # Validate method
        if request["method"] not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            raise ConfigLoaderException(f"Request {index} has invalid method: {request['method']}")
        
        # Validate show option
        if request["show"] not in ["headers", "body", "all"]:
            raise ConfigLoaderException(f"Request {index} has invalid show option: {request['show']}")
    
    def process_requests(self, variables: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process requests with variable interpolation."""
        if self.config is None:
            raise ConfigLoaderException("Configuration not loaded")
        
        # Merge variables from config and parameter
        all_variables = {}
        if "variables" in self.config:
            all_variables.update(self.config["variables"])
        if variables:
            all_variables.update(variables)
        
        # Process each request
        processed_requests = []
        for request in self.config["requests"]:
            processed_request = self._interpolate_variables(request, all_variables)
            processed_requests.append(processed_request)
        
        return processed_requests
    
    def _interpolate_variables(self, request: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Interpolate variables in request configuration."""
        import copy
        result = copy.deepcopy(request)
        
        # Interpolate in URL
        if "url" in result:
            result["url"] = self._interpolate_string(result["url"], variables)
        
        # Interpolate in headers
        if "headers" in result:
            result["headers"] = {
                self._interpolate_string(k, variables): self._interpolate_string(v, variables)
                for k, v in result["headers"].items()
            }
        
        # Interpolate in data
        if "data" in result and isinstance(result["data"], str):
            result["data"] = self._interpolate_string(result["data"], variables)
        
        # Interpolate in JSON data
        if "json" in result and isinstance(result["json"], str):
            result["json"] = self._interpolate_string(result["json"], variables)
        
        # Interpolate in auth
        if "auth" in result and isinstance(result["auth"], str):
            result["auth"] = self._interpolate_string(result["auth"], variables)
        
        # Interpolate in bearer token
        if "bearer" in result and isinstance(result["bearer"], str):
            result["bearer"] = self._interpolate_string(result["bearer"], variables)
        
        return result
    
    def _interpolate_string(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in a string using ${var} syntax."""
        if not isinstance(text, str):
            return text
        
        # Find all ${var} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, text)
        
        result = text
        for var_name in matches:
            if var_name in variables:
                replacement = str(variables[var_name])
                result = result.replace(f'${{{var_name}}}', replacement)
            else:
                raise ConfigLoaderException(f"Variable '{var_name}' not found in configuration")
        
        return result


def load_batch_config(config_path: str, variables: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Load and process batch configuration file."""
    loader = ConfigLoader(config_path)
    loader.load_config()
    return loader.process_requests(variables)