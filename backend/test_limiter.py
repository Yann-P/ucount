from unittest.mock import MagicMock, patch

import limiter


def setup_function():
    limiter._mem.clear()
    limiter._mem_window.clear()


def test_not_rate_limited_below_limit():
    with patch("limiter.store._r", return_value=None):
        for _ in range(limiter.LIMIT):
            assert not limiter.is_rate_limited("1.2.3.4")


def test_rate_limited_above_limit():
    with patch("limiter.store._r", return_value=None):
        for _ in range(limiter.LIMIT):
            limiter.is_rate_limited("1.2.3.4")
        assert limiter.is_rate_limited("1.2.3.4")


def test_different_ips_are_independent():
    with patch("limiter.store._r", return_value=None):
        for _ in range(limiter.LIMIT):
            limiter.is_rate_limited("1.2.3.4")
        assert limiter.is_rate_limited("1.2.3.4")
        assert not limiter.is_rate_limited("5.6.7.8")


def test_rate_limited_with_redis():
    mock_redis = MagicMock()
    mock_redis.incr.return_value = limiter.LIMIT + 1
    with patch("limiter.store._r", return_value=mock_redis):
        assert limiter.is_rate_limited("1.2.3.4")


def test_not_rate_limited_with_redis():
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 1
    with patch("limiter.store._r", return_value=mock_redis):
        assert not limiter.is_rate_limited("1.2.3.4")


def test_redis_sets_expiry_on_first_request():
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 1
    with patch("limiter.store._r", return_value=mock_redis):
        limiter.is_rate_limited("1.2.3.4")
    mock_redis.expire.assert_called_once()


def test_redis_no_expiry_on_subsequent_requests():
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 5
    with patch("limiter.store._r", return_value=mock_redis):
        limiter.is_rate_limited("1.2.3.4")
    mock_redis.expire.assert_not_called()
