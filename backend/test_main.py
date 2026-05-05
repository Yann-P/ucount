from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_index_returns_200():
    assert client.get("/").status_code == 200


def test_index_has_form_posting_to_groups():
    r = client.get("/")
    assert 'action="/groups"' in r.text
    assert 'method="post"' in r.text


def test_index_has_name_input():
    r = client.get("/")
    assert 'name="name"' in r.text
