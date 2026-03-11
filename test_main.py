import sqlite3
import pytest
from fastapi.testclient import TestClient
import main as app_module
from main import app, DB_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM users")
        conn.commit()
    yield
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM users")
        conn.commit()


def test_create_user():
    resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com", "age": 30})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["age"] == 30
    assert "id" in data


def test_create_user_duplicate_email():
    client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    resp = client.post("/users", json={"name": "Bob", "email": "alice@example.com"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_list_users():
    client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/users", json={"name": "Bob", "email": "bob@example.com"})
    resp = client.get("/users")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_user():
    create_resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    user_id = create_resp.json()["id"]
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


def test_get_user_not_found():
    resp = client.get("/users/nonexistent-id")
    assert resp.status_code == 404


def test_update_user():
    create_resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    user_id = create_resp.json()["id"]
    resp = client.put(f"/users/{user_id}", json={"name": "Alice Updated", "email": "alice2@example.com"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice Updated"
    assert resp.json()["email"] == "alice2@example.com"


def test_delete_user():
    create_resp = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    user_id = create_resp.json()["id"]
    resp = client.delete(f"/users/{user_id}")
    assert resp.status_code == 204
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 404


def test_data_persists_to_db():
    client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM users").fetchall()
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
