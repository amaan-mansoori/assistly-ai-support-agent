from src.platform.rate_limit import FixedWindowLimiter


def test_fixed_window_limit_and_key_isolation():
    clock = [120.0]
    limiter = FixedWindowLimiter(limit=2, clock=lambda: clock[0])

    assert limiter.allow("customer:1")
    assert limiter.allow("customer:1")
    assert not limiter.allow("customer:1")
    assert limiter.allow("customer:2")
    clock[0] = 180.0
    assert limiter.allow("customer:1")


def test_configured_redis_limit_falls_back_locally_on_unavailability(monkeypatch):
    import redis

    class BrokenRedis:
        def eval(self, *_args):
            raise redis.ConnectionError("do not log connection details")

    limiter = FixedWindowLimiter(limit=1, redis_url="redis://localhost:6379/0")
    limiter._redis = BrokenRedis()

    assert limiter.allow("user:1")
    assert not limiter.allow("user:1")
