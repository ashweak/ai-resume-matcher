from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.services.matcher import match_resume
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/api")


def provider_dep(settings: Settings = Depends(get_settings)) -> AIProvider:
    return get_provider(settings)


@router.get("/health")
def health(settings: Settings = Depends(get_settings)):
    return {"status": "ok", "provider": settings.ai_provider}


@router.post("/match")
async def match(
    resume: UploadFile = File(...),
    job_post: str = Form(...),
    provider: AIProvider = Depends(provider_dep),
):
    text = extract_text(resume.filename or "", await resume.read())
    if not text:
        raise HTTPException(400, "Could not read any text from the resume.")
    if not job_post.strip():
        raise HTTPException(400, "Job post is empty.")
    return match_resume(provider, text, job_post)
