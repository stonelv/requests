# HTTP2Adapter for Requests

The HTTP2Adapter is a plugin for the Requests library that adds support for HTTP/2 protocol.

## Features

- **Automatic ALPN Negotiation**: Automatically negotiates HTTP/2 with servers using ALPN.
- **Connection Reuse**: Reuses connections for multiple requests to the same host.
- **Stream-level Timeouts**: Supports timeouts at the stream level.
- **Basic Metrics Callback**: Provides a callback for collecting basic metrics.
- **Configurable Concurrent Streams**: Allows configuring the maximum number of concurrent streams per connection.
- **Configurable Window Size**: Allows configuring the initial window size for flow control.
- **Push Promise Support**: Supports handling server push promises (experimental).

## Installation

To use the HTTP2Adapter, you need to install the `hyper` library:

```bash
pip install hyper
```

## Usage

### Basic Usage

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

# Create a session
with requests.Session() as session:
    # Create an HTTP2Adapter instance
    adapter = HTTP2Adapter()
    
    # Mount the adapter to the session for HTTPS URLs
    session.mount('https://', adapter)
    
    # Send a request
    response = session.get('https://example.com')
    
    print(response.status_code)
    print(response.text)
```

### Advanced Configuration

```python
import requests
from requests.adapters_http2 import HTTP2Adapter

def metrics_callback(**kwargs):
    """Callback function to collect metrics."""
    print(f"Method: {kwargs['method']}")
    print(f"URL: {kwargs['url']}")
    print(f"Status: {kwargs['status']}")
    print(f"Duration: {kwargs['duration']:.3f}s")
    print(f"Stream ID: {kwargs['stream_id']}")

# Create a session
with requests.Session() as session:
    # Create an HTTP2Adapter instance with advanced configuration
    adapter = HTTP2Adapter(
        pool_connections=10,  # Number of connection pools
        pool_maxsize=10,      # Max connections per pool
        max_concurrent_streams=100,  # Max concurrent streams per connection
        initial_window_size=65536,   # Initial window size (bytes)
        enable_push=True,    # Enable push promise support
        metrics_callback=metrics_callback,  # Metrics callback
    )
    
    # Mount the adapter to the session for HTTPS and HTTP URLs
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    # Send a request
    response = session.get('https://example.com')
    
    print(response.status_code)
    print(response.text)
```

## API Reference

### HTTP2Adapter Class

#### Constructor

```python
HTTP2Adapter(
    pool_connections=DEFAULT_POOLSIZE,
    pool_maxsize=DEFAULT_POOLSIZE,
    max_concurrent_streams=100,
    initial_window_size=65536,
    enable_push=False,
    metrics_callback=None,
)
```

**Parameters:**
- `pool_connections`: Number of connection pools to cache (default: 10).
- `pool_maxsize`: Maximum number of connections to keep in each pool (default: 10).
- `max_concurrent_streams`: Maximum number of concurrent streams per connection (default: 100).
- `initial_window_size`: Initial window size for flow control (default: 65536 bytes).
- `enable_push`: Whether to enable server push promise support (default: False).
- `metrics_callback`: Callback function to collect basic metrics (default: None).

#### Methods

##### `send(request, stream=False, timeout=None, verify=True, cert=None, proxies=None)`

Sends a prepared request using HTTP/2.

**Parameters:**
- `request`: PreparedRequest object to send.
- `stream`: Whether to stream the response (default: False).
- `timeout`: Timeout in seconds (default: None).
- `verify`: Whether to verify the server's TLS certificate (default: True).
- `cert`: Client certificate to use (default: None).
- `proxies`: Dictionary of proxies to use (default: None).

**Returns:**
- Response object containing the server's response.

##### `close()`

Closes all connections in the pool.

## Metrics Callback

The metrics callback function is called for each request with the following parameters:

- `method`: HTTP method (e.g., 'GET', 'POST').
- `url`: Request URL.
- `status`: Response status code.
- `duration`: Request duration in seconds.
- `stream_id`: HTTP/2 stream ID.

## Limitations

- **Proxy Support**: Proxy support is not yet implemented.
- **HTTP/1.1 Fallback**: Fallback to HTTP/1.1 is not yet fully implemented. If HTTP/2 negotiation fails, the adapter will raise an error.

## Examples

See the `examples/http2_multi_request.py` file for an example of making multiple concurrent HTTP/2 requests.
