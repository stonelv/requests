import pytest
import threading
import time
from unittest.mock import Mock, patch
from requests.metrics import Stats, MetricsAdapter
from requests.models import Response, Request
from requests.adapters import HTTPAdapter


class TestStats:
    def test_basic_counting(self):
        """测试基本计数功能"""
        stats = Stats()
        
        # 记录两个请求
        stats.record(200, 0.1)
        stats.record(200, 0.2)
        
        assert stats.total_requests == 2
        assert stats.total_errors == 0
        assert stats.status_distribution == {200: 2}
        assert stats.latencies == [0.1, 0.2]

    def test_status_distribution(self):
        """测试状态码分布"""
        stats = Stats()
        
        stats.record(200, 0.1)
        stats.record(404, 0.2)
        stats.record(500, 0.3)
        stats.record(200, 0.4)
        
        assert stats.status_distribution == {200: 2, 404: 1, 500: 1}
        assert stats.total_errors == 2  # 404 和 500 都是错误

    def test_error_counting(self):
        """测试错误计数"""
        stats = Stats()
        
        stats.record(200, 0.1)  # 成功
        stats.record(400, 0.2)  # 错误
        stats.record(500, 0.3)  # 错误
        stats.record(302, 0.4)  # 重定向（非错误）
        
        assert stats.total_errors == 2
        assert stats.total_requests == 4

    def test_thread_safety(self):
        """测试线程安全"""
        stats = Stats()
        threads = []

        def worker():
            for _ in range(100):
                stats.record(200, 0.01)

        # 创建 10 个线程
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        assert stats.total_requests == 1000
        assert stats.status_distribution == {200: 1000}
        assert len(stats.latencies) == 1000

    def test_reset(self):
        """测试重置功能"""
        stats = Stats()
        
        stats.record(200, 0.1)
        stats.record(404, 0.2)
        
        assert stats.total_requests == 2
        assert stats.total_errors == 1
        
        stats.reset()
        
        assert stats.total_requests == 0
        assert stats.total_errors == 0
        assert stats.status_distribution == {}
        assert stats.latencies == []

    def test_summary(self):
        """测试统计摘要"""
        stats = Stats()
        
        stats.record(200, 0.1)
        stats.record(200, 0.2)
        stats.record(500, 0.3)
        
        summary = stats.summary()
        
        assert summary["total_requests"] == 3
        assert summary["total_errors"] == 1
        assert summary["error_rate"] == 1/3
        assert summary["status_distribution"] == {200: 2, 500: 1}
        assert summary["avg_latency"] == pytest.approx(0.2)
        assert summary["p50_latency"] == 0.2
        assert summary["p95_latency"] == 0.3
        assert summary["p99_latency"] == 0.3
        assert summary["min_latency"] == 0.1
        assert summary["max_latency"] == 0.3


class TestMetricsAdapter:
    def test_adapter_records_metrics(self):
        """测试适配器正确记录指标"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        # 创建模拟请求
        request = Request('GET', 'http://example.com')
        request = request.prepare()
        
        # 调用 send 方法
        with patch.object(HTTPAdapter, 'send') as mock_send:
            mock_send.return_value = Mock(spec=Response, status_code=200)
            adapter.send(request)
            
        # 验证指标是否被记录
        assert stats.total_requests == 1
        assert stats.status_distribution == {200: 1}
        assert stats.total_errors == 0

    def test_adapter_records_errors(self):
        """测试适配器正确记录错误"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        request = Request('GET', 'http://example.com')
        request = request.prepare()
        
        # 模拟请求失败
        with patch.object(HTTPAdapter, 'send', side_effect=Exception('Connection error')) as mock_send:
            with pytest.raises(Exception):
                adapter.send(request)
            
        # 验证错误是否被记录
        assert stats.total_requests == 1
        assert stats.status_distribution == {0: 1}  # 错误请求用 0 表示
        assert stats.total_errors == 1

    def test_adapter_records_status_codes(self):
        """测试适配器记录不同状态码"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        request = Request('GET', 'http://example.com')
        request = request.prepare()
        
        # 记录成功请求
        with patch.object(HTTPAdapter, 'send') as mock_send:
            mock_send.return_value = Mock(spec=Response, status_code=200)
            adapter.send(request)
            
        # 记录错误请求
        with patch.object(HTTPAdapter, 'send') as mock_send:
            mock_send.return_value = Mock(spec=Response, status_code=404)
            adapter.send(request)
            
        # 记录服务器错误
        with patch.object(HTTPAdapter, 'send') as mock_send:
            mock_send.return_value = Mock(spec=Response, status_code=500)
            adapter.send(request)
            
        assert stats.total_requests == 3
        assert stats.status_distribution == {200: 1, 404: 1, 500: 1}
        assert stats.total_errors == 2