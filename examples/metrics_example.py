"""
Example script to demonstrate MetricsAdapter usage.
"""

import time
import requests
from requests.metrics import MetricsAdapter
from requests.adapters import HTTPAdapter


def main():
    print("Request Metrics Example")
    print("-" * 50)
    
    # Create a session
    session = requests.Session()
    
    # Create a regular HTTPAdapter
    regular_adapter = HTTPAdapter()
    
    # Create MetricsAdapter wrapping the regular adapter
    metrics_adapter = MetricsAdapter(regular_adapter)
    
    # Mount the metrics adapter to the session
    session.mount('http://', metrics_adapter)
    session.mount('https://', metrics_adapter)
    
    # Make some sample requests
    print("\nMaking sample requests...")
    
    # Successful request
    try:
        response = session.get('https://httpbin.org/get')
        print(f"GET https://httpbin.org/get - Status: {response.status_code}")
    except Exception as e:
        print(f"GET https://httpbin.org/get - Error: {e}")
    
    time.sleep(0.1)
    
    # Successful request
    try:
        response = session.get('https://httpbin.org/headers')
        print(f"GET https://httpbin.org/headers - Status: {response.status_code}")
    except Exception as e:
        print(f"GET https://httpbin.org/headers - Error: {e}")
    
    time.sleep(0.1)
    
    # Error request
    try:
        response = session.get('https://httpbin.org/status/404')
        print(f"GET https://httpbin.org/status/404 - Status: {response.status_code}")
    except Exception as e:
        print(f"GET https://httpbin.org/status/404 - Error: {e}")
    
    time.sleep(0.1)
    
    # Error request
    try:
        response = session.get('https://httpbin.org/status/500')
        print(f"GET https://httpbin.org/status/500 - Status: {response.status_code}")
    except Exception as e:
        print(f"GET https://httpbin.org/status/500 - Error: {e}")
    
    time.sleep(0.1)
    
    # Successful request
    try:
        response = session.get('https://httpbin.org/ip')
        print(f"GET https://httpbin.org/ip - Status: {response.status_code}")
    except Exception as e:
        print(f"GET https://httpbin.org/ip - Error: {e}")
    
    # Print metrics summary
    print("\n" + "-" * 50)
    print("Metrics Summary:")
    print("-" * 50)
    
    summary = metrics_adapter.stats.summary()
    
    print(f"Total requests: {summary['total_requests']}")
    print(f"Total errors: {summary['total_errors']}")
    print(f"Status distribution: {summary['status_distribution']}")
    print(f"Average latency: {summary['avg_latency']:.4f}s")
    print(f"Min latency: {summary['min_latency']:.4f}s")
    print(f"Max latency: {summary['max_latency']:.4f}s")
    print(f"P50 latency: {summary['p50_latency']:.4f}s")
    print(f"P95 latency: {summary['p95_latency']:.4f}s")
    print(f"P99 latency: {summary['p99_latency']:.4f}s")
    
    print("\n" + "-" * 50)
    print("All request latencies (s):")
    for i, latency in enumerate(metrics_adapter.stats.latencies, 1):
        print(f"Request {i}: {latency:.4f}s")


if __name__ == "__main__":
    main()
