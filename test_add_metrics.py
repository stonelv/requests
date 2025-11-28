import requests
from requests.metrics import add_metrics

# Create a session
session = requests.Session()

# Add metrics to the session
stats = add_metrics(session)

# Print the stats object to verify it was created
print(f"Stats object created: {stats}")
print(f"Total requests: {stats._total_requests}")
print(f"Total errors: {stats._total_errors}")