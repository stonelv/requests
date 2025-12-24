import csv
import json
import os
from typing import List, Dict, Any

class Exporter:
    def __init__(self, config):
        self.config = config
        self.output_file = config.output_file
        self.output_format = config.output_format

    def export(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return None
        
        if self.output_format == 'csv':
            return self._export_csv(results)
        elif self.output_format == 'json':
            return self._export_json(results)
        else:
            raise ValueError(f'不支持的输出格式: {self.output_format}')

    def _export_csv(self, results: List[Dict[str, Any]]) -> str:
        if not self.output_file:
            self.output_file = 'reqcheck_results.csv'
        
        # 确保目录存在
        if os.path.dirname(self.output_file):
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # 确定CSV列名
        fields = [
            'url', 'status_code', 'final_url', 'duration', 'redirected', 
            'timed_out', 'content_length', 'headers', 'error', 'retries'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for result in results:
                row = {}
                for field in fields:
                    value = result.get(field)
                    if field == 'headers' and value:
                        row[field] = json.dumps(value)
                    elif isinstance(value, bool):
                        row[field] = 'True' if value else 'False'
                    else:
                        row[field] = value
                writer.writerow(row)
        
        return self.output_file

    def _export_json(self, results: List[Dict[str, Any]]) -> str:
        if not self.output_file:
            self.output_file = 'reqcheck_results.json'
        
        # 确保目录存在
        if os.path.dirname(self.output_file):
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return self.output_file

    def print_summary(self, results: List[Dict[str, Any]]):
        total = len(results)
        success = sum(1 for r in results if r['status_code'] is not None and 200 <= r['status_code'] < 300)
        failed = sum(1 for r in results if r['error'] is not None)
        redirected = sum(1 for r in results if r['redirected'])
        timed_out = sum(1 for r in results if r['timed_out'])
        
        print(f'\n=== 执行总结 ===')
        print(f'总URL数: {total}')
        print(f'成功: {success} ({success/total*100:.1f}%)')
        print(f'失败: {failed} ({failed/total*100:.1f}%)')
        print(f'重定向: {redirected} ({redirected/total*100:.1f}%)')
        print(f'超时: {timed_out} ({timed_out/total*100:.1f}%)')

    def __repr__(self) -> str:
        return f'Exporter(output_file={self.output_file}, format={self.output_format})'
