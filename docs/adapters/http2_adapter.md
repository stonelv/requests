# HTTP/2 Adapter for Requests

The HTTP2Adapter provides HTTP/2 support for the Requests library with automatic ALPN negotiation, connection reuse, stream-level timeouts, and comprehensive metrics collection.

## Features

- **Automatic ALPN Negotiation**: Automatically negotiates HTTP/2 using ALPN (Application-Layer Protocol Negotiation)
- **Connection Reuse**: Maintains persistent HTTP/2 connections with proper connection pooling
- **Stream-Level Timeouts**: Configurable timeouts for individual HTTP/2 streams
- **Metrics Collection**: Comprehensive metrics for monitoring connection performance
- **Fallback Support**: Automatic fallback to HTTP/1.1 when HTTP/2 is unavailable
- **Concurrent Streams**: Configurable maximum concurrent streams per connection
- **Flow Control**: Configurable initial window size for flow control
- **Server Push**: Experimental support for HTTP/2 server push

## Installation

The HTTP2Adapter requires the `h2` package for HTTP/2 support:

```bash
pip install h2
```

## Basic Usage

### Simple HTTP/2 Request

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Create a session with HTTP2Adapter
session = requests.Session()
http2_adapter = HTTP2Adapter()
session.mount('https://', http2_adapter)

# Make HTTP/2 request
response = session.get('https://example.com')
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
```

### Advanced Configuration

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Configure HTTP2Adapter with custom settings
http2_adapter = HTTP2Adapter(
    pool_connections=10,              # Maximum connections to cache
    pool_maxsize=100,                 # Maximum concurrent streams per connection
    max_concurrent_streams=100,       # HTTP/2 max concurrent streams
    initial_window_size=65535,       # Flow control window size
    enable_push=False,               # Disable server push
    stream_timeout=30,               # Timeout per stream
    fallback_to_http11=True         # Fallback to HTTP/1.1 if needed
)

session = requests.Session()
session.mount('https://', http2_adapter)

response = session.get('https://example.com')
```

## Configuration Options

### HTTP2Adapter Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pool_connections` | int | 10 | Maximum number of HTTP/2 connections to cache |
| `pool_maxsize` | int | 100 | Maximum number of concurrent streams per connection |
| `max_retries` | int | 0 | Maximum number of retries for failed requests |
| `max_concurrent_streams` | int | 100 | Maximum concurrent streams per HTTP/2 connection |
| `initial_window_size` | int | 65535 | Initial flow control window size |
| `enable_push` | bool | False | Enable HTTP/2 server push (experimental) |
| `stream_timeout` | float/tuple | None | Timeout for individual streams |
| `metrics_callback` | callable | None | Callback function for metrics collection |
| `fallback_to_http11` | bool | True | Fallback to HTTP/1.1 if HTTP/2 unavailable |

## Concurrent Requests

The HTTP2Adapter excels at handling concurrent requests:

```python
import requests
import concurrent.futures
from requests.adapters_http2 import HTTP2Adapter

def make_request(url):
    session = requests.Session()
    http2_adapter = HTTP2Adapter(max_concurrent_streams=50)
    session.mount('https://', http2_adapter)
    
    try:
        response = session.get(url, timeout=30)
        return {
            'url': url,
            'status': response.status_code,
            'content_length': len(response.content)
        }
    finally:
        session.close()

# URLs to test
urls = [
    'https://www.google.com',
    'https://www.github.com',
    'https://www.cloudflare.com',
    'https://www.akamai.com',
    'https://www.fastly.com'
]

# Make concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(make_request, url) for url in urls]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

for result in results:
    print(f"{result['url']}: Status {result['status']}, {result['content_length']} bytes")
```

## Metrics Collection

Monitor HTTP/2 connection performance with built-in metrics:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

