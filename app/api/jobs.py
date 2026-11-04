import os
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.routes import provider_dep
from app.providers.base import AIProvider
from app.services.job_store import JobStore
from app.services.matcher import cosine_similarity
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@lru_cache
def store_dep() -> JobStore:
    return JobStore(os.getenv("JOBS_DB", "jobs.db"))


class JobIn(BaseModel):
    title: str
    company: str = ""
    description: str


@router.post("", status_code=201)
def add_job(job: JobIn, provider: AIProvider = Depends(provider_dep), store: JobStore = Depends(store_dep)):
    if not job.description.strip():
        raise HTTPException(400, "Description is empty.")
    vector = provider.embed([f"{job.title}\n{job.description}"])[0]
    job_id = store.add(job.title, job.company, job.description, vector)
    return {"id": job_id, "title": job.title, "company": job.company}


@router.get("")
def list_jobs(store: JobStore = Depends(store_dep)):
    return store.list_all()


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, store: JobStore = Depends(store_dep)):
    if not store.delete(job_id):
        raise HTTPException(404, "Job not found.")


@router.post("/rank")
async def rank_jobs(
    resume: UploadFile = File(...),
    top_k: int = Form(5),
    provider: AIProvider = Depends(provider_dep),
    store: JobStore = Depends(store_dep),
):
    """Vector search: find the saved jobs that best fit this resume."""
    jobs = store.all_with_embeddings()
    if not jobs:
        raise HTTPException(400, "No jobs saved yet. Add some with POST /api/jobs.")

    text = extract_text(resume.filename or "", await resume.read())
    if not text:
        raise HTTPException(400, "Could not read any text from the resume.")

    resume_vec = provider.embed([text])[0]
    ranked = sorted(
        (
            {
                "id": j["id"],
                "title": j["title"],
                "company": j["company"],
                "score": round(max(0.0, cosine_similarity(resume_vec, j["embedding"])) * 100, 1),
            }
            for j in jobs
        ),
        key=lambda r: r["score"],
        reverse=True,
    )
    return ranked[: max(1, top_k)]
