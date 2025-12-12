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
        # 统一JSON导出格式
        formatted_results = []
        for result in results:
            headers = result.get('headers', {})
            headers_summary = '; '.join([f'{k}: {v}' for k, v in headers.items()])
            formatted_result = {
                'url': result.get('url', ''),
                'final_url': result.get('final_url', ''),
                'status_code': result.get('status_code', ''),
                'elapsed_ms': round(result.get('response_time', 0.0) * 1000),
                'redirected': result.get('redirected', False),
                'timed_out': result.get('timeout', False),
                'content_length': result.get('content_length', 0),
                'headers_summary': headers_summary
            }
            formatted_results.append(formatted_result)
        
        if not self.config.output_file:
            # 如果没有指定输出文件，直接打印到控制台
            print(json.dumps(formatted_results, indent=2, ensure_ascii=False))
            return
        
        # 确保输出目录存在
        output_dir = os.path.dirname(self.config.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(self.config.output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_results, f, indent=2, ensure_ascii=False)

class CSVExporter(Exporter):
    """CSV格式导出器"""
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """将结果导出为CSV文件"""
        if not results:
            return
        
        # 确定CSV字段
        csv_fields = [
            'url', 'final_url', 'status_code', 'elapsed_ms', 
            'redirected', 'timed_out', 'content_length', 'headers_summary'
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
        headers_summary = '; '.join([f'{k}: {v}' for k, v in headers.items()])
        return {
            'url': result.get('url', ''),
            'final_url': result.get('final_url', ''),
            'status_code': result.get('status_code', ''),
            'elapsed_ms': round(result.get('response_time', 0.0) * 1000),
            'redirected': result.get('redirected', False),
            'timed_out': result.get('timeout', False),
            'content_length': result.get('content_length', 0),
            'headers_summary': headers_summary
        }

def get_exporter(config: Config) -> Exporter:
    """根据配置获取对应的导出器"""
    if config.output_format == 'json':
        return JSONExporter(config)
    elif config.output_format == 'csv':
        return CSVExporter(config)
    else:
        raise ValueError(f"不支持的输出格式: {config.output_format}")