from fastapi.testclient import TestClient

from app.api.jobs import store_dep
from app.api.routes import provider_dep
from app.main import app
from app.providers.base import AIProvider
from app.services.job_store import JobStore


class KeywordProvider(AIProvider):
    """Fake embeddings: [python?, design?] so ranking is predictable. No API key, no cost."""

    def generate_json(self, prompt: str) -> dict:
        return {}

    def embed(self, texts):
        return [[float("python" in t.lower()), float("design" in t.lower())] for t in texts]


def make_client():
    store = JobStore(":memory:")
    app.dependency_overrides.clear()
    app.dependency_overrides[provider_dep] = lambda: KeywordProvider()
    app.dependency_overrides[store_dep] = lambda: store
    return TestClient(app)


def test_add_list_delete():
    client = make_client()
    r = client.post("/api/jobs", data={"title": "Backend Dev", "company": "Acme", "description": "Python APIs"})
    assert r.status_code == 201
    job_id = r.json()["id"]
    assert len(client.get("/api/jobs").json()) == 1
    assert client.delete(f"/api/jobs/{job_id}").status_code == 204
    assert client.get("/api/jobs").json() == []


def test_rank_puts_best_fit_first():
    client = make_client()
    client.post("/api/jobs", data={"title": "UI Designer", "description": "Figma design"})
    client.post("/api/jobs", data={"title": "Python Dev", "description": "FastAPI python"})
    r = client.post(
        "/api/jobs/rank",
        files={"resume": ("resume.txt", b"Python developer", "text/plain")},
        data={"top_k": "2"},
    )
    assert r.status_code == 200
    assert r.json()[0]["title"] == "Python Dev"


def test_rank_with_no_jobs():
    client = make_client()
    r = client.post("/api/jobs/rank", files={"resume": ("r.txt", b"Python", "text/plain")})
    assert r.status_code == 400


def test_each_visitor_sees_only_their_jobs():
    client = make_client()
    client.post("/api/jobs", data={"title": "Mine", "description": "python"}, headers={"X-Client-Id": "alice"})
    client.post("/api/jobs", data={"title": "Theirs", "description": "design"}, headers={"X-Client-Id": "bob"})
    alice = client.get("/api/jobs", headers={"X-Client-Id": "alice"}).json()
    assert [j["title"] for j in alice] == ["Mine"]
    bob_job = client.get("/api/jobs", headers={"X-Client-Id": "bob"}).json()[0]["id"]
    assert client.delete(f"/api/jobs/{bob_job}", headers={"X-Client-Id": "alice"}).status_code == 404
