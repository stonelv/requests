"""
Tests for the timing extension functionality.
"""

import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import requests
from requests.timing import ProfilerSession, attach_profiler, RequestRecord, TimingAdapter


class TestRequestRecord(unittest.TestCase):
    """Test the RequestRecord class."""
    
    def test_record_creation(self):
        """Test basic record creation."""
        record = RequestRecord('https://example.com', 'GET')
        
        self.assertEqual(record.url, 'https://example.com')
        self.assertEqual(record.method, 'GET')
        self.assertIsNotNone(record.start_time)
        self.assertEqual(record.duration_ms, 0.0)
        self.assertEqual(record.ttfb_ms, 0.0)
        self.assertIsNone(record.status_code)
        self.assertEqual(record.content_length, 0)
        self.assertIsNone(record.error)
    
    def test_mark_first_byte(self):
        """Test marking first byte time."""
        record = RequestRecord('https://example.com', 'GET')
        
        # Simulate some time passing
        time.sleep(0.01)
        record.mark_first_byte()
        
        self.assertGreater(record.ttfb_ms, 0)
        self.assertIsNotNone(record._first_byte_time)
    
    def test_mark_complete(self):
        """Test marking request completion."""
        record = RequestRecord('https://example.com', 'GET')
        
        # Simulate some time passing
        time.sleep(0.01)
        record.mark_complete(status_code=200, content_length=1024)
        
        self.assertGreater(record.duration_ms, 0)
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.content_length, 1024)
        self.assertIsNone(record.error)
    
    def test_mark_complete_with_error(self):
        """Test marking request completion with error."""
        record = RequestRecord('https://example.com', 'GET')
        
        record.mark_complete(error='Connection timeout')
        
        self.assertGreater(record.duration_ms, 0)
        self.assertIsNone(record.status_code)
        self.assertEqual(record.error, 'Connection timeout')
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = RequestRecord('https://example.com', 'POST')
        record.mark_complete(status_code=201, content_length=2048)
        
        result = record.to_dict()
        
        self.assertEqual(result['url'], 'https://example.com')
        self.assertEqual(result['method'], 'POST')
        self.assertEqual(result['status_code'], 201)
        self.assertEqual(result['content_length'], 2048)
        self.assertGreater(result['duration_ms'], 0)
    
    def test_to_csv_row(self):
        """Test conversion to CSV row."""
        record = RequestRecord('https://example.com', 'PUT')
        record.mark_complete(status_code=200, content_length=512)
        
        row = record.to_csv_row()
        
        self.assertEqual(len(row), 8)
        self.assertEqual(row[1], 'PUT')
        self.assertEqual(row[2], 'https://example.com')
        self.assertEqual(row[3], 200)
        self.assertEqual(row[6], 512)


