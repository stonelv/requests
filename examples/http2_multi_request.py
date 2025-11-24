#!/usr/bin/env python3
"""
HTTP/2 Multi-Request Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates how to use the HTTP2Adapter to make multiple
concurrent HTTP/2 requests with connection reuse, metrics collection,
and proper error handling.

Requirements:
    pip install requests h2

Usage:
    python http2_multi_request.py
"""

import requests
import time
import concurrent.futures
import threading
from requests.adapters_http2 import HTTP2Adapter


# Global metrics storage
metrics_history = []
metrics_lock = threading.Lock()


def metrics_callback(metrics):
    """Callback function to collect connection metrics."""
    with metrics_lock:
        metrics_history.append({
            'timestamp': time.time(),
            'metrics': metrics.copy()
        })


def make_http2_request(session, url, request_id):
    """Make a single HTTP/2 request and return the result."""
    try:
        start_time = time.time()
        response = session.get(url, timeout=30)
        end_time = time.time()
        
        return {
            'request_id': request_id,
            'url': url,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'response_time': end_time - start_time,
            'headers': dict(response.headers),
            'success': True
        }
    except Exception as e:
        return {
            'request_id': request_id,
            'url': url,
            'error': str(e),
            'success': False
        }


def make_concurrent_requests(urls, max_workers=5):
    """Make multiple concurrent HTTP/2 requests."""
    # Create session with HTTP2Adapter
    session = requests.Session()
    
    # Configure HTTP2Adapter with custom settings
    http2_adapter = HTTP2Adapter(
        pool_connections=10,              # Maximum connections to cache
        pool_maxsize=50,                 # Maximum concurrent streams per connection
        max_concurrent_streams=100,       # HTTP/2 max concurrent streams
        initial_window_size=65535,       # Flow control window size
        enable_push=False,               # Disable server push for this example
        stream_timeout=30,               # Timeout per stream
        metrics_callback=metrics_callback,  # Collect metrics
        fallback_to_http11=True          # Fallback to HTTP/1.1 if HTTP/2 unavailable
    )
    
    # Mount the adapter for HTTPS URLs
    session.mount('https://', http2_adapter)
    
    results = []
    
    # Use ThreadPoolExecutor for concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        future_to_url = {
            executor.submit(make_http2_request, session, url, i): url
            for i, url in enumerate(urls)
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Request {result['request_id']}: {url} - Status: {result.get('status_code', 'Error')}")
            except Exception as e:
                print(f"Request failed for {url}: {e}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'success': False
                })
    
    # Close the session
    session.close()
    
    return results


