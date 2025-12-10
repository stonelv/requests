#!/usr/bin/env python
"""
示例脚本：展示如何使用 requests-metrics 模块
"""
import time
import requests
from requests.metrics import Stats, MetricsAdapter
from concurrent.futures import ThreadPoolExecutor


def make_request(session, url):
    """发起 HTTP 请求"""
    try:
        response = session.get(url, timeout=5)
        print(f"Request to {url} returned {response.status_code}")
        return response
    except Exception as e:
        print(f"Request to {url} failed: {e}")
        return None


def main():
    # 创建统计实例
    stats = Stats()
    
    # 创建 Session 并挂载 MetricsAdapter
    session = requests.Session()
    
    # 替换默认的 HTTPAdapter 为 MetricsAdapter
    adapter = MetricsAdapter(stats)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    print("=== Starting Requests Metrics Example ===\n")
    
    # 1. 发起一些简单的请求
    print("Phase 1: Making simple requests...")
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
        "https://httpbin.org/delay/0.1",
        "https://httpbin.org/delay/0.2",
    ]
    
    for url in urls:
        make_request(session, url)
        time.sleep(0.1)
    
    print("\nPhase 1 complete! Current stats:")
    stats.print_summary()
    print("\n" + "-"*60 + "\n")
    
    # 2. 发起并发请求
    print("Phase 2: Making concurrent requests...")
    concurrent_urls = [
        "https://httpbin.org/get"
        for _ in range(20)
    ]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda url: make_request(session, url), concurrent_urls)
    
    print("\nPhase 2 complete! Final stats:")
    stats.print_summary()
    
    # 3. 重置统计并再次发起请求
    print("\n" + "-"*60 + "\n")
    print("Phase 3: Resetting stats and making a few more requests...")
    stats.reset()
    
    for _ in range(3):
        make_request(session, "https://httpbin.org/get")
    
    print("\nPhase 3 complete! Stats after reset:")
    stats.print_summary()
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
