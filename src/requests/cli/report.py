"""
Report generation and output formatting for rhttp CLI tool.
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

try:
    import requests
except ImportError:
    requests = None


@dataclass
class RequestResult:
    """Data class to represent the result of a single HTTP request."""
    url: str
    method: str
    status_code: Optional[int]
    response_time: float
    error: Optional[Exception] = None


class ReportGenerator:
    """Handles output formatting and report generation."""
    
    def __init__(self, color: bool = True, output_file: Optional[str] = None):
        self.color = color
        self.output_file = output_file
        self.use_color = color and self._supports_color()
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output."""
        try:
            # Check if we're in a terminal that supports color
            if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
                return True
            if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
                return True
            return False
        except:
            return False
    
    def colorize(self, text: str, color_code: str) -> str:
        """Apply color to text if color is enabled."""
        if not self.use_color:
            return text
        
        color_codes = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "bold": "\033[1m",
            "reset": "\033[0m",
        }
        
        if color_code in color_codes:
            return f"{color_codes[color_code]}{text}{color_codes['reset']}"
        return text
    
    def print_request_summary(self, result: RequestResult, index: Optional[int] = None) -> None:
        """Print a summary of a single request."""
        if index is not None:
            prefix = f"[{index}] "
        else:
            prefix = ""
        
        if result.error:
            status_text = self.colorize("FAILED", "red")
            output = f"{prefix}{result.method} {result.url} - {status_text}\n"
            output += f"  Error: {str(result.error)}"
            print(output)
        elif result.status_code is not None:
            status_category = self._get_status_code_category(result.status_code)
            
            if 200 <= result.status_code < 300:
                status_text = self.colorize(str(result.status_code), "green")
            elif 300 <= result.status_code < 400:
                status_text = self.colorize(str(result.status_code), "yellow")
            elif 400 <= result.status_code < 500:
                status_text = self.colorize(str(result.status_code), "red")
            else:
                status_text = self.colorize(str(result.status_code), "magenta")
            
            output = f"{prefix}{result.method} {result.url} - {status_text} ({status_category})\n"
            output += f"  Response time: {result.response_time:.1f}s"
            print(output)
        else:
            summary_line = f"{prefix}{result.method} {result.url} - Pending..."
            print(summary_line)
    
    def print_response_details(self, response: Any, show_headers: bool = False, show_body: bool = False) -> None:
        """Print detailed response information."""
        if show_headers:
            self._print_headers(response)
        
        if show_body:
            self._print_body(response)
    
    def _print_headers(self, response: Any) -> None:
        """Print response headers."""
        print(self.colorize("=== Response Headers ===", "bold"))
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
        print(f"Server: {response.headers.get('server', 'N/A')}")
        print(f"Date: {response.headers.get('date', 'N/A')}")
        
        # Print all headers if in verbose mode
        print("\nAll Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
    
    def _print_body(self, response: Any) -> None:
        """Print response body."""
        print(self.colorize("=== Response Body ===", "bold"))
        
        try:
            # Check if response has json method and it's callable
            if hasattr(response, 'json') and callable(response.json):
                try:
                    json_data = response.json()
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                except (ValueError, TypeError):
                    # If JSON parsing fails, try text
                    if hasattr(response, 'text'):
                        text_content = response.text
                        if len(text_content) > 1000:
                            print(text_content[:1000] + "... (truncated)")
                        else:
                            print(text_content)
                    else:
                        print("Unable to display response body")
            elif hasattr(response, 'text'):
                # If no json method, try text
                text_content = response.text
                if len(text_content) > 1000:
                    print(text_content[:1000] + "... (truncated)")
                else:
                    print(text_content)
            else:
                print("Unable to display response body")
        except AttributeError:
            print("Unable to display response body")
        print()
    
    def print_batch_summary(self, results: List[RequestResult]) -> None:
        """Print a summary of batch processing results."""
        total = len(results)
        successful = sum(1 for r in results if r.status_code is not None and 200 <= r.status_code < 300)
        failed = total - successful
        
        print(self.colorize("=== Batch Processing Summary ===", "bold"))
        print(f"Total requests: {total}")
        print(f"Successful: {self.colorize(str(successful), 'green')}")
        print(f"Failed: {self.colorize(str(failed), 'red')}")
        
        if failed > 0:
            print("\nFailed requests:")
            for i, result in enumerate(results):
                if result.status_code is None or not (200 <= result.status_code < 300):
                    error_msg = str(result.error) if result.error else "Unknown error"
                    print(f"  [{i}] {result.method} {result.url}: {error_msg}")
        
        print()
    
    def save_response_to_file(self, response: Any, file_path: str) -> None:
        """Save response to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Save response data
                f.write("Status: {}\n".format(response.status_code))
                f.write("Headers:\n")
                for key, value in response.headers.items():
                    f.write("  {}: {}\n".format(key, value))
                f.write("\nBody:\n")
                
                try:
                    # Try to get JSON data
                    if hasattr(response, 'json'):
                        json_data = response.json()
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    else:
                        # If not JSON, save as text
                        f.write(response.text)
                except (ValueError, TypeError, AttributeError):
                    # If not JSON, save as text
                    try:
                        f.write(response.text)
                    except AttributeError:
                        f.write(str(response))
            
            print(f"Response saved to: {file_path}")
        except Exception as e:
            print(f"Failed to save response: {str(e)}")
    
    def _format_headers(self, headers: Dict[str, str]) -> str:
        """Format headers for display."""
        if not headers:
            return ""
        
        formatted = []
        for key, value in headers.items():
            formatted.append(f"{key}: {value}")
        return "\n".join(formatted)
    
    def _color_code(self, color_name: str) -> str:
        """Get color code for color name."""
        if not self.color:
            return ""
        
        color_codes = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }
        
        return color_codes.get(color_name, "")
    
    def _format_time(self, seconds: float) -> str:
        """Format time in human readable format."""
        if seconds < 0.001:
            return f"{seconds * 1000000:.0f}μs"
        elif seconds < 1.0:
            return f"{seconds * 1000:.1f}ms"
        else:
            return f"{seconds:.1f}s"
    
    def _get_status_code_category(self, status_code: int) -> str:
        """Get the category of HTTP status code."""
        if 100 <= status_code < 200:
            return "Informational"
        elif 200 <= status_code < 300:
            return "Success"
        elif 300 <= status_code < 400:
            return "Redirection"
        elif 400 <= status_code < 500:
            return "Client Error"
        elif 500 <= status_code < 600:
            return "Server Error"
        else:
            return "Unknown"
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        error_msg = self.colorize(f"Error: {message}", "red")
        print(error_msg, file=sys.stderr)
    
    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        warning_msg = self.colorize(f"Warning: {message}", "yellow")
        print(warning_msg)
    
    def print_info(self, message: str) -> None:
        """Print an info message."""
        info_msg = self.colorize(f"Info: {message}", "blue")
        print(info_msg)


def create_report_generator(color: bool = True, output_file: Optional[str] = None) -> ReportGenerator:
    """Create a report generator instance."""
    return ReportGenerator(color=color, output_file=output_file)