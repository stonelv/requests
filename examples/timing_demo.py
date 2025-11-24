"""
Demo of the Requests Timing Extension.

This demonstrates how to use the timing extension to record and analyze
request timing information.
"""
import time
from requests.timing import ProfilerSession, attach_profiler
from requests import Session

def demo_profiler_session():
    """Demo using ProfilerSession."""
    print("=== ProfilerSession Demo ===")
    
    # Create a ProfilerSession with max 10 records
    session = ProfilerSession(max_records=10)
    
    # Make multiple requests
    for i in range(5):
        print(f"Making request {i+1}/5...")
        response = session.get('https://httpbin.org/get')
        print(f"Status: {response.status_code}")
        print(f"Duration: {response.timing_record.duration_ms:.2f}ms")
        print(f"TTFB: {response.timing_record.ttfb_ms:.2f}ms")
        print(f"Content Length: {response.timing_record.content_length} bytes")
        print()
        time.sleep(0.2)  # Add small delay
    
    # Get and print statistics
    print("=== Statistics ===")
    stats = session.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Average duration: {stats['duration']['avg']:.2f}ms")
    print(f"Min duration: {stats['duration']['min']:.2f}ms")
    print(f"Max duration: {stats['duration']['max']:.2f}ms")
    print(f"Average TTFB: {stats['ttfb']['avg']:.2f}ms")
    print(f"Min TTFB: {stats['ttfb']['min']:.2f}ms")
    print(f"Max TTFB: {stats['ttfb']['max']:.2f}ms")
    print(f"Status code distribution: {stats['status_code_distribution']}")
    print()
    
    # Export to CSV
    print("Exporting to timing_records.csv...")
    session.export_csv('timing_records.csv')
    print("Export complete!")
    print()

def demo_attach_profiler():
    """Demo attaching profiler to an existing Session."""
    print("=== attach_profiler Demo ===")
    
    # Create a regular Session
    session = Session()
    
    # Attach profiler
    session = attach_profiler(session, max_records=5)
    
    # Make some requests
    for i in range(3):
        print(f"Making request {i+1}/3...")
        response = session.get('https://httpbin.org/headers')
        print(f"Status: {response.status_code}")
        print(f"Duration: {response.timing_record.duration_ms:.2f}ms")
        print()
    
    # Get statistics from attached profiler
    print("=== Statistics from Attached Profiler ===")
    stats = session.profiler.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Average duration: {stats['duration']['avg']:.2f}ms")
    print()

def demo_ring_buffer():
    """Demo ring buffer behavior."""
    print("=== Ring Buffer Demo ===")
    
    # Create a ProfilerSession with max 3 records
    session = ProfilerSession(max_records=3)
    
    # Make 5 requests
    for i in range(5):
        print(f"Making request {i+1}/5...")
        session.get('https://httpbin.org/ip')
        print(f"Current records count: {len(session.records)}")
        print()
    
    # Verify only last 3 records are kept
    print(f"Final records count: {len(session.records)}")
    print("Ring buffer is working correctly!")
    print()

if __name__ == '__main__':
    demo_profiler_session()
    demo_attach_profiler()
    demo_ring_buffer()
