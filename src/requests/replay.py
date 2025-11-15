import enum
import hashlib
import json
import os
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .models import Request, Response
from .exceptions import RequestException


class ReplayMode(enum.Enum):
    OFF = "off"
    RECORD = "record"
    REPLAY = "replay"
    AUTO = "auto"


class ReplayMissError(RequestException):
    """Exception raised when a request cannot be matched in replay mode."""
    def __init__(self, request: Request, differences: List[str], *args, **kwargs):
        self.request = request
        self.differences = differences
        message = f"Replay miss for request: {request.method} {request.url}. Differences: {', '.join(differences)}"
        super().__init__(message, *args, **kwargs)


class RecordingWriteError(RequestException):
    """Exception raised when recording cannot be written to storage."""


class RedactionError(RequestException):
    """Exception raised when sensitive data redaction fails."""


class StoreCorruptionError(RequestException):
    """Exception raised when recording storage is corrupted."""


class RecordingStore:
    """Abstract base class for recording storage."""
    def save(self, key: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Save a recorded request-response pair."""
        raise NotImplementedError

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a recorded response for a given key."""
        raise NotImplementedError


class FileRecordingStore(RecordingStore):
    """File system implementation of RecordingStore."""
    def __init__(self, base_path: str = ".requests_recordings"):
        self.base_path = os.path.abspath(base_path)
        self._lock = threading.RLock()
        
        # Ensure base directory exists
        with self._lock:
            os.makedirs(self.base_path, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Generate file path from key."""
        return os.path.join(self.base_path, f"{key}.json")

    def save(self, key: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Save a recorded request-response pair to a JSON file."""
        recording = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request": request_data,
            "response": response_data
        }
        file_path = self._get_file_path(key)
        
        with self._lock:
            with open(file_path, "w") as f:
                json.dump(recording, f, indent=2, default=str)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a recorded response from a JSON file."""
        file_path = self._get_file_path(key)
        
        with self._lock:
            if not os.path.exists(file_path):
                return None
            
            try:
                with open(file_path, "r") as f:
                    recording = json.load(f)
                return recording["response"]
            except (json.JSONDecodeError, KeyError, IOError) as e:
                raise StoreCorruptionError(f"Failed to load recording: {e}") from e


def normalize_url(url: str) -> str:
    """Normalize URL for consistent matching."""
    # TODO: Implement URL normalization logic
    return url


def hash_request_body(body: Any) -> str:
    """Generate a hash of the request body."""
    if body is None:
        return ""
    
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    elif hasattr(body, "read"):
        # Handle file-like objects
        body_bytes = body.read()
        # Rewind the file pointer
        body.seek(0)
    else:
        # Convert to JSON string for other types
        body_bytes = json.dumps(body, sort_keys=True).encode("utf-8")
    
    return hashlib.sha256(body_bytes).hexdigest()


def redact_sensitive_headers(headers: Dict[str, str], sensitive_headers: List[str]) -> Dict[str, str]:
    """Redact sensitive headers."""
    redacted = dict(headers)
    for header in sensitive_headers:
        if header in redacted:
            redacted[header] = "[REDACTED]"
    return redacted


def generate_request_key(method: str, url: str, headers: Dict[str, str], body: Any,
                       sensitive_headers: List[str] = None, ignore_body: bool = False) -> str:
    """Generate a unique key for the request."""
    if sensitive_headers is None:
        sensitive_headers = []
    
    # Normalize method and URL
    normalized_method = method.upper()
    normalized_url = normalize_url(url)
    
    # Redact and sort headers
    redacted_headers = redact_sensitive_headers(headers, sensitive_headers)
    sorted_headers = sorted(redacted_headers.items())
    
    # Hash body if not ignored
    body_hash = "" if ignore_body else hash_request_body(body)
    
    # Generate composite key
    key_components = [
        normalized_method,
        normalized_url,
        json.dumps(sorted_headers),
        body_hash
    ]
    
    return hashlib.sha256("|" .join(key_components).encode("utf-8")).hexdigest()