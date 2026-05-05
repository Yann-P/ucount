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


def test_check_existing_group():
    slug = make_group()
    r = client.get(f"/api/groups/check?slugs={slug}")
    assert r.status_code == 200
    assert r.json()["slugs"] == [slug]


def test_check_nonexistent_group():
    r = client.get("/api/groups/check?slugs=doesnotexist")
    assert r.status_code == 200
    assert r.json()["slugs"] == []


def test_check_mixed():
    slug = make_group()
    r = client.get(f"/api/groups/check?slugs={slug},fake123,other")
    assert r.json()["slugs"] == [slug]


def test_check_empty_param():
    r = client.get("/api/groups/check?slugs=")
    assert r.json()["slugs"] == []


def test_check_no_param():
    r = client.get("/api/groups/check")
    assert r.json()["slugs"] == []


def test_check_multiple_existing():
    slug1 = make_group()
    slug2 = make_group()
    r = client.get(f"/api/groups/check?slugs={slug1},{slug2}")
    existing = r.json()["slugs"]
    assert slug1 in existing
    assert slug2 in existing
