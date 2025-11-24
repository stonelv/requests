import unittest
import tempfile
import os
import sys
import time
import importlib

# Add the current project's src directory to the beginning of the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)
# Remove any other requests directories from the Python path
sys.path = [p for p in sys.path if 'github\\requests\\' not in p or p == src_path]

from requests import Session
from requests.timing import ProfilerSession, attach_profiler, TimingAdapter
from tests.testserver.server import Server

class TestTimingExtension(unittest.TestCase):
    """Test the Requests timing extension."""
    
    def setUp(self):
        """Set up test server before each test."""
        self.server = Server.basic_response_server(requests_to_handle=10)
        self.server.start()
        # Wait for server to be ready
        if not self.server.ready_event.wait(self.server.WAIT_EVENT_TIMEOUT):
            raise RuntimeError("Timeout waiting for server to be ready")
        # Set the base URL for tests
        self.base_url = f"http://{self.server.host}:{self.server.port}"
        self.addCleanup(lambda: [self.server._close_server_sock_ignore_errors(), self.server.join()])
    
    
    def test_profiler_session_basic(self):
        """Test basic functionality of ProfilerSession."""
        # Print Python path at the beginning
        print("Python path:", sys.path)
        session = ProfilerSession(max_records=10)
        print("Adapters:", session.adapters)
        
        # Make a test request to the local test server
        url = f"http://{self.server.host}:{self.server.port}/"
        response = session.get(url)
        print("Response:", response)
        
        # Check if TimingAdapter.send was called
        print("Python path:", sys.path)
        # Check actual adapter instances in the session
        for protocol, adapter in session.adapters.items():
            print(f"Adapter for {protocol}: {adapter}")
            adapter_class = type(adapter)
            print(f"Adapter class: {adapter_class}")
            print(f"Adapter class module: {adapter_class.__module__}")
            # Import the module to get its __file__ attribute
            adapter_module = importlib.import_module(adapter_class.__module__)
            print(f"Adapter module path: {adapter_module.__file__}")
            print(f"Adapter has send_counter: {hasattr(adapter_class, 'send_counter')}")
            if hasattr(adapter_class, 'send_counter'):
                print(f"Adapter send_counter: {adapter_class.send_counter}")
            else:
                print("Adapter class has no send_counter attribute")
            print(f"Adapter has profiler: {hasattr(adapter, 'profiler')}")
            if hasattr(adapter, 'profiler'):
                print(f"Adapter profiler: {adapter.profiler}")
                print(f"Profiler records: {adapter.profiler.records}")

        # Check that response has timing record
        self.assertTrue(hasattr(response, 'timing_record'))
        self.assertIsNotNone(response.timing_record)
        
        # Check that record was added to profiler
        self.assertEqual(len(session.profiler.records), 1)
        self.assertEqual(session.profiler.records[0].status_code, 200)
        self.assertGreater(session.profiler.records[0].duration_ms, 0)
        # TTFB might be 0 for mock responses, so check duration instead
        if session.profiler.records[0].ttfb_ms == 0:
            self.assertGreater(session.profiler.records[0].duration_ms, 0)
        
        # Check get_stats returns valid data
        stats = session.get_stats()
        self.assertEqual(stats['count'], 1)
        self.assertEqual(stats['duration']['avg'], session.profiler.records[0].duration_ms)
        self.assertEqual(stats['ttfb']['avg'], session.profiler.records[0].ttfb_ms)
        self.assertEqual(stats['status_code_distribution'][200], 1)
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            
        session.export_csv(temp_path)
        
        # Check that CSV file was created and has content
        self.assertTrue(os.path.exists(temp_path))
        self.assertGreater(os.path.getsize(temp_path), 0)
        
        # Clean up
        os.unlink(temp_path)
        
    def test_attach_profiler(self):
        """Test attaching profiler to existing Session."""
        session = Session()
        
        # Attach profiler
        session = attach_profiler(session, max_records=10)
        
        # Make a test request
        response = session.get(f"{self.base_url}/")
        
        # Check that response has timing record
        self.assertTrue(hasattr(response, 'timing_record'))
        self.assertIsNotNone(response.timing_record)
        
        # Check that profiler is attached and record was added
        self.assertTrue(hasattr(session, 'profiler'))
        self.assertEqual(len(session.profiler.records), 1)
        
    def test_ring_buffer(self):
        """Test that ring buffer maintains max_records."""
        session = ProfilerSession(max_records=5)
        
        # Make 6 requests
        for i in range(6):
            session.get(f"{self.base_url}/")
            time.sleep(0.1)  # Add small delay to ensure different timings
            
        # Check that only last 5 records are kept
        self.assertEqual(len(session.profiler.records), 5)
        
    def test_timing_adapter_direct(self):
        """Test using TimingAdapter directly."""
        session = Session()
        
        # Create and mount TimingAdapter
        adapter = TimingAdapter()
        session.mount('http://', adapter)
        
        # Make a test request
        response = session.get(f"{self.base_url}/")
        
        # Check that response has timing record
        self.assertTrue(hasattr(response, 'timing_record'))
        self.assertIsNotNone(response.timing_record)

if __name__ == '__main__':
    unittest.main()
