import requests
from requests.metrics import Stats, MetricsAdapter


def main():
    # Create stats instance
    stats = Stats()

    # Create a Session and mount the MetricsAdapter
    session = requests.Session()
    adapter = MetricsAdapter(stats)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    # Make some requests
    print("Making requests...")
    try:
        # Successful request
        response = session.get('https://httpbin.org/get')
        print(f"GET https://httpbin.org/get -> {response.status_code}")

        # Another successful request
        response = session.get('https://httpbin.org/headers')
        print(f"GET https://httpbin.org/headers -> {response.status_code}")

        # 404 request
        response = session.get('https://httpbin.org/status/404')
        print(f"GET https://httpbin.org/status/404 -> {response.status_code}")

        # 500 request
        response = session.get('https://httpbin.org/status/500')
        print(f"GET https://httpbin.org/status/500 -> {response.status_code}")

    except Exception as e:
        print(f"Error making requests: {e}")

    # Print the summary
    print("\nMetrics Summary:")
    summary = stats.get_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
