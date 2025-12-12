import json
import csv
import os
from typing import List, Dict, Any
from .config import Config

class Exporter:
    """结果导出器基类"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """导出结果"""
        raise NotImplementedError

class JSONExporter(Exporter):
    """JSON格式导出器"""
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """将结果导出为JSON文件"""
        if not self.config.output_file:
            # 如果没有指定输出文件，直接打印到控制台
            print(json.dumps(results, indent=2, ensure_ascii=False))
            return
        
        # 确保输出目录存在
        output_dir = os.path.dirname(self.config.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(self.config.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

class CSVExporter(Exporter):
    """CSV格式导出器"""
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """将结果导出为CSV文件"""
        if not results:
            return
        
        # 确定CSV字段
        csv_fields = [
            'url', 'final_url', 'status_code', 'error', 
            'response_time', 'redirected', 'timeout',
            'content_length', 'server', 'content_type',
            'last_modified', 'etag'
        ]
        
        if not self.config.output_file:
            # 打印到控制台
            writer = csv.DictWriter(
                open(1, 'w'),  # 标准输出
                fieldnames=csv_fields
            )
            writer.writeheader()
            for result in results:
                row = self._format_csv_row(result)
                writer.writerow(row)
            return
        
        # 写入文件
        with open(self.config.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            for result in results:
                row = self._format_csv_row(result)
                writer.writerow(row)
    
    def _format_csv_row(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化CSV行"""
        headers = result.get('headers', {})
        return {
            'url': result.get('url', ''),
            'final_url': result.get('final_url', ''),
            'status_code': result.get('status_code', ''),
            'error': result.get('error', ''),
            'response_time': round(result.get('response_time', 0.0), 3),
            'redirected': result.get('redirected', False),
            'timeout': result.get('timeout', False),
            'content_length': result.get('content_length', 0),
            'server': headers.get('server', ''),
            'content_type': headers.get('content_type', ''),
            'last_modified': headers.get('last_modified', ''),
            'etag': headers.get('etag', '')
        }

def get_exporter(config: Config) -> Exporter:
    """根据配置获取对应的导出器"""
    if config.output_format == 'json':
        return JSONExporter(config)
    elif config.output_format == 'csv':
        return CSVExporter(config)
    else:
        raise ValueError(f"不支持的输出格式: {config.output_format}")