# ResuMatch AI: Resume & Job Matcher

Upload a resume and paste a job post. The app scores the match with embeddings and uses an LLM to list matched skills, missing skills, and resume fixes.

**Stack:** FastAPI · Google Gemini (free tier) · swappable AI provider (Gemini / Claude)

## How resumes are scored

Two scores, for two jobs:

- **Quick match** (instant): embedding similarity between the resume and each saved job, used to rank many jobs at once.
- **Recruiter score** (0–100): the AI grades 6 areas from 0–10 with a reason. The app then applies fixed weights in code, so the AI can't invent the total.

| Area | Weight | Why it matters |
|---|---|---|
| Skills & keywords | 30% | Recruiters and ATS software scan for the job's keywords first |
| Relevant experience & projects | 25% | Projects stand in for experience at entry level |
| Measurable impact | 15% | Bullets with numbers show results, not just duties |
| Education & certifications | 10% | Degree/field fit; weighted the same on major ATS platforms |
| Complete sections | 10% | Contact, LinkedIn/GitHub, skills, experience/projects, education |
| Clear & easy to scan | 10% | Recruiters spend ~6 seconds on a first look |

Facts such as contact info, sections, action-verb bullets and bullets with numbers are measured by code (`app/services/resume_checks.py`) and given to the AI, so its scores stay grounded in the real resume.

Research used:
- [TheLadders eye-tracking study](https://www.bu.edu/com/files/2018/10/TheLadders-EyeTracking-StudyC2.pdf) (6-second scan, what recruiters look at)
- [ATS scoring dimensions and weights](https://ats-screener.vercel.app/docs/scoring/dimensions)
- [Cornell Career Services: entry-level software engineer resumes](https://career.cornell.edu/blog/2026/01/21/entry-level-software-engineer-resume-what-recruiters-want-to-see/)

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
│       ├── matcher.py       # quick match + recruiter scorecard (rubric + weights)
│       ├── resume_checks.py # rule-based facts: contact, sections, bullets, numbers
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
# open http://127.0.0.1:8000
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
