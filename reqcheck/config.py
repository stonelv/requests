import os
import json
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

@dataclass
class Config:
    # 输入输出配置
    input_file: str = ""
    output_file: str = ""
    output_format: str = "json"  # csv or json
    
    # 请求配置
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    timeout: int = 10
    proxies: Dict[str, str] = field(default_factory=dict)
    
    # 并发配置
    concurrency: int = 5
    max_retries: int = 3
    backoff_factor: float = 0.5
    
    # 下载配置
    download: bool = False
    download_dir: str = "./downloads"
    
    # 日志配置
    verbose: bool = False
    quiet: bool = False
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量加载配置"""
        load_dotenv()
        return cls(
            method=os.getenv('REQCHECK_METHOD', 'GET'),
            timeout=int(os.getenv('REQCHECK_TIMEOUT', 10)),
            concurrency=int(os.getenv('REQCHECK_CONCURRENCY', 5)),
            max_retries=int(os.getenv('REQCHECK_MAX_RETRIES', 3)),
            backoff_factor=float(os.getenv('REQCHECK_BACKOFF_FACTOR', 0.5)),
        )
    
    @classmethod
    def from_file(cls, config_file: str) -> 'Config':
        """从JSON或YAML配置文件加载配置"""
        with open(config_file, 'r') as f:
            if config_file.endswith('.yml') or config_file.endswith('.yaml'):
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)
        return cls(**config_data)
    
    def merge(self, other: 'Config') -> None:
        """合并配置"""
        for key, value in other.__dict__.items():
            if value is not None and value != "" and value != [] and value != {}:
                setattr(self, key, value)
    
    def validate(self) -> None:
        """验证配置"""
        if self.input_file and not os.path.exists(self.input_file):
            raise FileNotFoundError(f"输入文件不存在: {self.input_file}")
        
        if self.download and not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)
        
        if self.output_format not in ['csv', 'json']:
            raise ValueError(f"不支持的输出格式: {self.output_format}")
        
        if self.method not in ['GET', 'POST', 'HEAD', 'OPTIONS']:
            raise ValueError(f"不支持的HTTP方法: {self.method}")
        
        if self.concurrency < 1:
            raise ValueError("并发数必须大于0")
        
        if self.max_retries < 0:
            raise ValueError("最大重试次数不能为负数")
        
        if self.backoff_factor < 0:
            raise ValueError("退避因子不能为负数")