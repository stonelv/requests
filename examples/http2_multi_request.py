import requests
import time
import threading
from requests.adapters_http2 import HTTP2Adapter


def make_request(session, url, results, index):
    """Make a request and store the result."""
    try:
        start_time = time.time()
        response = session.get(url)
        duration = time.time() - start_time
        results[index] = (response.status_code, duration)
    except Exception as e:
        results[index] = (str(e), 0)


def main():
    """Main function to run the example."""
    # URLs to test (use HTTP/2 enabled servers)
    urls = [
        'https://http2.akamai.com/demo',
        'https://example.com',
        'https://www.google.com',
        'https://www.github.com',
        'https://www.cloudflare.com',
        'https://http2.akamai.com/demo',
        'https://example.com',
        'https://www.google.com',
        'https://www.github.com',
        'https://www.cloudflare.com',
    ]
    
    # Create a session with HTTP2Adapter
    with requests.Session() as session:
        adapter = HTTP2Adapter(
            max_concurrent_streams=10,
            metrics_callback=lambda **kwargs: print(f"Request: {kwargs['method']} {kwargs['url']} - Status: {kwargs['status']} - Duration: {kwargs['duration']:.3f}s"),
        )
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        
        # Make requests sequentially
        print("Making requests sequentially...")
        start_time = time.time()
        for i, url in enumerate(urls):
            try:
                response = session.get(url)
                print(f"{i+1}. {url} - Status: {response.status_code}")
            except Exception as e:
                print(f"{i+1}. {url} - Error: {e}")
        sequential_time = time.time() - start_time
        print(f"Sequential time: {sequential_time:.3f}s")
        
        print()
        
        # Make requests concurrently
        print("Making requests concurrently...")
        start_time = time.time()
        results = [None] * len(urls)
        threads = []
        
        for i, url in enumerate(urls):
            t = threading.Thread(target=make_request, args=(session, url, results, i))
            threads.append(t)
            t.start()
        
        # Wait for all threads to finish
        for t in threads:
            t.join()
        
        concurrent_time = time.time() - start_time
        print(f"Concurrent time: {concurrent_time:.3f}s")
        print(f"Speedup: {sequential_time / concurrent_time:.2f}x")
        
        print()
        print("Results:")
        for i, (status, duration) in enumerate(results):
            print(f"{i+1}. {urls[i]} - Status: {status} - Duration: {duration:.3f}s")


if __name__ == '__main__':
    main()
