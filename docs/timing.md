# Requests Timing Extension

The Requests Timing Extension is a lightweight extension for the Python Requests library that records timing information for each HTTP request. It provides:

- Request duration tracking
- Time-to-first-byte (TTFB) measurement
- Status code and content length recording
- Statistics calculation (average, min, max, distribution)
- CSV export of timing records
- Ring buffer for efficient memory usage

## Installation

The extension is included in the Requests library. To use it, import the timing module:

```python
import requests
from requests.timing import ProfilerSession, attach_profiler, TimingAdapter
```

## Usage

### 1. Using ProfilerSession

ProfilerSession is a subclass of Session that automatically records timing information for all requests:

```python
from requests.timing import ProfilerSession

# Create a ProfilerSession with max 200 records (default)
session = ProfilerSession()

# Make requests as usual
response = session.get('https://httpbin.org/get')

# Access timing information from the response
print(f"Duration: {response.timing_record.duration_ms:.2f}ms")
print(f"TTFB: {response.timing_record.ttfb_ms:.2f}ms")
print(f"Status: {response.timing_record.status_code}")
```

### 2. Attaching to Existing Session

You can also attach timing profiling to an existing Session:

```python
from requests import Session
from requests.timing import attach_profiler

# Create a regular Session
session = Session()

# Attach profiler with max 100 records
session = attach_profiler(session, max_records=100)

# Make requests
response = session.get('https://httpbin.org/get')

# Access timing information
print(f"Duration: {response.timing_record.duration_ms:.2f}ms")

# Access profiler from session
stats = session.profiler.get_stats()
```

### 3. Using TimingAdapter Directly

For more control, you can use TimingAdapter directly:

```python
from requests import Session
from requests.timing import TimingAdapter

# Create a regular Session
session = Session()

# Create and mount TimingAdapter
adapter = TimingAdapter()
session.mount('https://', adapter)

# Make requests
response = session.get('https://httpbin.org/get')

# Access timing information
print(f"Duration: {response.timing_record.duration_ms:.2f}ms")
```

## Statistics

The profiler provides statistics about recorded requests:

```python
from requests.timing import ProfilerSession

session = ProfilerSession()

# Make multiple requests
for i in range(5):
    session.get('https://httpbin.org/get')

# Get statistics
stats = session.get_stats()

print(f"Total requests: {stats['count']}")
print(f"Average duration: {stats['duration']['avg']:.2f}ms")
print(f"Min duration: {stats['duration']['min']:.2f}ms")
print(f"Max duration: {stats['duration']['max']:.2f}ms")
print(f"Average TTFB: {stats['ttfb']['avg']:.2f}ms")
print(f"Min TTFB: {stats['ttfb']['min']:.2f}ms")
print(f"Max TTFB: {stats['ttfb']['max']:.2f}ms")
print(f"Status code distribution: {stats['status_code_distribution']}")
```

## CSV Export

You can export timing records to a CSV file:

```python
from requests.timing import ProfilerSession

session = ProfilerSession()

# Make some requests
for i in range(10):
    session.get('https://httpbin.org/get')

# Export to CSV
session.export_csv('timing_records.csv')
```

The CSV file contains the following columns:
- `start_time`: ISO format timestamp of the request start
- `duration_ms`: Total duration of the request in milliseconds
- `ttfb_ms`: Time to first byte in milliseconds
- `status_code`: HTTP status code of the response
- `content_length`: Length of the response content in bytes
- `url`: The URL of the request

## Ring Buffer

The profiler uses a ring buffer to maintain a maximum number of records. When the buffer is full, the oldest records are discarded.

```python
# Create a profiler with max 10 records
session = ProfilerSession(max_records=10)

# Make 15 requests
for i in range(15):
    session.get('https://httpbin.org/get')

# Only the last 10 records are kept
print(f"Total records: {len(session.records)}")  # Output: 10
```

## API Reference

### ProfilerSession

#### Methods
- `__init__(self, max_records: int = 200)`: Initialize a new ProfilerSession.
- `get_stats(self) -> dict`: Get statistics from recorded requests.
- `export_csv(self, path: str)`: Export timing records to a CSV file.

### attach_profiler

#### Signature
```python
def attach_profiler(session: Session, max_records: int = 200) -> Session:
```

#### Parameters
- `session`: The Session to attach the profiler to.
- `max_records`: Maximum number of records to keep in the ring buffer.

#### Returns
- The modified Session with timing profiling attached.

### TimingAdapter

#### Methods
- `send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None)`: Send a request and record timing information.

### TimingRecord

#### Attributes
- `start_time`: datetime object representing the start time of the request.
- `duration_ms`: Total duration of the request in milliseconds.
- `ttfb_ms`: Time to first byte in milliseconds.
- `status_code`: HTTP status code of the response.
- `content_length`: Length of the response content in bytes.
- `url`: The URL of the request.

#### Methods
- `to_dict(self) -> dict`: Convert the record to a dictionary for serialization.

## Testing

To run the tests for the timing extension:

```bash
python -m unittest tests.test_timing
python -m unittest tests.test_timing_stats
```

## Examples

Check out the `examples/timing_demo.py` file for a complete demo of the timing extension.
