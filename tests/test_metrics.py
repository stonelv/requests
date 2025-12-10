import pytest
import threading
import time
from unittest.mock import Mock, patch
from requests.metrics import Stats, MetricsAdapter
from requests.adapters import HTTPAdapter
from requests.models import Response, Request


class TestStats:
    def test_basic_counting(self):
        """测试基本计数功能"""
        stats = Stats()
        
        # 记录几个请求
        stats.record(200, 10.5)
        stats.record(200, 20.3)
        stats.record(404, 5.2)
        stats.record(500, 30.1)
        
        assert stats.get_total_requests() == 4
        assert stats.get_total_errors() == 2
        assert stats.get_error_rate() == 50.0
        
        status_dist = stats.get_status_distribution()
        assert status_dist == {200: 2, 404: 1, 500: 1}
        
        response_times = stats.get_response_times()
        assert len(response_times) == 4
        assert 10.5 in response_times
        assert 30.1 in response_times

    def test_status_distribution(self):
        """测试状态码分布统计"""
        stats = Stats()
        
        # 各种不同状态码
        status_codes = [200, 200, 201, 301, 302, 400, 401, 403, 404, 500, 502]
        
        for code in status_codes:
            stats.record(code, 10.0)
        
        status_dist = stats.get_status_distribution()
        
        assert status_dist[200] == 2
        assert status_dist[201] == 1
        assert status_dist[301] == 1
        assert status_dist[302] == 1
        assert status_dist[400] == 1
        assert status_dist[401] == 1
        assert status_dist[403] == 1
        assert status_dist[404] == 1
        assert status_dist[500] == 1
        assert status_dist[502] == 1
        
        assert stats.get_total_errors() == 6  # 400,401,403,404,500,502

    def test_error_counting(self):
        """测试错误计数功能"""
        stats = Stats()
        
        # 正常请求
        for _ in range(10):
            stats.record(200, 10.0)
        
        # 重定向不算错误
        for _ in range(3):
            stats.record(302, 5.0)
        
        # 客户端错误
        for _ in range(2):
            stats.record(400, 3.0)
        
        # 服务端错误
        for _ in range(1):
            stats.record(500, 20.0)
        
        assert stats.get_total_requests() == 16
        assert stats.get_total_errors() == 3
        assert stats.get_error_rate() == (3 / 16) * 100

    def test_thread_safety(self):
        """测试线程安全"""
        stats = Stats()
        thread_count = 10
        requests_per_thread = 100
        
        def worker():
            for i in range(requests_per_thread):
                status_code = 200 if i % 10 != 0 else 500
                stats.record(status_code, float(i % 100))
                time.sleep(0.001)  # 模拟一些延迟
        
        # 创建并启动线程
        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证计数正确
        total_requests = thread_count * requests_per_thread
        assert stats.get_total_requests() == total_requests
        
        # 每个线程有 10% 的错误率
        expected_errors = total_requests // 10
        assert stats.get_total_errors() == expected_errors
        
        # 验证状态码分布
        status_dist = stats.get_status_distribution()
        assert status_dist[200] == total_requests - expected_errors
        assert status_dist[500] == expected_errors
        
        # 验证所有耗时都被正确记录
        assert len(stats.get_response_times()) == total_requests

    def test_reset_functionality(self):
        """测试重置功能"""
        stats = Stats()
        
        # 先记录一些数据
        stats.record(200, 10.5)
        stats.record(404, 5.2)
        stats.record(500, 30.1)
        
        assert stats.get_total_requests() == 3
        assert stats.get_total_errors() == 2
        
        # 重置统计
        stats.reset()
        
        # 验证所有数据被重置
        assert stats.get_total_requests() == 0
        assert stats.get_total_errors() == 0
        assert stats.get_status_distribution() == {}
        assert stats.get_response_times() == []
        assert stats.get_error_rate() == 0.0
        
        # 重置后可以继续记录
        stats.record(200, 15.0)
        assert stats.get_total_requests() == 1
        assert stats.get_total_errors() == 0

    def test_summary_statistics(self):
        """测试摘要统计信息"""
        stats = Stats()
        
        # 记录一组有代表性的耗时
        response_times = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for i, rt in enumerate(response_times):
            stats.record(200 + (i % 10), rt)
        
        summary = stats.get_summary()
        
        assert summary['total_requests'] == 10
        assert summary['total_errors'] == 0
        assert summary['error_rate'] == "0.00%"
        assert len(summary['status_distribution']) == 10
        
        rt_summary = summary['response_time']
        assert rt_summary['min_ms'] == 10.0
        assert rt_summary['max_ms'] == 100.0
        assert rt_summary['avg_ms'] == 55.0
        assert rt_summary['p50_ms'] == 50.0
        assert rt_summary['p95_ms'] == 90.0
        assert rt_summary['p99_ms'] == 100.0
        assert rt_summary['count'] == 10


class TestMetricsAdapter:
    def test_adapter_records_metrics(self):
        """测试 MetricsAdapter 正确记录指标"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        # Mock 父类的 send 方法
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        
        with patch.object(HTTPAdapter, 'send', return_value=mock_response):
            request = Mock(spec=Request)
            response = adapter.send(request)
            
            assert response == mock_response
            assert stats.get_total_requests() == 1
            assert stats.get_total_errors() == 0
            status_dist = stats.get_status_distribution()
            assert status_dist == {200: 1}
            assert len(stats.get_response_times()) == 1

    def test_adapter_records_errors(self):
        """测试 MetricsAdapter 正确记录错误请求"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        # Mock 父类的 send 方法返回错误状态码
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        
        with patch.object(HTTPAdapter, 'send', return_value=mock_response):
            request = Mock(spec=Request)
            adapter.send(request)
            
            assert stats.get_total_requests() == 1
            assert stats.get_total_errors() == 1
            status_dist = stats.get_status_distribution()
            assert status_dist == {500: 1}

    def test_adapter_records_exceptions(self):
        """测试 MetricsAdapter 在请求抛出异常时也能记录指标"""
        stats = Stats()
        adapter = MetricsAdapter(stats)
        
        # Mock 父类的 send 方法抛出异常
        with patch.object(HTTPAdapter, 'send', side_effect=Exception("Connection error")):
            request = Mock(spec=Request)
            
            with pytest.raises(Exception):
                adapter.send(request)
            
            assert stats.get_total_requests() == 1
            assert stats.get_total_errors() == 1
            status_dist = stats.get_status_distribution()
            assert status_dist == {0: 1}  # 异常请求状态码记为 0
