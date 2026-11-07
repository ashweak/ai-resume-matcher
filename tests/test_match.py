from fastapi.testclient import TestClient

from app.api.routes import provider_dep
from app.main import app
from app.providers.base import AIProvider


class FakeProvider(AIProvider):
    """Lets tests run with no API key and no cost."""

    def generate_json(self, prompt: str) -> dict:
        return {"matched_skills": ["Python"], "missing_skills": ["Docker"], "suggestions": ["Add metrics"], "summary": "Good fit."}

    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


client = TestClient(app)


def setup_function():
    app.dependency_overrides.clear()
    app.dependency_overrides[provider_dep] = lambda: FakeProvider()


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_match():
    r = client.post(
        "/api/match",
        files={"resume": ("resume.txt", b"Python developer with FastAPI experience", "text/plain")},
        data={"job_post": "Looking for a Python developer who knows Docker"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["match_score"] == 100.0
    assert "Docker" in body["missing_skills"]


def test_home_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "AI Resume" in r.text
