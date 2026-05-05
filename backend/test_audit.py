import pytest

import audit
import store


@pytest.fixture(autouse=True)
def reset_store():
    store._mem.clear()
    yield
    store._mem.clear()


def test_log_records_entry():
    audit.log("abc", "1.2.3.4", "Chrome", "Created group")
    entries = audit.get_log("abc")
    assert len(entries) == 1
    assert entries[0]["ip"] == "1.2.3.4"
    assert entries[0]["browser"] == "Chrome"
    assert entries[0]["action"] == "Created group"
    assert "dt" in entries[0]


def test_log_multiple_entries():
    audit.log("abc", "1.2.3.4", "Chrome", "Action 1")
    audit.log("abc", "1.2.3.4", "Chrome", "Action 2")
    assert len(audit.get_log("abc")) == 2


def test_log_capped_at_100():
    for i in range(105):
        audit.log("abc", "1.2.3.4", "Chrome", f"Action {i}")
    assert len(audit.get_log("abc")) == 100


def test_log_keeps_latest_entries():
    for i in range(105):
        audit.log("abc", "1.2.3.4", "Chrome", f"Action {i}")
    actions = [e["action"] for e in audit.get_log("abc")]
    assert "Action 5" in actions
    assert "Action 104" in actions
    assert "Action 0" not in actions


def test_get_log_empty():
    assert audit.get_log("nonexistent") == []


def test_logs_are_scoped_per_slug():
    audit.log("slug1", "1.1.1.1", "Chrome", "Action A")
    audit.log("slug2", "2.2.2.2", "Firefox", "Action B")
    assert len(audit.get_log("slug1")) == 1
    assert audit.get_log("slug1")[0]["action"] == "Action A"


def test_parse_browser_chrome():
    assert (
        audit.parse_browser("Mozilla/5.0 AppleWebKit/537.36 Chrome/120.0") == "Chrome"
    )


def test_parse_browser_firefox():
    assert audit.parse_browser("Mozilla/5.0 Gecko/20100101 Firefox/121.0") == "Firefox"


def test_parse_browser_safari():
    assert (
        audit.parse_browser("Mozilla/5.0 AppleWebKit/605 Version/17 Safari/604")
        == "Safari"
    )


def test_parse_browser_edge():
    assert audit.parse_browser("Mozilla/5.0 Chrome/120 Edg/120.0") == "Edge"


def test_parse_browser_opera():
    assert audit.parse_browser("Mozilla/5.0 Chrome/120 OPR/106.0") == "Opera"


def test_parse_browser_unknown():
    assert audit.parse_browser("curl/7.68.0") == "curl/7.68.0"


def test_parse_browser_empty():
    assert audit.parse_browser("") == "Unknown"
