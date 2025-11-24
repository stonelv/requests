"""
requests.http2_connection
~~~~~~~~~~~~~~~~~~~~~~

This module contains HTTP/2 connection management for the HTTP2Adapter.
"""

import logging
import socket
import ssl
import threading
import time
from collections import defaultdict
from typing import Dict, Optional, Callable, Any, List, Tuple
from urllib.parse import urlparse

try:
    import h2.connection
    import h2.events
    import h2.exceptions
    import h2.config
    H2_AVAILABLE = True
except ImportError:
    H2_AVAILABLE = False

from .exceptions import ConnectionError, ConnectTimeout, ReadTimeout


logger = logging.getLogger(__name__)


class HTTP2Metrics:
    """HTTP/2 connection metrics collector."""
    
    def __init__(self):
        self.streams_opened = 0
        self.streams_closed = 0
        self.frames_sent = 0
        self.frames_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.connection_errors = 0
        self.stream_errors = 0
        self.start_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        return {
            'streams_opened': self.streams_opened,
            'streams_closed': self.streams_closed,
            'frames_sent': self.frames_sent,
            'frames_received': self.frames_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'connection_errors': self.connection_errors,
            'stream_errors': self.stream_errors,
            'uptime': time.time() - self.start_time
        }


class HTTP2Stream:
    """Represents a single HTTP/2 stream."""
    
    def __init__(self, stream_id: int, connection: 'HTTP2Connection'):
        self.stream_id = stream_id
        self.connection = connection
        self.state = 'idle'
        self.request_headers = {}
        self.response_headers = {}
        self.response_data = b''
        self.response_status = None
        self.error = None
        self._complete = threading.Event()
        self._lock = threading.Lock()
    
    def send_headers(self, headers: Dict[str, str], end_stream: bool = False):
        """Send headers on this stream."""
        with self._lock:
            self.request_headers = headers
            self.state = 'open'
            self.connection.send_headers(self.stream_id, headers, end_stream)
    
    def send_data(self, data: bytes, end_stream: bool = False):
        """Send data on this stream."""
        with self._lock:
            self.connection.send_data(self.stream_id, data, end_stream)
    
    def wait_for_response(self, timeout: Optional[float] = None) -> bool:
        """Wait for response completion."""
        return self._complete.wait(timeout)
    
    def mark_complete(self):
        """Mark stream as complete."""
        self.state = 'closed'
        self._complete.set()
        self.connection.metrics.streams_closed += 1
    
    def add_response_data(self, data: bytes):
        """Add response data."""
        self.response_data += data
    
    def set_response_headers(self, headers: List[Tuple[str, str]]):
        """Set response headers."""
        self.response_headers = dict(headers)
        for name, value in headers:
            if name == ':status':
                self.response_status = int(value)
                break


