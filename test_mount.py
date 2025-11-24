import requests
s = requests.Session()
print("Session object has 'mount' attribute:", hasattr(s, 'mount'))
print("Session class has 'mount' attribute:", hasattr(requests.Session, 'mount'))
