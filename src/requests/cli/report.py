# -*- coding: utf-8 -*-
"""Report generation for rhttp tool."""
from typing import List, Dict, Any, Optional
from requests import Response
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


def format_response(response: Response, show: str = 'body', color: bool = True) -> str:
    """Format a response for output."""
    output = []
    
    # Status line
    status_line = f'{response.status_code} {response.reason}'
    if color:
        if 200 <= response.status_code < 300:
            status_line = Fore.GREEN + status_line
        elif 300 <= response.status_code < 400:
            status_line = Fore.YELLOW + status_line
        else:
            status_line = Fore.RED + status_line
    output.append(status_line)
    
    # Headers
    if show in ['headers', 'all']:
        output.append(f'Headers:')
        for key, value in response.headers.items():
            header_line = f'  {key}: {value}'
            output.append(header_line)
        output.append('')  # Empty line for separation
    
    # Body
    if show in ['body', 'all']:
        output.append(f'Body:')
        output.append(response.text)
    
    return '\n'.join(output)


def generate_batch_summary(results: List[Dict[str, Any]], color: bool = True) -> str:
    """Generate a summary for batch mode results."""
    total = len(results)
    successful = sum(1 for r in results if 200 <= r['status_code'] < 300)
    failed = total - successful
    
    summary = [
        'Batch Summary:',
        f'  Total requests: {total}',
        f'  Successful: {successful}',
        f'  Failed: {failed}'
    ]
    
    if color:
        if failed > 0:
            summary[-1] = Fore.RED + summary[-1]
        else:
            summary[-2] = Fore.GREEN + summary[-2]
    
    return '\n'.join(summary)


def format_batch_result(result: Dict[str, Any], color: bool = True) -> str:
    """Format a single batch result for output."""
    status_line = f"Request {result['index']+1}: {result['method']} {result['url']} - {result['status_code']} {result['reason']}"
    if color:
        if 200 <= result['status_code'] < 300:
            status_line = Fore.GREEN + status_line
        elif 300 <= result['status_code'] < 400:
            status_line = Fore.YELLOW + status_line
        else:
            status_line = Fore.RED + status_line
    
    return f"{status_line}\n  Elapsed: {result['elapsed_time']:.3f}s"