class HTTP2Connection:
    """HTTP/2 connection manager with ALPN negotiation and connection reuse."""
    
    def __init__(
        self,
        host: str,
        port: int,
        max_concurrent_streams: int = 100,
        initial_window_size: int = 65535,
        enable_push: bool = False,
        metrics_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        timeout: Optional[float] = None
    ):
        if not H2_AVAILABLE:
            raise ImportError("hyper-h2 is required for HTTP/2 support")
        
        self.host = host
        self.port = port
        self.max_concurrent_streams = max_concurrent_streams
        self.initial_window_size = initial_window_size
        self.enable_push = enable_push
        self.metrics_callback = metrics_callback
        self.timeout = timeout
        
        self._socket = None
        self._ssl_context = None
        self._h2_conn = None
        self._streams: Dict[int, HTTP2Stream] = {}
        self._next_stream_id = 1
        self._lock = threading.RLock()
        self._connected = False
        self._connection_thread = None
        self._should_stop = threading.Event()
        
        self.metrics = HTTP2Metrics()
        
        # H2 configuration
        self._h2_config = h2.config.H2Configuration(
            client_side=True,
            header_encoding='utf-8',
            validate_inbound_headers=True,
            normalize_inbound_headers=True,
            validate_outbound_headers=True,
            normalize_outbound_headers=True
        )
    
    def _create_ssl_context(self, verify: bool = True, cert: Optional[str] = None):
        """Create SSL context with ALPN negotiation."""
        context = ssl.create_default_context()
        
        if not verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        if cert:
            context.load_cert_chain(cert)
        
        # Set ALPN protocols for HTTP/2 negotiation
        context.set_alpn_protocols(['h2', 'http/1.1'])
        
        return context
    
    def connect(self, verify: bool = True, cert: Optional[str] = None) -> bool:
        """Connect to the server with ALPN negotiation."""
        try:
            # Create socket
            self._socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout
            )
            
            # Create SSL context and wrap socket
            self._ssl_context = self._create_ssl_context(verify, cert)
            self._socket = self._ssl_context.wrap_socket(
                self._socket,
                server_hostname=self.host
            )
            
            # Check ALPN negotiation result
            negotiated_protocol = self._socket.selected_alpn_protocol()
            
            if negotiated_protocol != 'h2':
                logger.warning(f"HTTP/2 not negotiated, got: {negotiated_protocol}")
                self._socket.close()
                self._socket = None
                return False
            
            # Initialize HTTP/2 connection
            self._h2_conn = h2.connection.H2Connection(config=self._h2_config)
            self._h2_conn.initiate_connection()
            
            # Send initial connection preface
            self._send_pending_data()
            
            self._connected = True
            
            # Start connection handling thread
            self._connection_thread = threading.Thread(target=self._handle_connection)
            self._connection_thread.daemon = True
            self._connection_thread.start()
            
            logger.info(f"HTTP/2 connection established to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.metrics.connection_errors += 1
            self._cleanup()
            return False
    
    def _send_pending_data(self):
        """Send pending data from HTTP/2 connection."""
        data_to_send = self._h2_conn.data_to_send()
        if data_to_send:
            self._socket.sendall(data_to_send)
            self.metrics.bytes_sent += len(data_to_send)
            self.metrics.frames_sent += 1
    
    def _handle_connection(self):
        """Handle incoming HTTP/2 frames."""
        while not self._should_stop.is_set() and self._connected:
            try:
                # Read data from socket
                data = self._socket.recv(65536)
                if not data:
                    break
                
                self.metrics.bytes_received += len(data)
                
                # Feed data to HTTP/2 connection
                events = self._h2_conn.receive_data(data)
                self.metrics.frames_received += 1
                
                # Process events
                for event in events:
                    self._handle_event(event)
                
                # Send any pending data
                self._send_pending_data()
                
            except Exception as e:
                logger.error(f"Connection handling error: {e}")
                self.metrics.connection_errors += 1
                break
        
        self._cleanup()
    
    def _handle_event(self, event):
        """Handle HTTP/2 events."""
        if isinstance(event, h2.events.ResponseReceived):
            self._handle_response_received(event)
        elif isinstance(event, h2.events.DataReceived):
            self._handle_data_received(event)
        elif isinstance(event, h2.events.StreamEnded):
            self._handle_stream_ended(event)
        elif isinstance(event, h2.events.StreamReset):
            self._handle_stream_reset(event)
        elif isinstance(event, h2.events.PushedStreamReceived):
            self._handle_push_promise(event)
        elif isinstance(event, h2.events.SettingsAcknowledged):
            logger.debug("Settings acknowledged")
        elif isinstance(event, h2.events.PingAckReceived):
            logger.debug("Ping acknowledged")
    
    def _handle_response_received(self, event):
        """Handle response headers received."""
        stream = self._streams.get(event.stream_id)
        if stream:
            stream.set_response_headers(event.headers)
    
    def _handle_data_received(self, event):
        """Handle response data received."""
        stream = self._streams.get(event.stream_id)
        if stream:
            stream.add_response_data(event.data)
            
            # Acknowledge data received
            self._h2_conn.acknowledge_received_data(
                event.flow_controlled_length,
                event.stream_id
            )
    
    def _handle_stream_ended(self, event):
        """Handle stream end."""
        stream = self._streams.get(event.stream_id)
        if stream:
            stream.mark_complete()
    
    def _handle_stream_reset(self, event):
        """Handle stream reset."""
        stream = self._streams.get(event.stream_id)
        if stream:
            stream.error = f"Stream reset: {event.error_code}"
            stream.mark_complete()
            self.metrics.stream_errors += 1
    
    def _handle_push_promise(self, event):
        """Handle server push promise."""
        if self.enable_push:
            logger.info(f"Push promise received for stream {event.pushed_stream_id}")
            # TODO: Implement push promise handling
        else:
            # Reject push promise
            self._h2_conn.reset_stream(event.pushed_stream_id)
    
    def create_stream(self) -> HTTP2Stream:
        """Create a new HTTP/2 stream."""
        with self._lock:
            stream_id = self._next_stream_id
            self._next_stream_id += 2  # Client uses odd stream IDs
            
            stream = HTTP2Stream(stream_id, self)
            self._streams[stream_id] = stream
            self.metrics.streams_opened += 1
            
            return stream
    
    def send_headers(self, stream_id: int, headers: Dict[str, str], end_stream: bool = False):
        """Send headers on a stream."""
        # Convert headers to HTTP/2 format
        h2_headers = [(name.lower(), str(value)) for name, value in headers.items()]
        
        self._h2_conn.send_headers(stream_id, h2_headers, end_stream)
        self._send_pending_data()
    
    def send_data(self, stream_id: int, data: bytes, end_stream: bool = False):
        """Send data on a stream."""
        self._h2_conn.send_data(stream_id, data, end_stream)
        self._send_pending_data()
    
    def get_stream(self, stream_id: int) -> Optional[HTTP2Stream]:
        """Get stream by ID."""
        return self._streams.get(stream_id)
    
    def is_connected(self) -> bool:
        """Check if connection is established."""
        return self._connected and self._socket is not None
    
    def _cleanup(self):
        """Clean up connection resources."""
        self._connected = False
        self._should_stop.set()
        
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        
        # Don't join current thread from within itself
        if (self._connection_thread and 
            self._connection_thread.is_alive() and 
            self._connection_thread != threading.current_thread()):
            self._connection_thread.join(timeout=1.0)
        
        # Notify metrics callback
        if self.metrics_callback:
            try:
                self.metrics_callback(self.metrics.get_stats())
            except:
                pass
    
    def close(self):
        """Close the connection."""
        with self._lock:
            if self._h2_conn:
                try:
                    self._h2_conn.close_connection()
                    self._send_pending_data()
                except:
                    pass
            
            self._cleanup()


class HTTP2ConnectionPool:
    """Pool of HTTP/2 connections with connection reuse."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections: Dict[Tuple[str, int], HTTP2Connection] = {}
        self._lock = threading.Lock()
    
    def get_connection(
        self,
        host: str,
        port: int,
        max_concurrent_streams: int = 100,
        initial_window_size: int = 65535,
        enable_push: bool = False,
        metrics_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        timeout: Optional[float] = None
    ) -> Optional[HTTP2Connection]:
        """Get or create HTTP/2 connection."""
        key = (host, port)
        
        with self._lock:
            conn = self._connections.get(key)
            
            if conn and conn.is_connected():
                return conn
            
            # Create new connection
            conn = HTTP2Connection(
                host=host,
                port=port,
                max_concurrent_streams=max_concurrent_streams,
                initial_window_size=initial_window_size,
                enable_push=enable_push,
                metrics_callback=metrics_callback,
                timeout=timeout
            )
            
            self._connections[key] = conn
            return conn
    
    def remove_connection(self, host: str, port: int):
        """Remove connection from pool."""
        key = (host, port)
        
        with self._lock:
            conn = self._connections.pop(key, None)
            if conn:
                conn.close()
    
    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()