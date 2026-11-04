from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="AI Resume & Job Matcher")
app.include_router(router)
