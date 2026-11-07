import hashlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.config import Settings, get_settings
from app.deps import enforce_rate_limit, provider_dep, store_dep  # noqa: F401 (provider_dep re-exported for tests)
from app.providers.base import AIProvider
from app.services.job_store import JobStore
from app.services.matcher import match_resume
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/api")


@router.get("/health")
def health(settings: Settings = Depends(get_settings)):
    return {"status": "ok", "provider": settings.ai_provider}


@router.post("/match")
async def match(
    request: Request,
    resume: UploadFile = File(...),
    job_post: str = Form(...),
    provider: AIProvider = Depends(provider_dep),
    store: JobStore = Depends(store_dep),
    settings: Settings = Depends(get_settings),
):
    text = extract_text(resume.filename or "", await resume.read())
    if not text:
        raise HTTPException(400, "Could not read any text from the resume.")
    if not job_post.strip():
        raise HTTPException(400, "Job post is empty.")

    # Same resume + same job = same answer, so reuse it instead of calling the AI again.
    key = hashlib.sha256(f"v2\n{settings.ai_provider}\n{text}\n{job_post}".encode()).hexdigest()
    if cached := store.cache_get(key):
        return {**cached, "cached": True}

    enforce_rate_limit(request)  # only real AI calls count toward the limit
    result = match_resume(provider, text, job_post)
    store.cache_set(key, result)
    return {**result, "cached": False}
