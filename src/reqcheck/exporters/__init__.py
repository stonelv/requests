import json
import csv
import os
from typing import List, Dict, Any
from ..config import config
from ..logging_utils import get_logger
from ..requestor import RequestResult

class Exporter:
    def __init__(self):
        self.logger = get_logger()
        self.output_file = config.output_file
        self.output_format = config.output_format
    
    def convert_result_to_dict(self, result: RequestResult) -> Dict[str, Any]:
        return {
            "url": result.url,
            "status_code": result.status_code,
            "final_url": result.final_url,
            "elapsed": result.elapsed,
            "redirected": result.redirected,
            "timed_out": result.timed_out,
            "content_length": result.content_length,
            "headers": result.headers,
            "error": result.error,
            "success": result.success
        }
    
    def export_json(self, results: List[RequestResult]):
        if not self.output_file:
            self.logger.error("Output file not specified for JSON export")
            return
        
        try:
            data = [self.convert_result_to_dict(result) for result in results]
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Successfully exported results to JSON: {self.output_file}")
        except Exception as e:
            self.logger.error(f"Failed to export results to JSON: {str(e)}")
            raise
    
    def export_csv(self, results: List[RequestResult]):
        if not self.output_file:
            self.logger.error("Output file not specified for CSV export")
            return
        
        try:
            # Convert results to dictionaries
            data = [self.convert_result_to_dict(result) for result in results]
            
            # Get all unique keys
            if not data:
                self.logger.warning("No results to export to CSV")
                return
            
            fieldnames = list(data[0].keys())
            
            # Write CSV
            with open(self.output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Successfully exported results to CSV: {self.output_file}")
        except Exception as e:
            self.logger.error(f"Failed to export results to CSV: {str(e)}")
            raise
    
    def export(self, results: List[RequestResult]):
        if not self.output_file:
            self.logger.warning("No output file specified. Results will not be exported.")
            return
        
        if self.output_format == "json":
            self.export_json(results)
        elif self.output_format == "csv":
            self.export_csv(results)
        else:
            self.logger.error(f"Unsupported output format: {self.output_format}")
            raise ValueError(f"Unsupported output format: {self.output_format}")

def create_exporter() -> Exporter:
    return Exporter()