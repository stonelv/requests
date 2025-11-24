"""
requests.adapters_http2
~~~~~~~~~~~~~~~~~~~~~~

This module contains the HTTP/2 Transport Adapter for Requests.

Provides HTTP/2 support for Requests sessions using the hyper library.
"""

import socket
import typing
import warnings
import time
from threading import Lock

from .auth import _basic_auth_str
from .compat import basestring, urlparse
from .cookies import extract_cookies_to_jar
from .exceptions import (
    ConnectionError,
    ConnectTimeout,
    InvalidHeader,
    InvalidProxyURL,
    InvalidSchema,
    InvalidURL,
    ProxyError,
    ReadTimeout,
    RetryError,
    SSLError,
)
from .models import Response
from .structures import CaseInsensitiveDict
from .utils import (
    DEFAULT_CA_BUNDLE_PATH,
    extract_zipped_paths,
    get_auth_from_url,
    get_encoding_from_headers,
    prepend_scheme_if_needed,
    select_proxy,
    urldefragauth,
)

# Try to import httpx libraries

try:
    import httpx
    from httpx import HTTP20Connection, HTTP20Adapter
    from httpx.tls import init_context
    from httpx.exceptions import (
        ConnectionError as HttpxConnectionError,
        ConnectTimeoutError,
        HTTPError,
        InvalidCertificateError,
        ProtocolError as HttpxProtocolError,
        ReadTimeoutError as HttpxReadTimeoutError,
        SSLError as HttpxSSLError,
        StreamResetError,
    )
    from httpx.http20.exceptions import StreamError
    
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    
    # Define dummy exceptions for when httpx is not available
    class HttpxConnectionError(Exception):
        pass
        
    class ConnectTimeoutError(Exception):
        pass
        
    class HTTPError(Exception):
        pass
        
    class InvalidCertificateError(Exception):
        pass
        
    class HttpxProtocolError(Exception):
        pass
        
    class HttpxReadTimeoutError(Exception):
        pass
        
    class HttpxSSLError(Exception):
        pass
        
    class StreamResetError(Exception):
        pass
        
    class StreamError(Exception):
        pass

from .http2_connection import HTTP2ConnectionPoolManager
DEFAULT_POOLBLOCK = False
DEFAULT_POOLSIZE = 10
DEFAULT_RETRIES = 0
DEFAULT_POOL_TIMEOUT = None
DEFAULT_MAX_CONCURRENT_STREAMS = 100
DEFAULT_INITIAL_WINDOW_SIZE = 65535

