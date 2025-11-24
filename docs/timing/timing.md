# Requests Timing Extension

A lightweight profiling extension for the Requests library that provides comprehensive timing and performance analysis capabilities for HTTP requests.

## Overview

The Requests Timing Extension adds transparent timing capabilities to HTTP requests without affecting the existing API. It automatically records:

- Request start time
- Total request duration (in milliseconds)
- Time to first byte (TTFB) (in milliseconds)
- HTTP response status codes
- Response content length
- Error information for failed requests

## Features

- **Automatic Timing**: Seamlessly integrates with existing Requests code
- **Circular Buffer**: Memory-efficient storage with configurable maximum records
- **Statistical Analysis**: Comprehensive performance metrics and analysis
- **CSV Export**: Export timing data for external analysis
- **Error Tracking**: Detailed error information for failed requests
- **Status Code Distribution**: Analyze HTTP response patterns
- **Zero API Impact**: Maintains full compatibility with existing Requests API

## Installation

The timing extension is included as part of the Requests library. Simply import and use:

```python
from requests.timing import ProfilerSession, attach_profiler
```

## Quick Start

### Using ProfilerSession

The easiest way to start timing requests is to use `ProfilerSession` instead of the regular `Session`:

```python
from requests.timing import ProfilerSession

# Create a profiler session with automatic timing
session = ProfilerSession(max_records=200)

# Use it exactly like a regular session
response = session.get('https://api.example.com/data')
print(f"Status: {response.status_code}")

# Get performance statistics
stats = session.get_stats()
print(f"Average duration: {stats['avg_duration_ms']:.2f} ms")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### Attaching to Existing Session

You can also add timing capabilities to an existing session:

```python
import requests
from requests.timing import attach_profiler

# Create and configure your existing session
session = requests.Session()
session.headers.update({'User-Agent': 'MyApp/1.0'})
session.timeout = 30

# Attach timing capabilities
profiler_session = attach_profiler(session, max_records=100)

# Use the enhanced session
response = profiler_session.get('https://api.example.com/data')
```

## API Reference

### ProfilerSession

A session class that automatically times all HTTP requests.

```python
ProfilerSession(max_records=200, *args, **kwargs)
```

**Parameters:**
- `max_records` (int): Maximum number of timing records to keep in memory (default: 200)
- `*args, **kwargs`: Arguments passed to the parent Session class

**Methods:**

#### get_stats()
Get comprehensive statistics about all recorded requests.

```python
stats = session.get_stats()
print(stats)
# Output:
# {
#     'count': 50,
#     'avg_duration_ms': 234.56,
#     'min_duration_ms': 45.23,
#     'max_duration_ms': 1200.89,
#     'avg_ttfb_ms': 123.45,
#     'min_ttfb_ms': 23.45,
#     'max_ttfb_ms': 567.89,
#     'status_code_distribution': {200: 45, 404: 3, 500: 2},
#     'error_count': 0,
#     'success_rate': 90.0
# }
```

#### export_csv(path, include_errors=True)
Export timing records to a CSV file for external analysis.

```python
success = session.export_csv('request_timings.csv')
if success:
    print("Timing data exported successfully")
```

**Parameters:**
- `path` (str): Path to the output CSV file
- `include_errors` (bool): Whether to include failed requests (default: True)

**Returns:**
- `bool`: True if export was successful, False otherwise

#### get_records()
Get a list of all timing records.

```python
records = session.get_records()
for record in records:
    print(f"{record.method} {record.url}: {record.duration_ms:.2f}ms")
```

#### clear_records()
Clear all timing records from memory.

```python
session.clear_records()
print(f"Records after clear: {len(session)}")  # 0
```

### attach_profiler()

Attach timing capabilities to an existing session.

```python
attach_profiler(session, max_records=200)
```

**Parameters:**
- `session` (requests.Session): Existing session to enhance
- `max_records` (int): Maximum number of timing records (default: 200)

**Returns:**
- `ProfilerSession`: New profiler session with timing capabilities

### RequestRecord

A data class representing a single request's timing information.

**Attributes:**
- `url` (str): The request URL
- `method` (str): HTTP method (GET, POST, etc.)
- `start_time` (float): Unix timestamp when request started
- `duration_ms` (float): Total request duration in milliseconds
- `ttfb_ms` (float): Time to first byte in milliseconds
- `status_code` (int): HTTP response status code
- `content_length` (int): Length of response content in bytes
- `error` (str): Error message if request failed

## Examples

### Basic Usage

```python
from requests.timing import ProfilerSession

