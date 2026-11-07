# AI Resume & Job Matcher

Upload a resume and paste a job post. The app scores the match with embeddings and uses an LLM to list matched skills, missing skills, and resume fixes.

**Stack:** FastAPI · Google Gemini (free tier) · swappable AI provider (Gemini / Claude)

## Project structure

```
resume-matcher/
├── app/
│   ├── main.py              # FastAPI app
│   ├── deps.py              # shared dependencies (AI provider, DB, visitor id, rate limit)
│   ├── static/index.html    # the web page
│   ├── config.py            # settings from .env (AI_PROVIDER switch lives here)
│   ├── api/routes.py        # /api/health, /api/match
│   ├── api/jobs.py          # /api/jobs (add, list, delete) + /api/jobs/rank (vector search)
│   ├── providers/
│   │   ├── base.py          # AIProvider interface (generate_json, embed)
│   │   ├── gemini.py        # default, free tier
│   │   ├── claude.py        # optional, paid
│   │   └── factory.py       # picks provider from AI_PROVIDER
│   └── services/
│       ├── resume_parser.py # PDF/TXT → text
│       ├── matcher.py       # embedding score + LLM analysis
│       ├── job_store.py     # SQLite: jobs + embeddings + AI result cache
│       └── rate_limit.py    # protects the free AI quota
├── tests/test_match.py      # runs with a fake provider (no key, no cost)
├── requirements.txt
└── .env.example
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your Gemini key from aistudio.google.com
uvicorn app.main:app --reload
# open http://127.0.0.1:8000  (app)  or  /docs  (API)
pytest
```

## Build plan

| Phase | What you build | Skill it shows employers |
|---|---|---|
| 1 ✅ | Backend skeleton, swappable provider, `/match` endpoint, tests | FastAPI, clean architecture, testing |
| 2 ✅ | Job library: save many job posts, embed them, rank best-fit jobs for a resume | RAG / vector search (pgvector or ChromaDB) |
| 3 ✅ | Frontend: upload page + results dashboard (score, skills chips, suggestions) | Full-stack |
| 4 ✅ | Private job lists per visitor + saved AI results (SQLite) | Databases, multi-user design |
| 5 ✅ | Retry + fallback models, result caching, per-visitor rate limit | Production AI reliability |
| 6 ✅ | Docker + CI (GitHub Actions) + Render blueprint | DevOps, cloud |
| 7 | Polish: README screenshots, demo video, add to portfolio | Communication |

## Deploy (free, on Render)
1. Sign in at render.com with GitHub.
2. **New → Blueprint**, pick this repo. Render reads `render.yaml`.
3. Paste your `GEMINI_API_KEY` when asked, then **Apply**.
4. Your live link looks like `https://ai-resume-matcher.onrender.com`.

Free-plan notes: the app sleeps after ~15 min idle (first visit takes ~1 min to wake), and saved jobs reset on each redeploy.

## Notes
- Free-tier Gemini data may be used by Google to improve products. Don't upload real personal resumes during testing; use sample ones.
- Free-tier rate limits are low, so phase 5 matters for the demo.
