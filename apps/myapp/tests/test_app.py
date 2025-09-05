import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Welcome" in res.data

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"

def test_hello_default(client):
    res = client.get("/hello")
    assert res.status_code == 200
    assert res.get_json()["message"] == "Hello, world!"

def test_hello_with_name(client):
    res = client.get("/hello?name=niuniu")
    assert res.status_code == 200
    assert res.get_json()["message"] == "Hello, niuniu!"