class HTTP2Adapter:
    """
    HTTP/2 Transport Adapter for Requests.
    
    Provides HTTP/2 support with auto ALPN negotiation, connection pooling,
    stream multiplexing, and other HTTP/2 features.
    
    :param pool_connections: The number of connection pools to cache.
    :param pool_maxsize: The maximum number of connections to save in the pool.
    :param max_retries: The maximum number of retries each connection should attempt.
    :param pool_block: Whether the connection pool should block for connections.
    :param max_concurrent_streams: Maximum number of concurrent streams per connection.
    :param initial_window_size: Initial flow control window size.
    :param enable_push: Whether to enable server push (PUSH_PROMISE support).
    :param metrics_callback: Callback function to receive performance metrics.
    
    Usage:
      >>> import requests
      >>> from requests.adapters_http2 import HTTP2Adapter
      >>> s = requests.Session()
      >>> s.mount('https://', HTTP2Adapter())
      >>> response = s.get('https://http2.akamai.com/')
      >>> print(response.raw.version)
      (2, 0)
    """
    
    __attrs__ = [
        "max_retries",
        "config",
        "_pool_connections",
        "_pool_maxsize",
        "_pool_block",
        "_max_concurrent_streams",
        "_initial_window_size",
        "_enable_push",
        "_metrics_callback",
    ]
    
    def __init__(
        self,
        pool_connections=DEFAULT_POOLSIZE,
        pool_maxsize=DEFAULT_POOLSIZE,
        max_retries=DEFAULT_RETRIES,
        pool_block=DEFAULT_POOLBLOCK,
        max_concurrent_streams=DEFAULT_MAX_CONCURRENT_STREAMS,
        initial_window_size=DEFAULT_INITIAL_WINDOW_SIZE,
        enable_push=False,
        metrics_callback=None,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("HTTP/2 support requires the 'httpx' library. Please install it with 'pip install httpx'.")
            
        self.max_retries = max_retries
        self.config = {}
        self._pool_connections = pool_connections
        self._pool_maxsize = pool_maxsize
        self._pool_block = pool_block
        self._max_concurrent_streams = max_concurrent_streams
        self._initial_window_size = initial_window_size
        self._enable_push = enable_push
        self._metrics_callback = metrics_callback
        
        # Connection pool manager
        self._pool_manager = HTTP2ConnectionPoolManager(
            pool_connections=self._pool_connections,
            pool_maxsize=self._pool_maxsize,
            max_concurrent_streams=self._max_concurrent_streams,
            initial_window_size=self._initial_window_size,
            enable_push=self._enable_push,
        )
        
        # Initialize TLS context
        self._tls_context = init_context()
    
    def __getstate__(self):
        return {attr: getattr(self, attr, None) for attr in self.__attrs__}
    
    def __setstate__(self, state):
        self.config = {}
        self._connection_pool = {}
        self._pool_lock = Lock()
        
        for attr, value in state.items():
            setattr(self, attr, value)
        
        # Reinitialize TLS context
        self._tls_context = init_context()
    
    def get_connection(self, request, verify=True, cert=None, proxies=None):
        """
        Returns a HTTP/2 connection for the given request.
        
        :param request: The :class:`PreparedRequest <PreparedRequest>` object to be sent.
        :param verify: Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use.
        :param cert: Any user-provided SSL certificate for client authentication.
        :param proxies: A dictionary of schemes or schemes and hosts to proxy URLs.
        :rtype: hyper.HTTP20Connection
        """
        parsed_url = urlparse(request.url)
        scheme = parsed_url.scheme.lower()
        host = parsed_url.hostname
        port = parsed_url.port or (443 if scheme == 'https' else 80)
        
        # Handle proxies (not yet implemented)
        proxy = select_proxy(request.url, proxies)
        if proxy:
            raise NotImplementedError("Proxy support for HTTP/2 is not yet implemented.")
        
        # Configure TLS verification
        ssl_context = self._tls_context.copy()
        if verify is False:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        elif isinstance(verify, str):
            cert_loc = extract_zipped_paths(verify)
            if not os.path.exists(cert_loc):
                raise OSError(f"Could not find a suitable TLS CA certificate bundle, invalid path: {cert_loc}")
            ssl_context.load_verify_locations(cert_loc)
        
        # Configure client certificate
        if cert:
            if isinstance(cert, tuple) and len(cert) == 2:
                ssl_context.load_cert_chain(cert[0], cert[1])
            else:
                ssl_context.load_cert_chain(cert)
        
        # Get connection pool
        pool = self._pool_manager.get_pool(
            host=host,
            port=port,
            secure=scheme == 'https',
            ssl_context=ssl_context,
        )
        
        # Get connection from pool
        return pool.get_connection()
    
    def send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    ):
        """
        Sends PreparedRequest object. Returns Response object.
        
        :param request: The :class:`PreparedRequest <PreparedRequest>` being sent.
        :param stream: (optional) Whether to stream the request content.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param verify: (optional) Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use
        :param cert: (optional) Any user-provided SSL certificate to be trusted.
        :param proxies: (optional) The proxies dictionary to apply to the request.
        :rtype: requests.Response
        """
        start_time = time.time()
        
        try:
            conn = self.get_connection(request, verify=verify, cert=cert, proxies=proxies)
        except (ValueError, OSError) as e:
            raise InvalidURL(str(e), request=request)
        
        # Prepare request
        url = request.path_url
        headers = request.headers
        body = request.body
        
        # Convert headers to dictionary if needed
        if not isinstance(headers, dict):
            headers = dict(headers.items())
        
        # Remove Hop-by-Hop headers
        hop_by_hop = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade']
        for header in hop_by_hop:
            headers.pop(header, None)
        
        # Handle timeout
        connect_timeout = timeout
        read_timeout = timeout
        if isinstance(timeout, tuple):
            connect_timeout, read_timeout = timeout
        
        # Start timer
        request_start = time.time()
        
        try:
            # Connect if not already connected
            if not conn.connected:
                conn.connect(timeout=connect_timeout)
            
            # Send request
            stream_id = conn.request(
                request.method,
                url,
                body=body,
                headers=headers,
                end_stream=True
            )
            
            # Receive response
            resp = conn.get_response(stream_id, timeout=read_timeout)
            
        except ConnectTimeoutError as e:
            raise ConnectTimeout(str(e), request=request)
        except HttpxReadTimeoutError as e:
            raise ReadTimeout(str(e), request=request)
        except HttpxSSLError as e:
            raise SSLError(str(e), request=request)
        except (HttpxConnectionError, HttpxProtocolError, StreamResetError, StreamError, socket.error) as e:
            raise ConnectionError(str(e), request=request)
        except HTTPError as e:
            raise
        
        # Calculate metrics
        request_end = time.time()
        duration = request_end - request_start
        
        # Call metrics callback if provided
        if self._metrics_callback is not None:
            self._metrics_callback({
                'url': request.url,
                'method': request.method,
                'status': resp.status,
                'duration': duration,
                'stream_id': stream_id,
                'protocol': 'HTTP/2',
            })
        
        # Build requests.Response object
        response = Response()
        response.status_code = resp.status
        response.headers = CaseInsensitiveDict(resp.headers)
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = resp.reason
        response.url = request.url
        response.request = request
        response.connection = self
        
        # Extract cookies
        extract_cookies_to_jar(response.cookies, request, resp)
        
        return response
    
    def close(self):
        """
        Closes all connections in the pool.
        """
        self._pool_manager.close()

# Import ssl at the end to avoid circular imports
try:
    import ssl
except ImportError:
    pass