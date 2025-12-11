import requests
from requests.metrics import Stats, MetricsAdapter
import time
import random


def main():
    """
    示例：使用 MetricsAdapter 记录请求统计信息
    """
    # 创建统计实例
    stats = Stats()
    
    # 创建 Session 并挂载 MetricsAdapter
    session = requests.Session()
    
    # 移除默认适配器，添加 MetricsAdapter
    for protocol in ['http://', 'https://']:
        session.mount(protocol, MetricsAdapter(stats))
    
    print("=== 开始发送测试请求 ===")
    
    # 模拟一些请求
    for i in range(10):
        try:
            # 随机生成状态码，模拟不同的请求结果
            status_code = random.choice([200, 200, 200, 404, 500])
            
            # 发送请求（使用模拟响应）
            response = requests.Response()
            response.status_code = status_code
            response._content = b'OK'
            
            # 记录模拟的耗时
            latency = random.uniform(0.01, 0.1)
            stats.record(status_code, latency)
            
            print(f"请求 {i+1}: 状态码 {status_code}, 耗时 {latency:.3f}s")
            
            # 模拟请求间隔
            time.sleep(0.1)
            
        except Exception as e:
            print(f"请求 {i+1}: 失败 - {e}")
    
    print("\n=== 统计摘要 ===")
    summary = stats.summary()
    
    print(f"总请求数: {summary['total_requests']}")
    print(f"总错误数: {summary['total_errors']}")
    print(f"错误率: {summary['error_rate']:.2%}")
    print(f"平均耗时: {summary['avg_latency']:.3f}s")
    print(f"P50 耗时: {summary['p50_latency']:.3f}s")
    print(f"P95 耗时: {summary['p95_latency']:.3f}s")
    print(f"P99 耗时: {summary['p99_latency']:.3f}s")
    print(f"最小耗时: {summary['min_latency']:.3f}s")
    print(f"最大耗时: {summary['max_latency']:.3f}s")
    print(f"运行时间: {summary['uptime']:.2f}s")
    
    print("\n=== 状态码分布 ===")
    for status, count in summary['status_distribution'].items():
        if status == 0:
            print(f"  错误请求: {count}")
        else:
            print(f"  {status}: {count}")
    
    # 重置统计
    print("\n=== 重置统计 ===")
    stats.reset()
    print(f"重置后总请求数: {stats.total_requests}")
    print(f"重置后总错误数: {stats.total_errors}")


if __name__ == "__main__":
    main()