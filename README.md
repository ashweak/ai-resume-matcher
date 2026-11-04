# AI Resume & Job Matcher

Upload a resume and paste a job post. The app scores the match with embeddings and uses an LLM to list matched skills, missing skills, and resume fixes.

**Stack:** FastAPI · Google Gemini (free tier) · swappable AI provider (Gemini / Claude)

## Project structure

```
resume-matcher/
├── app/
│   ├── main.py              # FastAPI app
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
│       └── job_store.py     # SQLite store for jobs + embeddings
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
# open http://127.0.0.1:8000/docs
pytest
```

## Build plan

| Phase | What you build | Skill it shows employers |
|---|---|---|
| 1 ✅ | Backend skeleton, swappable provider, `/match` endpoint, tests | FastAPI, clean architecture, testing |
| 2 ✅ | Job library: save many job posts, embed them, rank best-fit jobs for a resume | RAG / vector search (pgvector or ChromaDB) |
| 3 | Frontend: upload page + results dashboard (score, skills chips, suggestions) | Full-stack |
| 4 | Users & history: login, saved analyses (PostgreSQL) | Auth, databases |
| 5 | Rate-limit handling: retry with backoff, caching results | Production AI reliability |
| 6 | Docker + CI (GitHub Actions) + deploy (Render free tier) | DevOps, cloud |
| 7 | Polish: README screenshots, demo video, add to portfolio | Communication |

## Notes
- Free-tier Gemini data may be used by Google to improve products. Don't upload real personal resumes during testing; use sample ones.
- Free-tier rate limits are low, so phase 5 matters for the demo.
