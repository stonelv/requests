"""Export results to CSV/JSON formats"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any

from .logging_utils import get_logger

logger = get_logger(__name__)


class BaseExporter:
    """Base exporter class"""
    
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.fields = [
            "url",
            "final_url",
            "status_code",
            "elapsed",
            "redirected",
            "timed_out",
            "content_length",
            "error"
        ]
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """Export results to file"""
        raise NotImplementedError


class CSVExporter(BaseExporter):
    """Export results to CSV"""
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """Export results to CSV file"""
        with open(self.output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writeheader()
            
            for result in results:
                # Prepare row data
                row = {}
                for field in self.fields:
                    value = result.get(field)
                    if value is None:
                        row[field] = ""
                    elif isinstance(value, float):
                        row[field] = f"{value:.4f}"
                    else:
                        row[field] = str(value)
                
                writer.writerow(row)
        
        logger.info(f"Results exported to {self.output_file} (CSV format)")


class JSONExporter(BaseExporter):
    """Export results to JSON"""
    
    def export(self, results: List[Dict[str, Any]]) -> None:
        """Export results to JSON file"""
        # Prepare data for JSON serialization
        export_data = []
        for result in results:
            # Convert non-serializable types
            data = {}
            for key, value in result.items():
                if key == "headers":
                    continue  # Skip headers in JSON output
                
                if isinstance(value, float):
                    data[key] = round(value, 4)
                else:
                    data[key] = value
            
            export_data.append(data)
        
        with open(self.output_file, "w") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results exported to {self.output_file} (JSON format)")


def get_exporter(output_file: Path) -> BaseExporter:
    """Get appropriate exporter based on file extension"""
    ext = output_file.suffix.lower()
    
    if ext == ".csv":
        return CSVExporter(output_file)
    elif ext in [".json", ".js"]:
        return JSONExporter(output_file)
    else:
        raise ValueError(f"Unsupported output format: {ext}")