import csv
import logging
from collections import deque, defaultdict
from requests import Session
from requests.adapters import HTTPAdapter
from .adapter import TimingAdapter

class Profiler:
    """
    Manages timing records and provides statistics/export functionality.
    
    Maintains a ring buffer of up to N timing records and supports getting
    performance statistics and exporting records to CSV.
    """
    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self.records = deque(maxlen=max_records)
    
    def add_record(self, record):
        """Add a timing record to the ring buffer."""
        self.records.append(record)
        
    def get_stats(self) -> dict:
        """
        Get statistics from the timing records.
        
        Returns:
            dict: Statistics including count, average, min, max for duration and TTFB,
                  and a status code distribution.
        """
        if not self.records:
            return {
                'count': 0,
                'duration': {'avg': 0, 'min': 0, 'max': 0},
                'ttfb': {'avg': 0, 'min': 0, 'max': 0},
                'status_code_distribution': {}
            }
            
        durations = [r.duration_ms for r in self.records]
        ttfb_values = [r.ttfb_ms for r in self.records]
        status_codes = [r.status_code for r in self.records]
        
        # Calculate duration stats
        duration_stats = {
            'avg': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations)
        }
        
        # Calculate TTFB stats
        ttfb_stats = {
            'avg': sum(ttfb_values) / len(ttfb_values),
            'min': min(ttfb_values),
            'max': max(ttfb_values)
        }
        
        # Calculate status code distribution
        status_dist = defaultdict(int)
        for code in status_codes:
            status_dist[code] += 1
        
        return {
            'count': len(self.records),
            'duration': duration_stats,
            'ttfb': ttfb_stats,
            'status_code_distribution': dict(status_dist)
        }
        
    def export_csv(self, path: str):
        """
        Export timing records to a CSV file.
        
        Args:
            path (str): The path to the CSV file to create.
        """
        if not self.records:
            return
            
        # Get headers from the first record
        headers = list(self.records[0].to_dict().keys())
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for record in self.records:
                writer.writerow(record.to_dict())

class ProfilerSession(Session):
    """
    A Session that automatically records timing information for each request.
    
    Uses a separate Profiler instance to manage records and statistics.
    """
    def __init__(self, max_records: int = 200):
        super().__init__()
        self.profiler = Profiler(max_records=max_records)
        
        # Replace default adapters with TimingAdapter
        self._init_timing_adapters()
        
    def _init_timing_adapters(self):
        """Initialize TimingAdapter for all protocols."""
        logging.debug("ProfilerSession._init_timing_adapters called")
        # Clear existing adapters to ensure TimingAdapter is used
        self.adapters.clear()
        for protocol in ['http://', 'https://']:
            adapter = TimingAdapter()
            adapter.profiler = self.profiler  # Attach profiler to adapter
            self.mount(protocol, adapter)
            
    def add_record(self, record):
        """Add a timing record to the profiler's ring buffer."""
        self.profiler.add_record(record)
        
    def get_stats(self) -> dict:
        """Get statistics from the profiler's records."""
        return self.profiler.get_stats()
        
    def export_csv(self, path: str):
        """Export timing records from the profiler to a CSV file."""
        self.profiler.export_csv(path)
                
def attach_profiler(session: Session, max_records: int = 200) -> Session:
    """
    Attach timing profiling to an existing Session.
    
    Args:
        session (Session): The session to attach the profiler to.
        max_records (int): Maximum number of records to keep in the ring buffer.
    
    Returns:
        Session: The modified session with timing profiling.
    """
    # Create a profiler to manage records
    profiler = Profiler(max_records=max_records)
    
    # Replace existing adapters with TimingAdapter
    for protocol in ['http://', 'https://']:
        # Get existing adapter (if any) to preserve configuration
        existing_adapter = session.adapters.get(protocol, None)
        if existing_adapter:
            # Create a new TimingAdapter with similar configuration
            adapter = TimingAdapter(
                pool_connections=existing_adapter._pool_connections,
                pool_maxsize=existing_adapter._pool_maxsize,
                max_retries=existing_adapter.max_retries,
                pool_block=existing_adapter._pool_block
            )
        else:
            # Use default configuration
            adapter = TimingAdapter()
            
        # Attach profiler to adapter
        adapter.profiler = profiler
        
        # Mount the adapter
        session.mount(protocol, adapter)
        
    # Attach profiler to session
    session.profiler = profiler
    
    return session
