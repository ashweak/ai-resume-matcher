from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.deps import enforce_rate_limit, owner_dep, provider_dep, store_dep  # noqa: F401 (store_dep re-exported for tests)
from app.providers.base import AIProvider
from app.services.job_store import JobStore
from app.services.matcher import cosine_similarity
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", status_code=201)
def add_job(
    request: Request,
    title: str = Form(..., max_length=200),
    description: str = Form(..., max_length=20000),
    company: str = Form("", max_length=200),
    owner: str = Depends(owner_dep),
    provider: AIProvider = Depends(provider_dep),
    store: JobStore = Depends(store_dep),
):
    """Form fields, so a multi-line job post can be pasted as-is."""
    if not title.strip() or not description.strip():
        raise HTTPException(400, "Please fill in the job title and the job post.")
    enforce_rate_limit(request)
    vector = provider.embed([f"{title}\n{description}"])[0]
    job_id = store.add(owner, title.strip(), company.strip(), description, vector)
    return {"id": job_id, "title": title, "company": company}


@router.get("")
def list_jobs(owner: str = Depends(owner_dep), store: JobStore = Depends(store_dep)):
    return store.list_all(owner)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, owner: str = Depends(owner_dep), store: JobStore = Depends(store_dep)):
    if not store.delete(owner, job_id):
        raise HTTPException(404, "Job not found.")


@router.post("/rank")
async def rank_jobs(
    request: Request,
    resume: UploadFile = File(...),
    top_k: int = Form(5),
    owner: str = Depends(owner_dep),
    provider: AIProvider = Depends(provider_dep),
    store: JobStore = Depends(store_dep),
):
    """Vector search: find the saved jobs that best fit this resume."""
    jobs = store.all_with_embeddings(owner)
    if not jobs:
        raise HTTPException(400, "No jobs saved yet. Add at least one job first.")

    text = extract_text(resume.filename or "", await resume.read())
    if not text:
        raise HTTPException(400, "Could not read any text from the resume.")

    enforce_rate_limit(request)
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
