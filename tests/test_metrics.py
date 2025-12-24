import threading
import time
import pytest
from unittest.mock import Mock, patch
from requests import Session
from requests.models import Response
from requests.metrics import Stats, MetricsAdapter


@pytest.fixture
def stats():
    return Stats()


@pytest.fixture
def adapter(stats):
    return MetricsAdapter(stats)


def test_basic_counting(stats, adapter):
    # Mock a successful response
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200

    with patch.object(adapter._adapter, 'send', return_value=mock_response):
        adapter.send(Mock())

    assert stats.get_total_requests() == 1
    assert stats.get_total_errors() == 0
    assert stats.get_status_distribution() == {200: 1}


def test_status_distribution(stats, adapter):
    # Mock responses with different status codes
    mock_200 = Mock(spec=Response)
    mock_200.status_code = 200
    mock_404 = Mock(spec=Response)
    mock_404.status_code = 404
    mock_500 = Mock(spec=Response)
    mock_500.status_code = 500

    with patch.object(adapter._adapter, 'send') as mock_send:
        mock_send.side_effect = [mock_200, mock_404, mock_500, mock_200]
        adapter.send(Mock())
        adapter.send(Mock())
        adapter.send(Mock())
        adapter.send(Mock())

    status_dist = stats.get_status_distribution()
    assert status_dist[200] == 2
    assert status_dist[404] == 1
    assert status_dist[500] == 1
    assert stats.get_total_requests() == 4
    assert stats.get_total_errors() == 2  # 404 and 500 are errors


def test_error_counting(stats, adapter):
    # Mock an error response
    mock_response = Mock(spec=Response)
    mock_response.status_code = 500

    with patch.object(adapter._adapter, 'send', return_value=mock_response):
        adapter.send(Mock())

    assert stats.get_total_errors() == 1


def test_thread_safety(stats):
    adapter = MetricsAdapter(stats)
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200

    def make_request():
        with patch.object(adapter._adapter, 'send', return_value=mock_response):
            adapter.send(Mock())

    threads = []
    for _ in range(10):
        t = threading.Thread(target=make_request)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert stats.get_total_requests() == 10
    assert stats.get_status_distribution()[200] == 10


def test_reset(stats, adapter):
    # Mock a successful response
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200

    with patch.object(adapter._adapter, 'send', return_value=mock_response):
        adapter.send(Mock())
        adapter.send(Mock())

    assert stats.get_total_requests() == 2
    stats.reset()
    assert stats.get_total_requests() == 0
    assert stats.get_total_errors() == 0
    assert stats.get_status_distribution() == {}
    assert stats.get_latencies() == []
    assert stats.get_summary() == {
        "total_requests": 0,
        "total_errors": 0,
        "status_distribution": {},
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0
    }
