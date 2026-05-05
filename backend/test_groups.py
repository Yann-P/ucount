import pytest
from fastapi.testclient import TestClient

import store
import main

client = TestClient(main.app)

GROUP = {"name": "Trip", "currency": "EUR", "members": ["Alice", "Bob", "Charlie"]}


@pytest.fixture(autouse=True)
def reset_store():
    store._mem.clear()
    yield
    store._mem.clear()


def make_group(**overrides):
    return client.post("/groups", data={**GROUP, **overrides}, follow_redirects=False)


def test_create_group_redirects_303():
    assert make_group().status_code == 303


def test_create_group_redirects_to_group_url():
    assert make_group().headers["location"].startswith("/group/")


def test_create_group_stores_name():
    r = client.post("/groups", data=GROUP, follow_redirects=True)
    assert r.status_code == 200
    assert "Trip" in r.text


def test_create_group_missing_name_returns_422():
    assert (
        client.post("/groups", data={"currency": "EUR", "members": "Alice"}).status_code
        == 422
    )


def test_create_group_missing_members_returns_422():
    assert (
        client.post("/groups", data={"name": "Trip", "currency": "EUR"}).status_code
        == 422
    )


def test_create_group_each_gets_unique_slug():
    slugs = {make_group(name=f"G{i}").headers["location"] for i in range(20)}
    assert len(slugs) == 20


def test_create_group_default_currency_is_eur():
    r = make_group()
    slug = r.headers["location"].split("/group/")[1]
    group = store.get(f"group:{slug}")
    assert group is not None
    assert group["currency"] == "EUR"


def test_group_page_returns_200():
    assert client.get(make_group().headers["location"]).status_code == 200


def test_group_page_shows_group_name():
    r = make_group()
    assert "Trip" in client.get(r.headers["location"]).text


def test_group_page_shows_members():
    r = make_group()
    page = client.get(r.headers["location"]).text
    assert "Alice" in page
    assert "Bob" in page
    assert "Charlie" in page


def test_group_currency_is_stored():
    r = make_group(currency="USD")
    slug = r.headers["location"].split("/group/")[1]
    group = store.get(f"group:{slug}")
    assert group is not None
    assert group["currency"] == "USD"


def test_group_page_shows_slug_in_body():
    r = make_group()
    slug = r.headers["location"].split("/group/")[1]
    assert slug in client.get(f"/group/{slug}").text


def test_group_not_found_redirects_to_index():
    r = client.get("/group/doesnotexist", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_group_data_persists_across_requests():
    url = make_group().headers["location"]
    for _ in range(3):
        assert "Trip" in client.get(url).text


def test_create_group_name_too_long_returns_422():
    assert make_group(name="x" * 401).status_code == 422


def test_create_group_excess_members_are_truncated():
    import groups as g

    original = g.MAX_MEMBERS
    g.MAX_MEMBERS = 3
    try:
        r = client.post(
            "/groups",
            data={"name": "T", "currency": "EUR", "members": ["A", "B", "C", "D", "E"]},
            follow_redirects=False,
        )
        slug = r.headers["location"].split("/group/")[1]
        assert len(store.get(f"group:{slug}")["members"]) == 3
    finally:
        g.MAX_MEMBERS = original
