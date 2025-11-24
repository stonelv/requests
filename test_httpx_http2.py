import httpx

# Test HTTP/2 support
with httpx.Client(http2=True) as client:
    response = client.get('https://www.google.com')
    print(f'HTTP version: {response.http_version}')
    print(f'Status code: {response.status_code}')
    print(f'Headers: {dict(response.headers)}')
