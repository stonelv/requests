import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from requests.timing.profiler import ProfilerSession
from requests.timing.adapter import TimingAdapter

# Create a session
session = ProfilerSession(max_records=10)

# Check adapters
print("Adapters:", session.adapters)

# Send a request
print("Sending request...")
response = session.get("http://example.com/")

# Check response
print("Response:", response)
print("Has timing_record:", hasattr(response, 'timing_record'))
print("TimingAdapter.send_counter:", TimingAdapter.send_counter)

# Check profiler records
if hasattr(session, 'profiler'):
    print("Profiler records:", session.profiler.records)