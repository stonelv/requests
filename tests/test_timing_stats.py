import unittest
import time
from requests import Session
from requests.timing import ProfilerSession
from tests.testserver.server import Server

class TestTimingStatistics(unittest.TestCase):
    """Test statistics calculation for timing records."""
    
    def setUp(self):
        """Set up test server before each test."""
        self.server = Server.basic_response_server(requests_to_handle=10)
        self.server.start()
        self.server.ready_event.wait()
        self.base_url = f"http://localhost:{self.server.port}"
    
    def tearDown(self):
        """Stop test server after each test."""
        self.server.stop_event.set()
        self.server.join()
    
    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        session = ProfilerSession(max_records=10)
        
        # Make multiple requests
        for i in range(5):
            response = session.get(f"{self.base_url}/")
            time.sleep(0.1)  # Add small delay to ensure different timings
            
        # Check that 5 records are present
        self.assertEqual(len(session.profiler.records), 5)
        
        # Get statistics
        stats = session.get_stats()
        
        # Verify count
        self.assertEqual(stats['count'], 5)
        
        # Verify duration stats
        durations = [r.duration_ms for r in session.profiler.records]
        self.assertAlmostEqual(stats['duration']['avg'], sum(durations)/len(durations), places=2)
        self.assertEqual(stats['duration']['min'], min(durations))
        self.assertEqual(stats['duration']['max'], max(durations))
        
        # Verify TTFB stats
        ttfb_values = [r.ttfb_ms for r in session.profiler.records]
        self.assertAlmostEqual(stats['ttfb']['avg'], sum(ttfb_values)/len(ttfb_values), places=2)
        self.assertEqual(stats['ttfb']['min'], min(ttfb_values))
        self.assertEqual(stats['ttfb']['max'], max(ttfb_values))
        
        # Verify status code distribution
        self.assertEqual(stats['status_code_distribution'][200], 5)
        
    def test_statistics_with_no_records(self):
        """Test statistics when no records are present."""
        session = ProfilerSession(max_records=10)
        
        # Get statistics with no requests made
        stats = session.get_stats()
        
        # Verify all stats are zero
        self.assertEqual(stats['count'], 0)
        self.assertEqual(stats['duration']['avg'], 0)
        self.assertEqual(stats['duration']['min'], 0)
        self.assertEqual(stats['duration']['max'], 0)
        self.assertEqual(stats['ttfb']['avg'], 0)
        self.assertEqual(stats['ttfb']['min'], 0)
        self.assertEqual(stats['ttfb']['max'], 0)
        self.assertEqual(stats['status_code_distribution'], {})
        
    def test_original_behavior_preserved(self):
        """Test that original Requests behavior is preserved when extension is not used."""
        # Create a regular Session (not ProfilerSession)
        session = Session()
        
        # Make a request
        response = session.get(f"{self.base_url}/")
        
        # Verify response has status code 200
        self.assertEqual(response.status_code, 200)
        
        # Verify response does NOT have a timing_record attribute
        self.assertFalse(hasattr(response, 'timing_record'))
        
        # Verify session does NOT have a profiler attribute
        self.assertFalse(hasattr(session, 'profiler'))

if __name__ == '__main__':
    unittest.main()
