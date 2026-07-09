import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "WHMCS AI Assistant Pro Backend API"
    }

def test_chatbot_endpoint(monkeypatch):
    # Mock LLM run_agent to avoid hitting Gemini/OpenAI during tests
    def mock_run_agent(db, session_id, message):
        return "This is a mock reply for: " + message, ["Modexa WHMCS Theme"]
    
    import backend.app.api.endpoints as endpoints
    monkeypatch.setattr(endpoints, "run_agent", mock_run_agent)
    
    payload = {
        "session_id": "test_session_123",
        "message": "Hello, I need modexa theme"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "mock reply" in data["response"]
    assert data["session_id"] == "test_session_123"
    assert data["matched_products"] == ["Modexa WHMCS Theme"]

def test_lead_capture_endpoint():
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.org",
        "business_type": "Hosting Reseller",
        "requirement": "Requires a custom modules configuration"
    }
    response = client.post("/api/v1/lead", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.org"
    assert data["status"] == "new"

def test_products_endpoint():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