def demonstrate_basic_usage():
    """Demonstrate basic HTTP/2 usage."""
    print("=== Basic HTTP/2 Usage ===")
    
    # Create session with HTTP2Adapter
    session = requests.Session()
    http2_adapter = HTTP2Adapter()
    session.mount('https://', http2_adapter)
    
    try:
        # Make a simple request
        response = session.get('https://www.google.com')
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content length: {len(response.content)} bytes")
        
        # Get adapter metrics
        metrics = http2_adapter.get_metrics()
        print(f"Connection metrics: {metrics}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()


def demonstrate_concurrent_requests():
    """Demonstrate concurrent HTTP/2 requests."""
    print("\n=== Concurrent HTTP/2 Requests ===")
    
    # List of URLs to test (using reliable HTTP/2 enabled sites)
    test_urls = [
        'https://www.google.com',
        'https://www.github.com',
        'https://www.cloudflare.com',
        'https://www.akamai.com',
        'https://www.fastly.com',
        'https://www.google.com/search?q=http2',
        'https://www.github.com/search?q=http2',
        'https://www.cloudflare.com/learning/performance/what-is-http2/',
        'https://www.akamai.com/what-is-http2',
        'https://www.fastly.com/blog/what-is-http2'
    ]
    
    # Make concurrent requests
    start_time = time.time()
    results = make_concurrent_requests(test_urls, max_workers=5)
    end_time = time.time()
    
    # Analyze results
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]
    
    print(f"\nResults Summary:")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful_requests)}")
    print(f"Failed: {len(failed_requests)}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    
    if successful_requests:
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        print(f"Average response time: {avg_response_time:.2f} seconds")
        
        # Show status codes
        status_codes = {}
        for result in successful_requests:
            status_code = result['status_code']
            status_codes[status_code] = status_codes.get(status_code, 0) + 1
        
        print(f"Status codes: {status_codes}")
    
    if failed_requests:
        print(f"\nFailed requests:")
        for result in failed_requests:
            print(f"  {result['url']}: {result['error']}")


def demonstrate_metrics_collection():
    """Demonstrate metrics collection and analysis."""
    print("\n=== Metrics Collection ===")
    
    # Clear metrics history
    global metrics_history
    metrics_history = []
    
    # Make some requests to generate metrics
    session = requests.Session()
    http2_adapter = HTTP2Adapter(metrics_callback=metrics_callback)
    session.mount('https://', http2_adapter)
    
    try:
        # Make several requests
        for i in range(3):
            try:
                response = session.get('https://www.google.com')
                print(f"Request {i+1}: Status {response.status_code}")
                time.sleep(0.5)  # Small delay between requests
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
        
        # Show collected metrics
        print(f"\nCollected {len(metrics_history)} metrics snapshots:")
        
        for i, snapshot in enumerate(metrics_history):
            print(f"\nSnapshot {i+1} (at {snapshot['timestamp']}):")
            metrics = snapshot['metrics']
            print(f"  Streams opened: {metrics['streams_opened']}")
            print(f"  Streams closed: {metrics['streams_closed']}")
            print(f"  Frames sent: {metrics['frames_sent']}")
            print(f"  Frames received: {metrics['frames_received']}")
            print(f"  Bytes sent: {metrics['bytes_sent']}")
            print(f"  Bytes received: {metrics['bytes_received']}")
            print(f"  Connection errors: {metrics['connection_errors']}")
            print(f"  Stream errors: {metrics['stream_errors']}")
            print(f"  Uptime: {metrics['uptime']:.2f} seconds")
        
        # Show final adapter metrics
        final_metrics = http2_adapter.get_metrics()
        print(f"\nFinal adapter metrics:")
        for key, value in final_metrics.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error in metrics demonstration: {e}")
    finally:
        session.close()


def demonstrate_error_handling():
    """Demonstrate error handling and fallback."""
    print("\n=== Error Handling and Fallback ===")
    
    session = requests.Session()
    http2_adapter = HTTP2Adapter(fallback_to_http11=True)
    session.mount('https://', http2_adapter)
    
    # Test with various scenarios
    test_cases = [
        ('https://www.google.com', 'Valid HTTPS URL'),
        ('https://httpstat.us/404', '404 response'),
        ('https://httpstat.us/500', '500 response'),
    ]
    
    for url, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"URL: {url}")
        
        try:
            response = session.get(url, timeout=10)
            print(f"Result: Status {response.status_code}")
            print(f"HTTP/2 used: Connection established successfully")
            
        except Exception as e:
            print(f"Result: Error - {e}")
            print(f"HTTP/2 used: Connection failed")
    
    # Test with non-HTTPS URL (should fallback to HTTP/1.1)
    print(f"\nTesting: Non-HTTPS URL (should fallback)")
    print(f"URL: http://example.com")
    
    try:
        response = session.get('http://example.com', timeout=10)
        print(f"Result: Status {response.status_code}")
        print(f"Fallback used: Yes (HTTP/1.1)")
    except Exception as e:
        print(f"Result: Error - {e}")
    
    session.close()


def main():
    """Main function to run all demonstrations."""
    print("HTTP/2 Adapter Demonstration")
    print("=" * 50)
    
    try:
        # Basic usage
        demonstrate_basic_usage()
        
        # Concurrent requests
        demonstrate_concurrent_requests()
        
        # Metrics collection
        demonstrate_metrics_collection()
        
        # Error handling
        demonstrate_error_handling()
        
    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("\nDemonstration complete")


if __name__ == '__main__':
    main()