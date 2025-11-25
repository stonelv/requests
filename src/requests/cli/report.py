# -*- coding: utf-8 -*-
"""Report generation for rhttp tool."""
from typing import List, Dict, Any, Optional
from requests import Response
import sys

# Use ANSI colors directly to avoid dependency on colorama
def get_colorama_alternatives():
    """Return ANSI color codes as alternative to colorama."""
    return {
        'Fore': {
            'GREEN': '\033[32m',
            'YELLOW': '\033[33m',
            'RED': '\033[31m',
        },
        'Style': {
            'RESET_ALL': '\033[0m',
        }
    }

# Check if color should be enabled
use_color = sys.stdout.isatty()

# Get color codes
colors = get_colorama_alternatives()
Fore = colors['Fore']
Style = colors['Style']

# Ensure Fore and Style are dictionaries (in case of any issues)
if not isinstance(Fore, dict):
    Fore = {'GREEN': '', 'YELLOW': '', 'RED': ''}
if not isinstance(Style, dict):
    Style = {'RESET_ALL': ''}


def format_response(response: Response, show: str = 'body', color: bool = None, elapsed_ms: float = None, attempts_used: int = None) -> str:
    """Format a response for output with additional information."""
    output = []
    
    # Determine if color should be used
    use_color = color if color is not None else sys.stdout.isatty()
    
    # Status line
    status_line = f'{response.status_code} {response.reason}'
    if use_color:
        if 200 <= response.status_code < 300:
            status_line = Fore['GREEN'] + status_line + Style['RESET_ALL']
        elif 300 <= response.status_code < 400:
            status_line = Fore['YELLOW'] + status_line + Style['RESET_ALL']
        else:
            status_line = Fore['RED'] + status_line + Style['RESET_ALL']
    output.append(status_line)
    
    # Additional information
    if elapsed_ms is not None or attempts_used is not None:
        additional_info = []
        if elapsed_ms is not None:
            additional_info.append(f'Elapsed: {elapsed_ms:.2f}ms')
        if attempts_used is not None:
            additional_info.append(f'Retries: {attempts_used - 1}')  # 0 retries means 1 attempt
        output.append(f'({', '.join(additional_info)})')
    
    # Body length
    body_length = len(response.text)
    output.append(f'Body: {body_length} bytes')
    
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


def generate_batch_summary(results: List[Dict[str, Any]], color: bool = None) -> str:
    """Generate a summary for batch mode results with detailed table."""
    # Determine if color should be used
    use_color = color if color is not None else sys.stdout.isatty()
    
    # Create summary table
    table = []
    
    # Header row
    table.append('+-----------------+---------+--------+-----+-----------+-------------+')
    table.append('| Name            | Method  | Status | OK  | Time (ms) | Retries Used|')
    table.append('+-----------------+---------+--------+-----+-----------+-------------+')
    
    # Data rows
    for idx, result in enumerate(results):
        index = result.get('index', idx) or idx
        name = result.get('name') or f'Req {index+1}' or 'Req'
        method = result.get('method', 'GET')  # Default to GET if method is missing
        status_code = result['status_code']
        status_reason = result.get('reason', '')
        status = f'{status_code} {status_reason}' if status_reason else str(status_code)
        ok = '✓' if 200 <= status_code < 300 else '✗'
        # Use elapsed_ms if available, otherwise calculate from elapsed_time, default to 0 if neither is present
        if 'elapsed_ms' in result:
            time_ms = result['elapsed_ms'] or 0  # Preserve decimal part if available, default to 0 if None
        elif 'elapsed_time' in result:
            time_ms = (result['elapsed_time'] or 0) * 1000
        else:
            time_ms = 0  # Default to 0 if neither field is present
        retries_used = result.get('attempts_used', 1) - 1  # 0 retries means 1 attempt
        
        # Format row with padding
        row = f"| {name:<15} | {method:<7} | {status:<6} | {ok:<3} | {time_ms:<9} | {retries_used:<11} |"
        
        # Apply color if enabled
        if use_color:
            if ok == '✓':
                row = row.replace('✓', Fore['GREEN'] + '✓' + Style['RESET_ALL'])
            else:
                row = row.replace('✗', Fore['RED'] + '✗' + Style['RESET_ALL'])
        
        table.append(row)
    
    table.append('+-----------------+---------+--------+-----+-----------+-------------+')
    
    # Summary statistics
    total = len(results)
    successful = sum(1 for r in results if 200 <= r['status_code'] < 300)
    failed = total - successful
    
    summary = [
        'Batch Summary:',
        f'  Total requests: {total}',
        f'  Successful: {successful}',
        f'  Failed: {failed}'
    ]
    
    if use_color:
        if failed > 0:
            summary[-1] = Fore['RED'] + summary[-1] + Style['RESET_ALL']
        else:
            summary[-2] = Fore['GREEN'] + summary[-2] + Style['RESET_ALL']
    
    return '\n'.join(table + [''] + summary)


def format_batch_result(result: Dict[str, Any], color: bool = None) -> str:
    """Format a single batch result for output."""
    # Determine if color should be used
    use_color = color if color is not None else sys.stdout.isatty()
    
    # Handle missing index key
    index = result.get('index', 0)
    name = result.get('name') or f'Request {index+1}'
    method = result.get('method') or 'GET'
    status_line = f"{name}: {method} {result['url']} - {result['status_code']} {result['reason']}"
    
    if use_color:
        if 200 <= result['status_code'] < 300:
            status_line = Fore['GREEN'] + status_line + Style['RESET_ALL']
        elif 300 <= result['status_code'] < 400:
            status_line = Fore['YELLOW'] + status_line + Style['RESET_ALL']
        else:
            status_line = Fore['RED'] + status_line + Style['RESET_ALL']
    
    elapsed_time = result.get('elapsed_time', 0)
    retries_used = result.get('attempts_used', 1) - 1  # 0 retries means 1 attempt
    
    return f"{status_line}\n  Elapsed: {elapsed_time:.3f}s, Retries: {retries_used}"
