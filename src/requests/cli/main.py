# -*- coding: utf-8 -*-
"""Main entry point for rhttp tool."""
import sys
import requests
from typing import List, Dict, Any
from .parser import parse_args, parse_headers, parse_auth
from .executor import execute_request, prepare_request
from .report import format_response, generate_batch_summary, format_batch_result
from .config_loader import load_config, interpolate_variables

def main() -> int:
    """Main function for rhttp tool."""
    try:
        args = parse_args()
    except Exception as e:
        print(f'Error parsing arguments: {e}', file=sys.stderr)
        return 2
    
    if args.batch:
        # Batch mode
        try:
            config = load_config(args.batch)
            requests_config = interpolate_variables(config)
        except Exception as e:
            print(f'Error loading batch configuration: {e}', file=sys.stderr)
            return 2
        
        results = []
        for i, req in enumerate(requests_config):
            try:
                # Prepare request parameters
                req_params = {
                    'url': req['url'],
                    'method': req.get('method', 'GET'),
                    'headers': req.get('headers', {}),
                    'data': req.get('data'),
                    'json': req.get('json'),
                    'file_path': req.get('file'),
                    'auth': req.get('auth'),
                    'bearer': req.get('bearer'),
                    'timeout': req.get('timeout', args.timeout),
                    'retries': req.get('retries', args.retries),
                    'retry_backoff': req.get('retry_backoff', args.retry_backoff)
                }
                
                # Execute request
                response, elapsed_time = execute_request(**req_params)
                
                # Store result
                results.append({
                    'index': i,
                    'method': req_params['method'],
                    'url': req_params['url'],
                    'status_code': response.status_code,
                    'reason': response.reason,
                    'elapsed_time': elapsed_time
                })
                
                # Print result
                print(format_batch_result(results[-1], color=args.color))
                print()  # Empty line for separation
                
            except Exception as e:
                print(f'Request {i+1} failed: {e}', file=sys.stderr)
                results.append({
                    'index': i,
                    'method': req.get('method', 'GET'),
                    'url': req['url'],
                    'status_code': -1,
                    'reason': 'Error',
                    'elapsed_time': 0.0
                })
        
        # Print summary
        print(generate_batch_summary(results, color=args.color))
        
        # Return exit code: 11 if any failed, 0 otherwise
        return 11 if any(r['status_code'] < 200 or r['status_code'] >= 300 for r in results) else 0
    
    else:
        # Single request mode
        if not args.url:
            print('URL is required in single request mode', file=sys.stderr)
            return 2
        
        try:
            # Parse headers
            headers = parse_headers(args.header)
            
            # Prepare request
            req_params = prepare_request(
                url=args.url,
                method=args.method,
                headers=headers,
                data=args.data,
                json=args.json,
                file_path=args.file,
                auth=args.auth,
                bearer=args.bearer
            )
            
            # Add timeout, retries, and retry_backoff to request parameters
            req_params.update({
                'timeout': args.timeout,
                'retries': args.retries,
                'retry_backoff': args.retry_backoff
            })
            
            # Execute request
            response, elapsed_time = execute_request(**req_params)
            
            # Save response if requested
            if args.save:
                with open(args.save, 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            # Format and print response
            print(format_response(response, show=args.show, color=args.color))
            
            # Return exit code: 10 if non-2xx, 0 otherwise
            return 10 if (response.status_code < 200 or response.status_code >= 300) else 0
            
        except requests.RequestException as e:
            print(f'Request failed: {e}', file=sys.stderr)
            return 10
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            return 2

if __name__ == '__main__':
    sys.exit(main())
