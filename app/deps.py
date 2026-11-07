"""Shared FastAPI dependencies. Tests override provider_dep and store_dep."""
import os
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, Request

from app.config import Settings, get_settings
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.services.job_store import JobStore
from app.services.rate_limit import RateLimiter


def provider_dep(settings: Settings = Depends(get_settings)) -> AIProvider:
    return get_provider(settings)


@lru_cache
def store_dep() -> JobStore:
    return JobStore(os.getenv("JOBS_DB", "jobs.db"))


def owner_dep(x_client_id: str = Header("public", max_length=64)) -> str:
    """Anonymous id the browser creates, so each visitor only sees their own jobs."""
    return x_client_id or "public"


@lru_cache
def _limiter() -> RateLimiter:
    return RateLimiter(get_settings().ai_calls_per_hour)


def enforce_rate_limit(request: Request) -> None:
    """Call before any paid/free-quota AI request."""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    if not _limiter().allow(ip):
        raise HTTPException(429, "You've reached the hourly limit for AI checks. Please try again later.")