class TestTimingAdapter(unittest.TestCase):
    """Test the TimingAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recorded_requests = []
        self.adapter = TimingAdapter(record_callback=self.recorded_requests.append)
    
    def test_adapter_creation(self):
        """Test adapter creation."""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.record_callback, self.recorded_requests.append)
    
    @patch('requests.adapters.HTTPAdapter.send')
    def test_successful_request_timing(self, mock_send):
        """Test timing of successful requests."""
        # Mock a successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'Hello, World!'
        mock_send.return_value = mock_response
        
        # Create a mock request
        mock_request = Mock()
        mock_request.url = 'https://example.com'
        mock_request.method = 'GET'
        
        # Send the request
        response = self.adapter.send(mock_request)
        
        # Verify the response
        self.assertEqual(response, mock_response)
        self.assertTrue(hasattr(response, '_timing_record'))
        
        # Verify timing record was created
        self.assertEqual(len(self.recorded_requests), 1)
        record = self.recorded_requests[0]
        self.assertEqual(record.url, 'https://example.com')
        self.assertEqual(record.method, 'GET')
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.content_length, 13)  # len(b'Hello, World!')
        self.assertGreater(record.duration_ms, 0)
    
    @patch('requests.adapters.HTTPAdapter.send')
    def test_failed_request_timing(self, mock_send):
        """Test timing of failed requests."""
        # Mock a connection error
        mock_send.side_effect = requests.exceptions.ConnectionError('Connection failed')
        
        # Create a mock request
        mock_request = Mock()
        mock_request.url = 'https://example.com'
        mock_request.method = 'POST'
        
        # Send the request (should raise exception)
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.adapter.send(mock_request)
        
        # Verify timing record was created for failed request
        self.assertEqual(len(self.recorded_requests), 1)
        record = self.recorded_requests[0]
        self.assertEqual(record.url, 'https://example.com')
        self.assertEqual(record.method, 'POST')
        self.assertIsNone(record.status_code)
        self.assertEqual(record.error, 'Connection failed')
        self.assertGreater(record.duration_ms, 0)


class TestProfilerSession(unittest.TestCase):
    """Test the ProfilerSession class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session = ProfilerSession(max_records=10)
    
    def test_session_creation(self):
        """Test basic session creation."""
        self.assertIsInstance(self.session, ProfilerSession)
        self.assertEqual(self.session.max_records, 10)
        self.assertEqual(len(self.session), 0)
    
    def test_circular_buffer(self):
        """Test circular buffer behavior."""
        # Create multiple records to test buffer overflow
        for i in range(15):
            record = RequestRecord(f'https://example.com/{i}', 'GET')
            record.mark_complete(status_code=200, content_length=100)
            self.session._record_request(record)
        
        # Buffer should only keep the last 10 records
        self.assertEqual(len(self.session), 10)
        
        # Verify the oldest records were dropped
        records = self.session.get_records()
        urls = [r.url for r in records]
        self.assertIn('https://example.com/14', urls)
        self.assertIn('https://example.com/5', urls)
        self.assertNotIn('https://example.com/0', urls)
    
    def test_get_stats_empty(self):
        """Test get_stats with no records."""
        stats = self.session.get_stats()
        
        self.assertEqual(stats['count'], 0)
        self.assertEqual(stats['avg_duration_ms'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
        self.assertEqual(stats['status_code_distribution'], {})
    
    def test_get_stats_with_records(self):
        """Test get_stats with various records."""
        # Create records with different characteristics
        records = [
            ('https://example.com/fast', 50, 200),
            ('https://example.com/slow', 500, 200),
            ('https://example.com/medium', 200, 201),
            ('https://example.com/error', 0, 500),
            ('https://example.com/timeout', 0, None, 'Timeout'),
        ]
        
        for url, duration, status_code, *args in records:
            record = RequestRecord(url, 'GET')
            if args:
                record.mark_complete(error=args[0])
            else:
                record.duration_ms = duration
                record.status_code = status_code
                record.content_length = 100
            self.session._record_request(record)
        
        stats = self.session.get_stats()
        
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(stats['success_rate'], 60.0)  # 3 successful out of 5
        
        # Status code distribution
        status_dist = stats['status_code_distribution']
        self.assertEqual(status_dist[200], 2)
        self.assertEqual(status_dist[201], 1)
        self.assertEqual(status_dist[500], 1)
    
    def test_export_csv(self):
        """Test CSV export functionality."""
        # Create some test records
        for i in range(5):
            record = RequestRecord(f'https://example.com/{i}', 'GET')
            record.mark_complete(status_code=200, content_length=100 * (i + 1))
            self.session._record_request(record)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            success = self.session.export_csv(temp_path)
            
            self.assertTrue(success)
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            # Header + 5 data rows
            self.assertEqual(len(lines), 6)
            
            # Check header
            header = lines[0].strip()
            self.assertIn('timestamp', header)
            self.assertIn('method', header)
            self.assertIn('url', header)
            self.assertIn('status_code', header)
            self.assertIn('duration_ms', header)
            self.assertIn('ttfb_ms', header)
            self.assertIn('content_length', header)
            self.assertIn('error', header)
            
            # Check data row
            data_row = lines[1].strip()
            self.assertIn('https://example.com/0', data_row)
            self.assertIn('200', data_row)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_clear_records(self):
        """Test clearing records."""
        # Add some records
        for i in range(3):
            record = RequestRecord(f'https://example.com/{i}', 'GET')
            record.mark_complete(status_code=200)
            self.session._record_request(record)
        
        self.assertEqual(len(self.session), 3)
        
        # Clear records
        self.session.clear_records()
        
        self.assertEqual(len(self.session), 0)
        self.assertEqual(self.session.record_count, 0)


class TestAttachProfiler(unittest.TestCase):
    """Test the attach_profiler function."""
    
    def test_attach_profiler(self):
        """Test attaching profiler to existing session."""
        # Create a regular session with some configuration
        session = requests.Session()
        session.headers.update({'User-Agent': 'TestApp/1.0'})
        session.timeout = 30
        
        # Attach profiler
        profiler_session = attach_profiler(session, max_records=50)
        
        # Verify it's a ProfilerSession
        self.assertIsInstance(profiler_session, ProfilerSession)
        self.assertEqual(profiler_session.max_records, 50)
        
        # Verify configuration was copied
        self.assertEqual(profiler_session.headers.get('User-Agent'), 'TestApp/1.0')
        self.assertEqual(profiler_session.timeout, 30)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_profiler_session_integration(self):
        """Test ProfilerSession with multiple requests."""
        session = ProfilerSession(max_records=10)
        
        # Create some mock records directly
        for i in range(5):
            record = RequestRecord(f'https://example.com/api/{i}', 'GET')
            record.mark_complete(status_code=200, content_length=100 * (i + 1))
            session._record_request(record)
        
        # Verify records were stored
        self.assertEqual(len(session), 5)
        
        # Test stats
        stats = session.get_stats()
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['error_count'], 0)
        self.assertEqual(stats['success_rate'], 100.0)
        self.assertIn(200, stats['status_code_distribution'])
        
        # Test circular buffer behavior
        for i in range(10):
            record = RequestRecord(f'https://example.com/api/new/{i}', 'POST')
            record.mark_complete(status_code=201, content_length=50)
            session._record_request(record)
        
        # Should only keep the last 10 records
        self.assertEqual(len(session), 10)
        records = session.get_records()
        urls = [r.url for r in records]
        self.assertIn('https://example.com/api/new/9', urls)
        self.assertNotIn('https://example.com/api/0', urls)  # Old records should be gone
    
    def test_attach_profiler_integration(self):
        """Test attach_profiler function."""
        # Create a regular session
        session = requests.Session()
        session.headers.update({'User-Agent': 'TestApp/1.0'})
        
        # Attach profiler
        profiler_session = attach_profiler(session, max_records=20)
        
        # Verify it's a ProfilerSession
        self.assertIsInstance(profiler_session, ProfilerSession)
        self.assertEqual(profiler_session.max_records, 20)
        
        # Test that it can record requests
        record = RequestRecord('https://example.com/test', 'GET')
        record.mark_complete(status_code=200, content_length=100)
        profiler_session._record_request(record)
        
        self.assertEqual(len(profiler_session), 1)
        stats = profiler_session.get_stats()
        self.assertEqual(stats['count'], 1)


if __name__ == '__main__':
    unittest.main()