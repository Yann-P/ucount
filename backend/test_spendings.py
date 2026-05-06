import pytest
from fastapi.testclient import TestClient

import store
import main

client = TestClient(main.app)

GROUP = {"name": "Trip", "currency": "EUR", "members": ["Alice", "Bob", "Charlie"]}
SPENDING = {
    "paid_by": "Alice",
    "amount": "30.00",
    "description": "Dinner",
    "beneficiaries": ["Alice", "Bob"],
}


@pytest.fixture(autouse=True)
def reset_store():
    store._mem.clear()
    yield
    store._mem.clear()


def make_group(**overrides):
    r = client.post("/groups", data={**GROUP, **overrides}, follow_redirects=False)
    return r.headers["location"].split("/group/")[1]


def add_spending(slug, **overrides):
    return client.post(
        f"/group/{slug}/spendings",
        data={**SPENDING, **overrides},
        follow_redirects=False,
    )


def test_add_spending_redirects_303():
    slug = make_group()
    assert add_spending(slug).status_code == 303


def test_add_spending_redirects_to_group_page():
    slug = make_group()
    r = add_spending(slug)
    assert r.headers["location"] == f"/group/{slug}?added=1"


def test_spending_appears_on_group_page():
    slug = make_group()
    add_spending(slug)
    page = client.get(f"/group/{slug}").text
    assert "Dinner" in page
    assert "Alice" in page
    assert "30" in page


def test_multiple_spendings_all_appear():
    slug = make_group()
    add_spending(slug, description="Dinner", amount="30")
    add_spending(slug, description="Taxi", amount="12", paid_by="Bob")
    page = client.get(f"/group/{slug}").text
    assert "Dinner" in page
    assert "Taxi" in page


def test_beneficiaries_default_to_all_members_when_none_submitted():
    slug = make_group()
    client.post(
        f"/group/{slug}/spendings",
        data={"paid_by": "Alice", "amount": "10", "description": "Coffee"},
        follow_redirects=False,
    )
    page = client.get(f"/group/{slug}").text
    assert "Alice" in page
    assert "Bob" in page
    assert "Charlie" in page


def test_add_spending_unknown_group_returns_404():
    r = client.post("/group/doesnotexist/spendings", data=SPENDING)
    assert r.status_code == 404


def test_add_spending_missing_paid_by_returns_422():
    slug = make_group()
    r = client.post(
        f"/group/{slug}/spendings", data={"amount": "10", "description": "x"}
    )
    assert r.status_code == 422


def test_add_spending_missing_amount_returns_422():
    slug = make_group()
    r = client.post(
        f"/group/{slug}/spendings", data={"paid_by": "Alice", "description": "x"}
    )
    assert r.status_code == 422


def test_add_spending_missing_description_returns_422():
    slug = make_group()
    r = client.post(
        f"/group/{slug}/spendings", data={"paid_by": "Alice", "amount": "10"}
    )
    assert r.status_code == 422


def test_spending_stores_correct_amount():
    slug = make_group()
    add_spending(slug, amount="99.99")
    page = client.get(f"/group/{slug}").text
    assert "99.99" in page


def test_spending_stores_provided_date():
    slug = make_group()
    add_spending(slug, date="2024-06-15")
    group = store.get(f"group:{slug}")
    assert group["spendings"][0]["date"] == "2024-06-15"


def test_spending_default_date_is_today():
    from datetime import date

    slug = make_group()
    add_spending(slug)
    group = store.get(f"group:{slug}")
    assert group["spendings"][0]["date"] == date.today().isoformat()


def test_spending_date_displayed_on_page():
    slug = make_group()
    add_spending(slug, date="2024-06-15")
    page = client.get(f"/group/{slug}").text
    assert "2024-06-15" in page


def test_add_spending_invalid_paid_by_returns_400():
    slug = make_group()
    assert add_spending(slug, paid_by="Stranger").status_code == 400


def test_add_spending_invalid_beneficiary_returns_400():
    slug = make_group()
    r = client.post(
        f"/group/{slug}/spendings",
        data={**SPENDING, "beneficiaries": ["Alice", "Stranger"]},
        follow_redirects=False,
    )
    assert r.status_code == 400


def test_add_spending_description_too_long_returns_422():
    slug = make_group()
    assert add_spending(slug, description="x" * 401).status_code == 422


def test_add_spending_paid_by_too_long_returns_422():
    slug = make_group()
    assert add_spending(slug, paid_by="x" * 401).status_code == 422


def test_spending_limit_returns_400():
    import spendings as sp

    original = sp.MAX_SPENDINGS
    sp.MAX_SPENDINGS = 2
    try:
        slug = make_group()
        add_spending(slug)
        add_spending(slug)
        assert add_spending(slug).status_code == 400
    finally:
        sp.MAX_SPENDINGS = original


def test_negative_amount_returns_400():
    slug = make_group()
    assert add_spending(slug, amount="-10").status_code == 400


def test_zero_amount_returns_400():
    slug = make_group()
    assert add_spending(slug, amount="0").status_code == 400
