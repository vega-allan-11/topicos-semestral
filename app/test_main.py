import os
import tempfile
import pytest

os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_inventory.db")

from main import app, init_db


@pytest.fixture
def client():
    if os.path.exists(os.environ["DB_PATH"]):
        os.remove(os.environ["DB_PATH"])
    init_db()
    return app.test_client()


def test_health(client):
    assert client.get("/health").status_code == 200


def test_create_and_list(client):
    r = client.post("/products", json={"name": "Teclado", "quantity": 10, "price": 25.5})
    assert r.status_code == 201
    pid = r.get_json()["id"]

    r = client.get("/products")
    assert r.status_code == 200
    assert len(r.get_json()) == 1

    r = client.get(f"/products/{pid}")
    assert r.get_json()["name"] == "Teclado"


def test_create_requires_name(client):
    r = client.post("/products", json={"quantity": 5})
    assert r.status_code == 400


def test_update(client):
    pid = client.post("/products", json={"name": "Mouse", "quantity": 3}).get_json()["id"]
    r = client.put(f"/products/{pid}", json={"quantity": 20})
    assert r.status_code == 200
    assert r.get_json()["quantity"] == 20


def test_delete(client):
    pid = client.post("/products", json={"name": "Monitor"}).get_json()["id"]
    assert client.delete(f"/products/{pid}").status_code == 200
    assert client.get(f"/products/{pid}").status_code == 404
