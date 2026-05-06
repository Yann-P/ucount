import pytest
from fastapi.testclient import TestClient

import store
import main

client = TestClient(main.app, follow_redirects=False)

GROUP = {"name": "Trip", "currency": "EUR", "members": ["Alice", "Bob"]}


@pytest.fixture(autouse=True)
def reset_store():
    store._mem.clear()
    yield
    store._mem.clear()


def make_group() -> str:
    r = client.post("/groups", data=GROUP)
    return r.headers["location"].split("/")[-1]


def test_partial_existing_group():
    slug = make_group()
    r = client.get(f"/api/groups/partial?slugs={slug}")
    assert r.status_code == 200
    assert slug in r.text
    assert "Trip" in r.text


def test_partial_nonexistent_group():
    r = client.get("/api/groups/partial?slugs=doesnotexist")
    assert r.status_code == 200
    assert r.text.strip() == ""


def test_partial_mixed():
    slug = make_group()
    r = client.get(f"/api/groups/partial?slugs={slug},fake123,other")
    assert slug in r.text
    assert "fake123" not in r.text


def test_partial_empty_param():
    r = client.get("/api/groups/partial?slugs=")
    assert r.status_code == 200
    assert r.text.strip() == ""


def test_partial_no_param():
    r = client.get("/api/groups/partial")
    assert r.status_code == 200
    assert r.text.strip() == ""


def test_partial_multiple_existing():
    slug1 = make_group()
    slug2 = make_group()
    r = client.get(f"/api/groups/partial?slugs={slug1},{slug2}")
    assert slug1 in r.text
    assert slug2 in r.text
