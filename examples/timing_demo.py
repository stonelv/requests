#!/usr/bin/env python3
"""
Requests Timing Extension Demo

This script demonstrates the usage of the Requests timing extension for
profiling HTTP requests and analyzing performance statistics.
"""

import time
import requests
from requests.timing import ProfilerSession, attach_profiler


def demo_profiler_session():
    """Demonstrate using ProfilerSession for automatic request timing."""
    print("=== ProfilerSession Demo ===")
    print("Creating a ProfilerSession with automatic timing...")
    
    # Create a profiler session with a maximum of 50 records
    session = ProfilerSession(max_records=50)
    
    # Make some sample requests
    urls = [
        'https://httpbin.org/get',
        'https://httpbin.org/delay/1',
        'https://httpbin.org/status/200',
        'https://httpbin.org/status/404',
        'https://httpbin.org/json',
        'https://httpbin.org/html',
        'https://httpbin.org/delay/2',
    ]
    
    print(f"Making {len(urls)} requests...")
    for url in urls:
        try:
            print(f"  Requesting: {url}")
            response = session.get(url, timeout=10)
            print(f"    Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"    Error: {e}")
        
        # Small delay between requests
        time.sleep(0.1)
    
    # Get and display statistics
    print("\n=== Request Statistics ===")
    stats = session.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Successful requests: {stats['count'] - stats['error_count']}")
    print(f"Failed requests: {stats['error_count']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    
    if stats['count'] > 0:
        print(f"\nTiming Statistics:")
        print(f"  Average duration: {stats['avg_duration_ms']:.2f} ms")
        print(f"  Minimum duration: {stats['min_duration_ms']:.2f} ms")
        print(f"  Maximum duration: {stats['max_duration_ms']:.2f} ms")
        print(f"  Average TTFB: {stats['avg_ttfb_ms']:.2f} ms")
        print(f"  Minimum TTFB: {stats['min_ttfb_ms']:.2f} ms")
        print(f"  Maximum TTFB: {stats['max_ttfb_ms']:.2f} ms")
    
    print(f"\nStatus Code Distribution:")
    for status_code, count in sorted(stats['status_code_distribution'].items()):
        print(f"  {status_code}: {count}")
    
    # Export to CSV
    print("\n=== CSV Export ===")
    csv_filename = 'request_timing_demo.csv'
    success = session.export_csv(csv_filename)
    if success:
        print(f"Timing data exported to {csv_filename}")
        print(f"File size: {os.path.getsize(csv_filename)} bytes")
    else:
        print("Failed to export timing data")
    
    return session


def demo_attach_profiler():
    """Demonstrate attaching timing to an existing session."""
    print("\n=== Attach Profiler Demo ===")
    print("Creating a regular session and attaching timing...")
    
    # Create a regular session with custom configuration
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'TimingDemo/1.0',
        'Accept': 'application/json',
    })
    session.timeout = 15
    
    print(f"Original session timeout: {session.timeout}")
    print(f"Original session headers: {dict(session.headers)}")
    
    # Attach timing capabilities
    profiler_session = attach_profiler(session, max_records=20)
    
    print(f"Profiler session timeout: {profiler_session.timeout}")
    print(f"Profiler session headers: {dict(profiler_session.headers)}")
    
    # Make some requests
    test_urls = [
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
        'https://httpbin.org/ip',
    ]
    
    print("\nMaking requests with attached profiler...")
    for url in test_urls:
        try:
            response = profiler_session.get(url)
            print(f"  {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  {url}: ERROR - {e}")
    
    # Show stats
    stats = profiler_session.get_stats()
    print(f"\nAttached profiler stats:")
    print(f"  Requests made: {stats['count']}")
    print(f"  Average duration: {stats['avg_duration_ms']:.2f} ms")
    
    return profiler_session


def demo_circular_buffer():
    """Demonstrate circular buffer behavior."""
    print("\n=== Circular Buffer Demo ===")
    print("Testing circular buffer with max_records=5...")
    
    session = ProfilerSession(max_records=5)
    
    # Make more requests than the buffer can hold
    for i in range(10):
        url = f'https://httpbin.org/delay/{i % 3}'  # Varying delays
        try:
            response = session.get(url, timeout=10)
            print(f"  Request {i+1}: {url} -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  Request {i+1}: {url} -> ERROR")
        
        # Small delay between requests
        time.sleep(0.1)
    
    print(f"\nBuffer capacity: 5")
    print(f"Total requests made: 10")
    print(f"Records in buffer: {len(session)}")
    
    # Show which records are kept
    records = session.get_records()
    print("Records in buffer (oldest to newest):")
    for i, record in enumerate(records):
        print(f"  {i+1}. {record.method} {record.url} - {record.status_code} ({record.duration_ms:.2f}ms)")
    
    return session


def demo_error_handling():
    """Demonstrate error handling and failed requests."""
    print("\n=== Error Handling Demo ===")
    print("Testing error handling with various problematic URLs...")
    
    session = ProfilerSession(max_records=20)
    
    # Test various error conditions
    test_cases = [
        ('https://httpbin.org/status/500', 'Server Error'),
        ('https://httpbin.org/status/503', 'Service Unavailable'),
        ('https://httpbin.org/delay/10', 'Timeout (will be cancelled)'),
    ]
    
    for url, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"URL: {url}")
        
        try:
            # Use a short timeout to trigger timeout errors
            response = session.get(url, timeout=2)
            print(f"Response: {response.status_code}")
        except requests.exceptions.Timeout:
            print("Exception: Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"Exception: {type(e).__name__}: {e}")
    
    # Show final statistics
    stats = session.get_stats()
    print(f"\n=== Final Statistics ===")
    print(f"Total requests: {stats['count']}")
    print(f"Successful requests: {stats['count'] - stats['error_count']}")
    print(f"Failed requests: {stats['error_count']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    
    return session


def main():
    """Main demo function."""
    print("Requests Timing Extension Demo")
    print("=" * 50)
    
    try:
        # Run all demos
        session1 = demo_profiler_session()
        session2 = demo_attach_profiler()
        session3 = demo_circular_buffer()
        session4 = demo_error_handling()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nFeatures demonstrated:")
        print("- Automatic request timing with ProfilerSession")
        print("- Attaching timing to existing sessions")
        print("- Circular buffer behavior for memory efficiency")
        print("- Error handling and failed request tracking")
        print("- Statistical analysis of request performance")
        print("- CSV export for further analysis")
        
        # Clean up CSV file
        csv_file = 'request_timing_demo.csv'
        if os.path.exists(csv_file):
            print(f"\nCSV file '{csv_file}' has been created in the current directory.")
            print("You can open it with Excel or any spreadsheet application.")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import os
    main()