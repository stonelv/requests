# -*- coding: utf-8 -*-
"""Configuration loader for batch mode."""
import yaml
import os
from typing import Dict, Any, List
import re


def load_config(file_path: str) -> Dict[str, Any]:
    """Load and parse YAML configuration file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Ensure configuration has required keys
    if 'requests' not in config:
        raise ValueError('Configuration file must contain a "requests" list')
    
    return config


def interpolate_variables(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Interpolate variables in requests using ${var} syntax."""
    variables = config.get('variables', {})
    requests = config.get('requests', [])
    
    # Function to interpolate variables in a string
    def interpolate_string(s: str) -> str:
        if not isinstance(s, str):
            return s
        # Replace ${var} with variable value
        return re.sub(r'\$\{([^}]+)\}', lambda m: variables.get(m.group(1), ''), s)
    
    # Function to interpolate variables in a nested structure
    def interpolate(obj):
        if isinstance(obj, dict):
            return {k: interpolate(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [interpolate(v) for v in obj]
        elif isinstance(obj, str):
            return interpolate_string(obj)
        else:
            return obj
    
    # Interpolate variables in each request
    interpolated_requests = [interpolate(req) for req in requests]
    
    return interpolated_requests
