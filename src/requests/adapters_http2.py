"""
requests.adapters_http2
~~~~~~~~~~~~~~~~~~~~~

This module contains the HTTP2Adapter for HTTP/2 support in Requests.
"""

import logging
import time
from typing import Optional, Callable, Dict, Any, Union
from urllib.parse import urlparse

from .adapters import BaseAdapter
from .http2_connection import HTTP2ConnectionPool, HTTP2Connection, HTTP2Stream
from .models import Response
from .exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    InvalidSchema,
    SSLError
)
from .structures import CaseInsensitiveDict
from .utils import DEFAULT_CA_BUNDLE_PATH, extract_zipped_paths
from .compat import basestring


try:
    from .http2_connection import H2_AVAILABLE
except ImportError:
    H2_AVAILABLE = False


logger = logging.getLogger(__name__)


class HTTP2Adapter(BaseAdapter):
    """
    HTTP/2 Transport Adapter for Requests.
    
    Provides HTTP/2 support with automatic ALPN negotiation, connection reuse,
    stream-level timeouts, and configurable concurrency.
    
    :param pool_connections: Maximum number of HTTP/2 connections to cache.
    :param pool_maxsize: Maximum number of concurrent streams per connection.
    :param max_retries: Maximum number of retries for failed requests.
    :param max_concurrent_streams: Maximum concurrent streams per connection.
    :param initial_window_size: Initial flow control window size.
    :param enable_push: Enable server push support (experimental).
    :param stream_timeout: Default timeout for individual streams.
    :param metrics_callback: Callback for connection metrics.
    :param fallback_to_http11: Whether to fallback to HTTP/1.1 if HTTP/2 is not available.
    
    Usage::
    
      >>> import requests
      >>> from requests.adapters_http2 import HTTP2Adapter
      >>> s = requests.Session()
      >>> adapter = HTTP2Adapter(max_concurrent_streams=100)
      >>> s.mount('https://', adapter)
      >>> response = s.get('https://http2.example.com')
    """
    
    __attrs__ = [
        "max_retries",
        "max_concurrent_streams",
        "initial_window_size",
        "enable_push",
        "stream_timeout",
        "metrics_callback",
        "fallback_to_http11",
        "_pool_connections",
        "_pool_maxsize",
    ]
    
    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 100,
        max_retries: int = 0,
        max_concurrent_streams: int = 100,
        initial_window_size: int = 65535,
        enable_push: bool = False,
        stream_timeout: Optional[Union[float, tuple]] = None,
        metrics_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        fallback_to_http11: bool = True
    ):
        if not H2_AVAILABLE:
            raise ImportError(
                "HTTP/2 support requires hyper-h2 package. "
                "Install it with: pip install h2"
            )
        
        super().__init__()
        
        self.max_retries = max_retries
        self.max_concurrent_streams = max_concurrent_streams
        self.initial_window_size = initial_window_size
        self.enable_push = enable_push
        self.stream_timeout = stream_timeout
        self.metrics_callback = metrics_callback
        self.fallback_to_http11 = fallback_to_http11
        
        self._pool_connections = pool_connections
        self._pool_maxsize = pool_maxsize
        
        # Initialize connection pool
        self._connection_pool = HTTP2ConnectionPool(max_connections=pool_connections)
        
        # Fallback adapter for HTTP/1.1
        if fallback_to_http11:
            from .adapters import HTTPAdapter
            self._fallback_adapter = HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=max_retries
            )
        else:
            self._fallback_adapter = None
    
    def __getstate__(self):
        return {attr: getattr(self, attr, None) for attr in self.__attrs__}
    
    def __setstate__(self, state):
        super().__init__()
        for attr, value in state.items():
            setattr(self, attr, value)
        
        self._connection_pool = HTTP2ConnectionPool(
            max_connections=self._pool_connections
        )
        
        if self.fallback_to_http11:
            from .adapters import HTTPAdapter
            self._fallback_adapter = HTTPAdapter(
                pool_connections=self._pool_connections,
                pool_maxsize=self._pool_maxsize,
                max_retries=self.max_retries
            )
        else:
            self._fallback_adapter = None
    
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """
        Send a PreparedRequest object using HTTP/2.
        
        :param request: The PreparedRequest being sent.
        :param stream: (optional) Whether to stream the request content.
        :param timeout: (optional) Timeout for the request.
        :param verify: (optional) SSL verification.
        :param cert: (optional) Client certificate.
        :param proxies: (optional) Proxy configuration.
        :return: Response object.
        """
        # Parse URL
        parsed = urlparse(request.url)
        
        # Only support HTTPS for HTTP/2
        if parsed.scheme != 'https':
            if self.fallback_to_http11 and self._fallback_adapter:
                return self._fallback_adapter.send(
                    request, stream, timeout, verify, cert, proxies
                )
            else:
                raise InvalidSchema(f"HTTP/2 requires HTTPS, got: {parsed.scheme}")
        
        # Extract host and port
        host = parsed.hostname
        port = parsed.port or 443
        
        # Determine timeout
        if timeout is None:
            timeout = self.stream_timeout
        
        # Convert timeout to float if it's a tuple
        if isinstance(timeout, (tuple, list)):
            timeout = timeout[1] if len(timeout) > 1 else timeout[0]
        
        # Get or create connection
        connection = self._connection_pool.get_connection(
            host=host,
            port=port,
            max_concurrent_streams=self.max_concurrent_streams,
            initial_window_size=self.initial_window_size,
            enable_push=self.enable_push,
            metrics_callback=self.metrics_callback,
            timeout=timeout
        )
        
        if not connection:
            raise ConnectionError(f"Failed to get HTTP/2 connection to {host}:{port}")
        
        # Connect if not already connected
        if not connection.is_connected():
            verify_ssl = self._get_verify_value(verify)
            cert_file = self._get_cert_file(cert)
            
            connected = connection.connect(verify=verify_ssl, cert=cert_file)
            
            if not connected:
                # Connection failed, try fallback
                if self.fallback_to_http11 and self._fallback_adapter:
                    return self._fallback_adapter.send(
                        request, stream, timeout, verify, cert, proxies
                    )
                else:
                    raise ConnectionError(f"Failed to establish HTTP/2 connection to {host}:{port}")
        
        # Create stream
        h2_stream = connection.create_stream()
        
        try:
            # Build HTTP/2 headers
            headers = self._build_http2_headers(request, parsed)
            
            # Send request
            self._send_request(h2_stream, headers, request.body)
            
            # Wait for response
            if not h2_stream.wait_for_response(timeout=timeout):
                raise ReadTimeout(f"Stream timeout after {timeout}s")
            
            # Build response
            response = self._build_response(request, h2_stream)
            
            return response
            
        except Exception as e:
            logger.error(f"HTTP/2 request failed: {e}")

            # Clean up stream on error
            try:
                if hasattr(connection, '_streams') and h2_stream.stream_id in connection._streams:
                    del connection._streams[h2_stream.stream_id]
            except (AttributeError, TypeError):
                # Handle cases where connection._streams might not be available
                pass
            
            raise
    
    def _get_verify_value(self, verify):
        """Convert verify parameter to SSL verification value."""
        if verify is True:
            return True
        elif verify is False:
            return False
        elif isinstance(verify, str):
            return verify
        else:
            return True
    
    def _get_cert_file(self, cert):
        """Extract certificate file path from cert parameter."""
        if not cert:
            return None
        
        if isinstance(cert, (tuple, list)) and len(cert) > 0:
            return cert[0]  # First item is cert file
        elif isinstance(cert, str):
            return cert
        else:
            return None
    
    def _build_http2_headers(self, request, parsed):
        """Build HTTP/2 headers from request."""
        headers = []
        
        # Add pseudo-headers
        headers.append((':method', request.method.upper()))
        headers.append((':scheme', parsed.scheme))
        headers.append((':authority', parsed.netloc))
        headers.append((':path', parsed.path or '/'))
        
        if parsed.query:
            headers[-1] = (':path', f"{parsed.path or '/'}?{parsed.query}")
        
        # Add regular headers
        for name, value in request.headers.items():
            # Skip connection-specific headers
            if name.lower() not in ['connection', 'keep-alive', 'proxy-connection',
                                   'transfer-encoding', 'upgrade', 'te']:
                headers.append((name.lower(), str(value)))
        
        return headers
    
    def _send_request(self, stream, headers, body):
        """Send HTTP/2 request."""
        # Send headers
        end_stream = body is None
        stream.send_headers(dict(headers), end_stream=end_stream)
        
        # Send body if present
        if body is not None:
            if isinstance(body, str):
                body = body.encode('utf-8')
            elif isinstance(body, bytes):
                pass
            else:
                # For file-like objects, read the content
                if hasattr(body, 'read'):
                    body = body.read()
                else:
                    body = str(body).encode('utf-8')
            
            stream.send_data(body, end_stream=True)
    
    def _build_response(self, request, h2_stream):
        """Build Response object from HTTP/2 stream."""
        response = Response()
        
        # Set status code
        response.status_code = h2_stream.response_status or 200
        
        # Set headers
        response.headers = CaseInsensitiveDict(h2_stream.response_headers)
        
        # Set response data
        response._content = h2_stream.response_data
        
        # Set URL
        response.url = request.url
        
        # Set request
        response.request = request
        
        # Set connection
        response.connection = self
        
        return response
    
    def close(self):
        """Close all HTTP/2 connections."""
        self._connection_pool.close_all()
        
        if self._fallback_adapter:
            self._fallback_adapter.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all connections."""
        total_metrics = {
            'streams_opened': 0,
            'streams_closed': 0,
            'frames_sent': 0,
            'frames_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connection_errors': 0,
            'stream_errors': 0,
            'connections': 0
        }
        
        # Collect metrics from all connections
        for conn in self._connection_pool._connections.values():
            stats = conn.metrics.get_stats()
            for key in total_metrics:
                if key in stats:
                    total_metrics[key] += stats[key]
            total_metrics['connections'] += 1
        
        return total_metrics