def metrics_callback(metrics):
    """Process connection metrics."""
    print(f"Streams opened: {metrics['streams_opened']}")
    print(f"Streams closed: {metrics['streams_closed']}")
    print(f"Frames sent: {metrics['frames_sent']}")
    print(f"Frames received: {metrics['frames_received']}")
    print(f"Bytes sent: {metrics['bytes_sent']}")
    print(f"Bytes received: {metrics['bytes_received']}")
    print(f"Connection errors: {metrics['connection_errors']}")
    print(f"Stream errors: {metrics['stream_errors']}")

# Create adapter with metrics callback
http2_adapter = HTTP2Adapter(metrics_callback=metrics_callback)
session = requests.Session()
session.mount('https://', http2_adapter)

# Make requests
response = session.get('https://example.com')

# Get aggregated metrics
final_metrics = http2_adapter.get_metrics()
print(f"Total connections: {final_metrics['connections']}")
```

## Error Handling and Fallback

The HTTP2Adapter provides robust error handling with automatic fallback:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Enable fallback to HTTP/1.1
http2_adapter = HTTP2Adapter(fallback_to_http11=True)
session = requests.Session()
session.mount('https://', http2_adapter)

# This will use HTTP/2 if available, HTTP/1.1 otherwise
response = session.get('https://example.com')

# Non-HTTPS URLs automatically use HTTP/1.1 fallback
response = session.get('http://example.com')
```

## Stream-Level Timeouts

Configure timeouts for individual HTTP/2 streams:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Set stream timeout
http2_adapter = HTTP2Adapter(stream_timeout=30)
session = requests.Session()
session.mount('https://', http2_adapter)

# Request with custom timeout
response = session.get('https://example.com', timeout=45)

# Timeout can be a tuple: (connect_timeout, read_timeout)
http2_adapter = HTTP2Adapter(stream_timeout=(5, 30))
```

## Connection Pooling

The HTTP2Adapter maintains a pool of persistent connections:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Configure connection pool
http2_adapter = HTTP2Adapter(
    pool_connections=10,    # Maximum different hosts
    pool_maxsize=100       # Maximum streams per host
)

session = requests.Session()
session.mount('https://', http2_adapter)

# Multiple requests to the same host reuse the connection
for i in range(10):
    response = session.get(f'https://example.com/page{i}')
    print(f"Request {i}: Status {response.status_code}")
```

## ALPN Negotiation

The HTTP2Adapter automatically handles ALPN negotiation:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# ALPN negotiation happens automatically
http2_adapter = HTTP2Adapter()
session = requests.Session()
session.mount('https://', http2_adapter)

# If the server supports HTTP/2, it will be used
response = session.get('https://http2.example.com')

# If the server doesn't support HTTP/2, fallback to HTTP/1.1
response = session.get('https://http1-only.example.com')
```

## Server Push Support (Experimental)

Enable experimental HTTP/2 server push support:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Enable server push
http2_adapter = HTTP2Adapter(enable_push=True)
session = requests.Session()
session.mount('https://', http2_adapter)

# Server push resources will be handled automatically
response = session.get('https://example.com')
```

## SSL/TLS Configuration

Configure SSL verification and client certificates:

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# SSL verification
http2_adapter = HTTP2Adapter()
session = requests.Session()
session.mount('https://', http2_adapter)

# Disable SSL verification
response = session.get('https://example.com', verify=False)

# Custom CA bundle
response = session.get('https://example.com', verify='/path/to/ca-bundle.crt')

