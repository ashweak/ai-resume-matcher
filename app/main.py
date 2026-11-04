from fastapi import FastAPI

from app.api import jobs, routes

app = FastAPI(title="AI Resume & Job Matcher")
app.include_router(routes.router)
app.include_router(jobs.router)
