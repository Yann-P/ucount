import pytest
import store


@pytest.fixture(autouse=True)
def reset():
    store._mem.clear()
    yield
    store._mem.clear()


def test_get_missing_returns_none():
    assert store.get("x") is None


def test_set_and_get_roundtrip():
    store.set("k", {"a": 1, "b": "hello"})
    assert store.get("k") == {"a": 1, "b": "hello"}


def test_overwrite():
    store.set("k", {"v": 1})
    store.set("k", {"v": 2})
    assert store.get("k") == {"v": 2}


def test_keys_are_independent():
    store.set("a", {"x": 1})
    store.set("b", {"x": 2})
    assert store.get("a") == {"x": 1}
    assert store.get("b") == {"x": 2}