session = ProfilerSession()

# Make some requests
for url in ['https://httpbin.org/get', 'https://httpbin.org/delay/1']:
    response = session.get(url)
    print(f"Got response: {response.status_code}")

# Analyze performance
stats = session.get_stats()
print(f"Made {stats['count']} requests")
print(f"Average response time: {stats['avg_duration_ms']:.2f} ms")
```

### Advanced Analysis

```python
from requests.timing import ProfilerSession
import matplotlib.pyplot as plt

session = ProfilerSession(max_records=1000)

# Make many requests to analyze patterns
for i in range(100):
    session.get(f'https://httpbin.org/delay/{i % 5}')

# Get detailed statistics
stats = session.get_stats()

# Analyze status code distribution
status_codes = stats['status_code_distribution']
print("Status code breakdown:")
for code, count in sorted(status_codes.items()):
    percentage = (count / stats['count']) * 100
    print(f"  {code}: {count} ({percentage:.1f}%)")

# Export for external analysis
session.export_csv('performance_analysis.csv')
```

### Error Handling and Monitoring

```python
from requests.timing import ProfilerSession
import time

def monitor_api_health():
    session = ProfilerSession(max_records=500)
    
    while True:
        try:
            response = session.get('https://api.example.com/health')
            stats = session.get_stats()
            
            # Alert if success rate drops below 95%
            if stats['success_rate'] < 95:
                print(f"WARNING: Success rate dropped to {stats['success_rate']:.1f}%")
            
            # Alert if average response time exceeds 1 second
            if stats['avg_duration_ms'] > 1000:
                print(f"WARNING: Average response time is {stats['avg_duration_ms']:.2f} ms")
            
        except Exception as e:
            print(f"Error during monitoring: {e}")
        
        time.sleep(60)  # Check every minute
```

### Performance Testing

```python
from requests.timing import ProfilerSession
import concurrent.futures

def load_test_api():
    session = ProfilerSession(max_records=1000)
    
    def make_request(i):
        try:
            return session.get(f'https://api.example.com/endpoint/{i}')
        except Exception as e:
            return None
    
    # Simulate concurrent load
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(100)]
        concurrent.futures.wait(futures)
    
    # Analyze results
    stats = session.get_stats()
    print(f"Total requests: {stats['count']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average duration: {stats['avg_duration_ms']:.2f} ms")
    print(f"95th percentile: {stats['max_duration_ms']:.2f} ms")
    
    # Export detailed results
    session.export_csv('load_test_results.csv')
```

## CSV Export Format

The CSV export includes the following columns:

| Column | Description |
|--------|-------------|
| timestamp | Unix timestamp when request started |
| method | HTTP method (GET, POST, etc.) |
| url | Request URL |
| status_code | HTTP response status code |
| duration_ms | Total request duration in milliseconds |
| ttfb_ms | Time to first byte in milliseconds |
| content_length | Response content length in bytes |
| error | Error message if request failed |

## Best Practices

1. **Memory Management**: Use appropriate `max_records` values based on your needs. The circular buffer automatically manages memory usage.

2. **Production Use**: Consider exporting data periodically to avoid memory issues with long-running applications.

3. **Error Monitoring**: Regularly check the `error_count` and `success_rate` metrics for API health monitoring.

4. **Performance Analysis**: Use the CSV export feature to analyze trends and patterns over time.

5. **Integration**: The extension maintains full API compatibility, so existing code requires no changes.

## Limitations

- Timing precision depends on system clock resolution
- Memory usage scales with the number of stored records
- TTFB measurement may vary based on network conditions
- Does not measure DNS resolution time separately

## Troubleshooting

### No Timing Data

Ensure you're using `ProfilerSession` or a session enhanced with `attach_profiler()`:

```python
# Wrong - regular session won't collect timing
session = requests.Session()

# Correct - profiler session collects timing
session = ProfilerSession()
```

### Memory Issues

Reduce the `max_records` parameter or periodically clear records:

```python
session = ProfilerSession(max_records=50)  # Smaller buffer
# or
session.clear_records()  # Clear periodically
```

### CSV Export Fails

Check file permissions and directory existence:

```python
import os
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
session.export_csv(csv_path)
```

## Contributing

This extension is part of the Requests library. See the main Requests documentation for contribution guidelines.

## License

This extension follows the same license as the Requests library.