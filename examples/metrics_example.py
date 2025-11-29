#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example demonstrating the use of the MetricsAdapter with requests.

This example creates a requests Session with a MetricsAdapter, makes several
requests to httpbin.org, and prints the collected metrics.

Run this example with:
  python examples/metrics_example.py
"""

import requests
from requests.metrics import add_metrics


def main():
    """Main function to demonstrate metrics collection."""
    # Create a requests session
    session = requests.Session()

    # Add metrics tracking to the session
    stats = add_metrics(session)

    print("Making requests to httpbin.org...")

    try:
        # Make several requests
        for i in range(10):
            # Make a GET request
            response = session.get(f"https://httpbin.org/get?index={i}")
            print(f"Request {i+1}: Status code {response.status_code}")

            # Sleep for a short time to simulate real-world usage
            import time
            time.sleep(0.1)

        # Make some POST requests
        for i in range(5):
            data = {"key": f"value_{i}", "index": i}
            response = session.post("https://httpbin.org/post", data=data)
            print(f"Request {i+11}: Status code {response.status_code}")

        # Make a request that will fail
        try:
            session.get("https://httpbin.org/status/404")
            print("Request 16: Status code 404")
        except requests.exceptions.HTTPError:
            print("Request 16: Failed with 404")

        # Make a request that will return 500
        try:
            session.get("https://httpbin.org/status/500")
            print("Request 17: Status code 500")
        except requests.exceptions.HTTPError:
            print("Request 17: Failed with 500")

        print("\n" + "="*50)
        print("Metrics Summary:")
        print("="*50)

        # Print the summary
        summary = stats.summary()
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Error Rate: {summary['error_rate']}%")
        print(f"Average Latency: {summary['avg_latency']:.4f} seconds")
        print(f"Minimum Latency: {summary['min_latency']:.4f} seconds")
        print(f"Maximum Latency: {summary['max_latency']:.4f} seconds")
        print(f"P50 Latency: {summary['p50_latency']:.4f} seconds")
        print(f"P95 Latency: {summary['p95_latency']:.4f} seconds")
        print(f"P99 Latency: {summary['p99_latency']:.4f} seconds")

        print("\n" + "-"*50)
        print("Status Code Distribution:")
        print("-"*50)

        # Print status code distribution
        status_dist = stats.status_distribution
        for status_code, count in sorted(status_dist.items()):
            print(f"Status {status_code}: {count} requests")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()