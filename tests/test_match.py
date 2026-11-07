from fastapi.testclient import TestClient

from app.api.routes import provider_dep, store_dep
from app.main import app
from app.providers.base import AIProvider
from app.services.job_store import JobStore
from app.services.matcher import RUBRIC
from app.services.rate_limit import RateLimiter


class FakeProvider(AIProvider):
    """Lets tests run with no API key and no cost."""

    calls = 0

    def generate_json(self, prompt: str) -> dict:
        FakeProvider.calls += 1
        return {
            "scores": {k: {"score": 8, "reason": "ok"} for k in RUBRIC},
            "matched_skills": ["Python"], "missing_skills": ["Docker"],
            "suggestions": [{"priority": "high", "text": "Add metrics"}], "summary": "Good fit.",
        }

    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


client = TestClient(app)


def setup_function():
    app.dependency_overrides.clear()
    store = JobStore(":memory:")
    app.dependency_overrides[provider_dep] = lambda: FakeProvider()
    app.dependency_overrides[store_dep] = lambda: store


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
    assert body["recruiter_score"] == 80.0
    assert len(body["dimensions"]) == len(RUBRIC)


def test_home_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "ResuMatch AI" in r.text


def test_match_is_cached():
    FakeProvider.calls = 0
    args = dict(
        files={"resume": ("r.txt", b"Python developer", "text/plain")},
        data={"job_post": "Python job"},
    )
    first, second = client.post("/api/match", **args).json(), client.post("/api/match", **args).json()
    assert (first["cached"], second["cached"]) == (False, True)
    assert FakeProvider.calls == 1


def test_unsupported_file_type():
    r = client.post("/api/match", files={"resume": ("cv.jpg", b"xx", "image/jpeg")}, data={"job_post": "x"})
    assert r.status_code == 400


def test_rate_limiter():
    limiter = RateLimiter(max_calls=2)
    assert [limiter.allow("ip") for _ in range(3)] == [True, True, False]
    assert RateLimiter(max_calls=0).allow("ip")
