import logging
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.models import Response
from .record import TimingRecord

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

class TimingAdapter(HTTPAdapter):
    """
    An HTTP adapter that records timing information for each request.
    
    Records:
    - Start time
    - Duration in milliseconds
    - Time to first byte (TTFB) in milliseconds
    - Status code
    - Content length
    """
    send_counter = 0  # Class-level counter for debugging
    
    def __init__(self, profiler=None, *args, **kwargs):
        print(f"TimingAdapter.__init__ called with profiler: {profiler}")
        super().__init__(*args, **kwargs)
        self.profiler = profiler
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        TimingAdapter.send_counter += 1
        print(f"TimingAdapter.send was called! Counter: {TimingAdapter.send_counter}")
        # Initialize response to None to handle exceptions
        response = None
        
        # Record start time
        start_time = datetime.now()
        start_time_ms = start_time.timestamp() * 1000
        
        # Send the request
        try:
            response = super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)
            logging.debug(f"After super.send: response={response}")
        except Exception:
            # If request fails, we still want to record timing information
            raise
        finally:
            # Calculate duration
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Calculate TTFB
            ttfb_ms = 0
            if response is not None and hasattr(response, 'elapsed'):
                ttfb_ms = response.elapsed.total_seconds() * 1000
            
            # Get content length
            content_length = 0
            if response is not None and hasattr(response, 'headers') and 'Content-Length' in response.headers:
                try:
                    content_length = int(response.headers['Content-Length'])
                except (ValueError, TypeError):
                    pass
            
            # Get status code
            status_code = response.status_code if (response is not None and hasattr(response, 'status_code')) else 0
            
            # Create timing record
            record = TimingRecord(
                start_time=start_time,
                duration_ms=duration_ms,
                ttfb_ms=ttfb_ms,
                status_code=status_code,
                content_length=content_length,
                url=request.url
            )
            
            logging.debug(f"Record: {record}")
            
            # Attach record to response if it exists
            if response is not None:
                logging.debug(f"Attaching record to response: {response}")
                response.timing_record = record
                logging.debug(f"Response now has timing_record: {hasattr(response, 'timing_record')}")
            
            # Add record to the profiler if available
            if self.profiler is not None:
                self.profiler.add_record(record)
        
        return response
