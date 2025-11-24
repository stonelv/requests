"""
requests.http2_connection
~~~~~~~~~~~~~~~~~~~~~~~~

This module contains HTTP/2 connection pooling implementation.
"""

import socket
import ssl
import time
from threading import Lock
from typing import Dict, Optional, Tuple

from .compat import urlparse
from .exceptions import ConnectionError, ConnectTimeout

# Try to import httpx libraries
try:
    import httpx
    from httpx import HTTP20Connection
    from httpx.tls import init_context
    from httpx.exceptions import (
        ConnectionError as HttpxConnectionError,
        ConnectTimeoutError,
        ProtocolError as HttpxProtocolError,
        StreamResetError,
    )
    from httpx.http20.exceptions import StreamError
    
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    
    # Define dummy classes for when httpx is not available
    class HTTP20Connection:
        pass
        
    def init_context():
        pass
        
    class HttpxConnectionError(Exception):
        pass
        
    class ConnectTimeoutError(Exception):
        pass
        
    class HttpxProtocolError(Exception):
        pass
        
    class StreamResetError(Exception):
        pass
        
    class StreamError(Exception):
        pass

class HTTP2ConnectionPool:
    """
    HTTP/2 connection pool implementation.
    
    Manages a pool of HTTP/2 connections for a specific host and port.
    Supports connection reuse and stream multiplexing.
    
    :param host: The host to connect to.
    :param port: The port to connect to.
    :param secure: Whether to use TLS (HTTPS).
    :param max_concurrent_streams: Maximum number of concurrent streams per connection.
    :param initial_window_size: Initial flow control window size.
    :param enable_push: Whether to enable server push.
    :param ssl_context: Custom SSL context to use.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 443,
        secure: bool = True,
        max_concurrent_streams: int = 100,
        initial_window_size: int = 65535,
        enable_push: bool = False,
        ssl_context: ssl.SSLContext = None,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("HTTP/2 support requires the 'httpx' library. Please install it with 'pip install httpx'.")
            
        self.host = host
        self.port = port
        self.secure = secure
        self.max_concurrent_streams = max_concurrent_streams
        self.initial_window_size = initial_window_size
        self.enable_push = enable_push
        self.ssl_context = ssl_context or init_context()
        
        # Connection pool - stores HTTP20Connection objects
        self._connections: Dict[Tuple[int, int], HTTP20Connection] = {}
        self._connection_lock = Lock()
        
        # Active streams counter
        self._active_streams: Dict[HTTP20Connection, int] = {}
        self._stream_lock = Lock()
    
    def get_connection(self, timeout: Optional[float] = None) -> HTTP20Connection:
        """
        Get an available HTTP/2 connection from the pool.
        
        :param timeout: Maximum time to wait for a connection (not implemented yet).
        :return: An available HTTP/2 connection.
        :raises: ConnectionError if no connection is available or could be created.
        """
        with self._connection_lock:
            # First try to reuse an existing connection
            for conn in self._connections.values():
                try:
                    # Check if connection is alive and has available streams
                    if conn.connected:
                        with self._stream_lock:
                            active_streams = self._active_streams.get(conn, 0)
                        if active_streams < self.max_concurrent_streams:
                            return conn
                except (HttpxConnectionError, HttpxProtocolError, socket.error):
                    # Connection is dead, remove it
                    self._remove_connection(conn)
            
            # If no available connection, create a new one
            conn = self._create_connection(timeout)
            self._connections[(conn.host, conn.port)] = conn
            self._active_streams[conn] = 0
            return conn
    
    def _create_connection(self, timeout: Optional[float] = None) -> HTTP20Connection:
        """
        Create a new HTTP/2 connection.
        
        :param timeout: Maximum time to wait for connection establishment.
        :return: A new HTTP/2 connection.
        :raises: ConnectionError or ConnectTimeout if connection fails.
        """
        try:
            conn = HTTP20Connection(
                self.host,
                self.port,
                secure=self.secure,
                window_size=self.initial_window_size,
                enable_push=self.enable_push,
                ssl_context=self.ssl_context,
            )
            
            # Connect to the server
            conn.connect(timeout=timeout)
            return conn
        except ConnectTimeoutError as e:
            raise ConnectTimeout(str(e)) from e
        except (HttpxConnectionError, HttpxProtocolError, socket.error) as e:
            raise ConnectionError(str(e)) from e
    
    def _remove_connection(self, conn: HTTP20Connection) -> None:
        """
        Remove a connection from the pool.
        
        :param conn: The connection to remove.
        """
        try:
            conn.close()
        except:
            pass
        
        key = (conn.host, conn.port)
        if key in self._connections:
            del self._connections[key]
        if conn in self._active_streams:
            del self._active_streams[conn]
    
    def increment_stream_count(self, conn: HTTP20Connection) -> None:
        """
        Increment the active stream count for a connection.
        
        :param conn: The connection to increment stream count for.
        """
        with self._stream_lock:
            self._active_streams[conn] = self._active_streams.get(conn, 0) + 1
    
    def decrement_stream_count(self, conn: HTTP20Connection) -> None:
        """
        Decrement the active stream count for a connection.
        
        :param conn: The connection to decrement stream count for.
        """
        with self._stream_lock:
            if conn in self._active_streams:
                self._active_streams[conn] -= 1
                if self._active_streams[conn] == 0:
                    # No more active streams, can keep connection in pool for reuse
                    pass
    
    def close(self) -> None:
        """
        Close all connections in the pool.
        """
        with self._connection_lock:
            for conn in self._connections.values():
                try:
                    conn.close()
                except:
                    pass
            self._connections.clear()
            self._active_streams.clear()

class HTTP2ConnectionPoolManager:
    """
    HTTP/2 connection pool manager.
    
    Manages a pool of HTTP/2 connection pools for different hosts and ports.
    
    :param pool_connections: Number of connection pools to cache.
    :param pool_maxsize: Maximum number of connections per pool.
    :param max_concurrent_streams: Maximum number of concurrent streams per connection.
    :param initial_window_size: Initial flow control window size.
    :param enable_push: Whether to enable server push.
    """
    
    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_concurrent_streams: int = 100,
        initial_window_size: int = 65535,
        enable_push: bool = False,
    ):
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        self.max_concurrent_streams = max_concurrent_streams
        self.initial_window_size = initial_window_size
        self.enable_push = enable_push
        
        # Pool of connection pools - maps (host, port) to HTTP2ConnectionPool
        self._pools: Dict[Tuple[str, int], HTTP2ConnectionPool] = {}
        self._pool_lock = Lock()
    
    def get_pool(
        self,
        host: str,
        port: int = 443,
        secure: bool = True,
        ssl_context: ssl.SSLContext = None,
    ) -> HTTP2ConnectionPool:
        """
        Get or create a connection pool for the specified host and port.
        
        :param host: The host to get a pool for.
        :param port: The port to get a pool for.
        :param secure: Whether to use TLS (HTTPS).
        :param ssl_context: Custom SSL context to use.
        :return: A connection pool for the specified host and port.
        """
        with self._pool_lock:
            key = (host, port)
            if key not in self._pools:
                # Create a new connection pool
                self._pools[key] = HTTP2ConnectionPool(
                    host,
                    port,
                    secure=secure,
                    max_concurrent_streams=self.max_concurrent_streams,
                    initial_window_size=self.initial_window_size,
                    enable_push=self.enable_push,
                    ssl_context=ssl_context,
                )
            return self._pools[key]
    
    def close(self) -> None:
        """
        Close all connection pools.
        """
        with self._pool_lock:
            for pool in self._pools.values():
                pool.close()
            self._pools.clear()