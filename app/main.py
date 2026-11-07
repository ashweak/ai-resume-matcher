from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api import jobs, routes

app = FastAPI(title="AI Resume & Job Matcher")
app.include_router(routes.router)
app.include_router(jobs.router)

INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(INDEX)
