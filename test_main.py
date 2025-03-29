from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_valid_request():
    response = client.post("/weather", json={
        "lon": 105.85,
        "lat": 21.02,
        "start_year": 2020,
        "end_year": 2023
    })
    assert response.status_code == 200
    assert "value" in response.json()

def test_invalid_year():
    response = client.post("/weather", json={
        "lon": 105.85,
        "lat": 21.02,
        "start_year": 2024,
        "end_year": 2023
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "Năm kết thúc phải lớn hơn hoặc bằng năm bắt đầu."

def test_start_year():
    response = client.post("/weather", json={
        "lon": 105.85,
        "lat": 21.02,
        "start_year": 2050,
        "end_year": 2050
    })
    assert response.status_code == 422
    assert "Năm bắt đầu không thể lớn hơn năm hiện tại" in response.json()["detail"]

def test_future_end_year():
    response = client.post("/weather", json={
        "lon": 105.85,
        "lat": 21.02,
        "start_year": 2020,
        "end_year": 3000
    })
    assert response.status_code == 422
    assert "Năm kết thúc không thể lớn hơn năm hiện tại" in response.json()["detail"]

def test_missing_field():
    response = client.post("/weather", json={
        "lon": 105.85,
        "start_year": 2020
    })
    assert response.status_code == 422
