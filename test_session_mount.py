import sys
sys.path.insert(0, 'src')
import requests
from requests.sessions import Session

print("Session class has 'mount' attribute:", hasattr(Session, 'mount'))
print("Session class methods:", [m for m in dir(Session) if not m.startswith('_')])

# Try to create a session instance
try:
    s = Session()
    print("Session instance created successfully")
    print("Session instance has 'mount' attribute:", hasattr(s, 'mount'))
except Exception as e:
    print(f"Error creating session: {e}")
