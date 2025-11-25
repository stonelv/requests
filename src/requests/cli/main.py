"""
Main entry point for rhttp CLI tool.
"""

import json
import sys
from typing import Dict, Any, Optional, List

from .parser import parse_args, validate_args
from .executor import create_executor, parse_auth, is_success_status_code, RequestExecutorException
from .config_loader import load_batch_config, ConfigLoaderException
from .report import create_report_generator, RequestResult


# Exit codes
EXIT_SUCCESS = 0
EXIT_ARGUMENT_ERROR = 2
EXIT_REQUEST_ERROR = 10
EXIT_BATCH_ERROR = 11


def main() -> int:
    """Main entry point for rhttp CLI."""
    try:
        # Parse arguments
        args = parse_args()
        validate_args(args)
        
        if args.batch:
            return handle_batch_mode(args)
        else:
            return handle_single_request(args)
    
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return EXIT_ARGUMENT_ERROR
    except ConfigLoaderException as e:
        print(f"Configuration Error: {str(e)}", file=sys.stderr)
        return EXIT_ARGUMENT_ERROR
    except RequestExecutorException as e:
        print(f"Request Error: {str(e)}", file=sys.stderr)
        return EXIT_REQUEST_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return EXIT_ARGUMENT_ERROR
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return EXIT_ARGUMENT_ERROR


def handle_single_request(args) -> int:
    """Handle single request mode."""
    # Create report generator
    reporter = create_report_generator(color=args.color)
    
    # Create request executor
    executor = create_executor(
        timeout=args.timeout,
        retries=args.retries,
        retry_backoff=args.retry_backoff
    )
    
    # Prepare request parameters
    request_params = build_request_params(args)
    
    try:
        # Execute request
        response, elapsed_time, attempts_used = executor.execute_request(**request_params)
        
        # Print request summary
        request_config = {
            "method": args.method,
            "url": args.url
        }
        reporter.print_request_summary(request_config, response, elapsed_time=elapsed_time, attempts_used=attempts_used)
        
        # Print response details
        if is_success_status_code(response.status_code):
            reporter.print_response_details(response, args.show)
        else:
            reporter.print_response_details(response, args.show)
            return EXIT_REQUEST_ERROR
        
        # Save response if requested
        if args.save:
            reporter.save_response(response, args.save)
        
        return EXIT_SUCCESS
    
    except RequestExecutorException as e:
        request_config = {
            "method": args.method,
            "url": args.url
        }
        reporter.print_request_summary(request_config, error=str(e))
        return EXIT_REQUEST_ERROR


def handle_batch_mode(args) -> int:
    """Handle batch processing mode."""
    # Create report generator
    reporter = create_report_generator(color=args.color)
    
    try:
        # Load batch configuration
        requests_config = load_batch_config(args.batch)
        
        # Create request executor
        executor = create_executor(
            timeout=30.0,  # Default timeout for batch mode
            retries=0,      # Default retries for batch mode
            retry_backoff=1.0
        )
        
        results = []
        has_failures = False
        
        # Process each request
        for i, request_config in enumerate(requests_config):
            try:
                # Build request parameters from config
                request_params = build_request_params_from_config(request_config)
                
                # Execute request
                response, elapsed_time, attempts_used = executor.execute_request(**request_params)
                
                # Create RequestResult for this request
                request_result = RequestResult(
                    url=request_config.get("url", ""),
                    method=request_config.get("method", "GET"),
                    status_code=response.status_code if response else None,
                    response_time=elapsed_time,
                    error=None,
                    name=request_config.get("name"),
                    retries=attempts_used - 1,  # retries = attempts - 1
                    body_length=len(response.content) if response and hasattr(response, 'content') else None
                )
                
                # Print request summary
                reporter.print_request_summary(request_config, response, index=i, elapsed_time=elapsed_time, attempts_used=attempts_used)
                
                # Print response details if requested
                show_option = request_config.get("show", "all")
                if is_success_status_code(response.status_code):
                    if show_option != "none":
                        reporter.print_response_details(response, show_option)
                else:
                    has_failures = True
                    if show_option != "none":
                        reporter.print_response_details(response, show_option)
                
                # Save response if requested
                if "save" in request_config:
                    reporter.save_response(response, request_config["save"])
                
                results.append(request_result)
            
            except RequestExecutorException as e:
                # Create RequestResult for failed request
                request_result = RequestResult(
                    url=request_config.get("url", ""),
                    method=request_config.get("method", "GET"),
                    status_code=None,
                    response_time=0.0,  # No elapsed time for failed requests
                    error=str(e),
                    name=request_config.get("name"),
                    retries=0,  # No retries for failed requests
                    body_length=None
                )
                
                reporter.print_request_summary(request_config, error=str(e), index=i)
                results.append(request_result)
                has_failures = True
        
        # Print batch summary
        reporter.print_batch_summary(results)
        
        return EXIT_BATCH_ERROR if has_failures else EXIT_SUCCESS
    
    except ConfigLoaderException as e:
        reporter.print_error(str(e))
        return EXIT_ARGUMENT_ERROR


def build_request_params(args) -> Dict[str, Any]:
    """Build request parameters from command line arguments."""
    params = {
        "url": args.url,
        "method": args.method,
        "headers": args.headers if hasattr(args, 'headers') else {},
    }
    
    # Add authentication
    if hasattr(args, 'auth') and args.auth:
        username, password = parse_auth(args.auth)
        params["auth"] = (username, password)
    elif hasattr(args, 'bearer') and args.bearer:
        params["bearer_token"] = args.bearer
    
    # Add data
    if hasattr(args, 'data') and args.data:
        params["data"] = args.data
    elif hasattr(args, 'json') and args.json:
        try:
            params["json_data"] = json.loads(args.json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {str(e)}")
    elif hasattr(args, 'file') and args.file:
        params["file_path"] = args.file
        if hasattr(args, 'file_field') and args.file_field:
            params["file_field"] = args.file_field
    
    return params


def build_request_params_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build request parameters from configuration dictionary."""
    params = {
        "url": config["url"],
        "method": config.get("method", "GET"),
        "headers": config.get("headers", {}),
    }
    
    # Add authentication
    if "auth" in config:
        username, password = parse_auth(config["auth"])
        params["auth"] = (username, password)
    elif "bearer" in config:
        params["bearer_token"] = config["bearer"]
    
    # Add data
    if "data" in config:
        params["data"] = config["data"]
    elif "json" in config:
        if isinstance(config["json"], str):
            try:
                params["json_data"] = json.loads(config["json"])
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON data: {str(e)}")
        else:
            params["json_data"] = config["json"]
    elif "file" in config:
        params["file_path"] = config["file"]
    
    return params


if __name__ == "__main__":
    sys.exit(main())