# Client certificate
response = session.get('https://example.com', cert=('/path/to/cert.pem', '/path/to/key.pem'))
```

## Performance Considerations

### Connection Reuse
- HTTP/2 connections are automatically reused when possible
- Connection pooling reduces handshake overhead
- Streams are multiplexed over existing connections

### Concurrent Streams
- Configure `max_concurrent_streams` based on server capabilities
- Higher values allow more concurrent requests per connection
- Balance between concurrency and resource usage

### Flow Control
- `initial_window_size` affects flow control behavior
- Larger windows allow more data in flight
- Adjust based on network conditions and server capabilities

### Memory Usage
- Each connection maintains state for active streams
- Monitor memory usage with high concurrency
- Use connection limits to control resource usage

## Troubleshooting

### HTTP/2 Not Available
If HTTP/2 is not available:

1. Check that the server supports HTTP/2
2. Verify ALPN negotiation is working
3. Ensure SSL/TLS is properly configured
4. Check fallback to HTTP/1.1 is enabled

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

http2_adapter = HTTP2Adapter(fallback_to_http11=True)
session = requests.Session()
session.mount('https://', http2_adapter)

# Check if HTTP/2 was used
metrics = http2_adapter.get_metrics()
print(f"Connections: {metrics['connections']}")
print(f"Streams opened: {metrics['streams_opened']}")
```

### Connection Issues
For connection problems:

1. Check network connectivity
2. Verify SSL certificates
3. Review timeout settings
4. Monitor connection metrics

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for HTTP/2
logger = logging.getLogger('requests.http2_connection')
logger.setLevel(logging.DEBUG)
```

### Performance Issues
For performance problems:

1. Monitor connection metrics
2. Adjust concurrent stream limits
3. Optimize timeout settings
4. Check server capabilities

## Examples

See the `examples/http2_multi_request.py` file for a comprehensive example demonstrating:
- Basic HTTP/2 usage
- Concurrent requests
- Metrics collection
- Error handling
- Connection pooling

## API Reference

### HTTP2Adapter

The main adapter class that provides HTTP/2 support.

#### Methods

- `send(request, stream=False, timeout=None, verify=True, cert=None, proxies=None)` - Send a request using HTTP/2
- `close()` - Close all HTTP/2 connections
- `get_metrics()` - Get aggregated metrics from all connections

#### Properties

- `max_concurrent_streams` - Maximum concurrent streams per connection
- `initial_window_size` - Initial flow control window size
- `enable_push` - Server push support status
- `stream_timeout` - Default stream timeout

### HTTP2Connection

Internal connection manager for HTTP/2 connections.

#### Methods

- `connect(verify=True, cert=None)` - Establish HTTP/2 connection with ALPN negotiation
- `create_stream()` - Create a new HTTP/2 stream
- `send_headers(stream_id, headers, end_stream=False)` - Send headers on a stream
- `send_data(stream_id, data, end_stream=False)` - Send data on a stream
- `close()` - Close the connection

### HTTP2Stream

Represents an individual HTTP/2 stream.

#### Methods

- `send_headers(headers, end_stream=False)` - Send headers
- `send_data(data, end_stream=False)` - Send data
- `wait_for_response(timeout=None)` - Wait for response completion
- `mark_complete()` - Mark stream as complete

### HTTP2Metrics

Metrics collector for HTTP/2 connections.

#### Methods

- `get_stats()` - Get current metrics statistics

#### Metrics Available

- `streams_opened` - Number of streams opened
- `streams_closed` - Number of streams closed
- `frames_sent` - Number of frames sent
- `frames_received` - Number of frames received
- `bytes_sent` - Bytes sent
- `bytes_received` - Bytes received
- `connection_errors` - Connection errors
- `stream_errors` - Stream errors
- `uptime` - Connection uptime

## Compatibility

### Requirements
- Python 3.6+
- `h2` package for HTTP/2 support
- SSL/TLS support for HTTPS connections

### Browser Compatibility
The HTTP2Adapter is compatible with servers that support HTTP/2, including:
- Modern web servers (nginx, Apache, etc.)
- CDN providers (Cloudflare, Akamai, Fastly)
- Cloud services (Google Cloud, AWS, Azure)

### Limitations
- HTTPS only (HTTP/2 requires TLS in most implementations)
- Server push support is experimental
- Some advanced HTTP/2 features may not be available

## Contributing

Contributions are welcome! Please see the main Requests project for contribution guidelines.

## License

This HTTP2Adapter is part of the Requests project and follows the same license terms.