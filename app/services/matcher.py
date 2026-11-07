"""Resume vs job analysis, scored the way recruiters and ATS software do.

Research behind the rubric:
- Recruiters spend ~6 seconds on a first look, mostly on titles, companies, dates,
  education, and keywords that match the job (TheLadders eye-tracking study).
- ATS software scores keyword match, section completeness, experience relevance,
  education, quantified results, and parse-friendly formatting.
- For entry-level tech roles, projects, technical skills, GitHub/portfolio links and
  action-verb bullets carry the most weight.

The AI gives each dimension a 0-10 score with a reason; the final weighted score is
computed here in code, so the math is consistent and can't be invented by the model.
"""
import math

from app.providers.base import AIProvider
from app.services.resume_checks import analyze, facts_for_prompt

# key: (label, weight, what the AI should judge)
RUBRIC = {
    "keywords": ("Skills & keywords", 0.30,
                 "How many of the job's required skills, tools and keywords appear in the resume."),
    "experience": ("Relevant experience & projects", 0.25,
                   "Do the jobs, internships and projects show the work this role needs? Projects count for entry-level."),
    "impact": ("Measurable impact", 0.15,
               "Do bullets show results with numbers (%, users, time saved) and start with action verbs?"),
    "education": ("Education & certifications", 0.10,
                  "Does the degree, field, and any certifications fit what the job asks for?"),
    "completeness": ("Complete sections", 0.10,
                     "Contact info, LinkedIn/GitHub/portfolio, skills, experience/projects and education present?"),
    "clarity": ("Clear & easy to scan", 0.10,
                "Would a recruiter understand the candidate in 6 seconds? Concise, consistent, 1-2 pages."),
}

PROMPT = """You are an experienced technical recruiter screening a resume for the JOB POST below.
Judge it like a real recruiter and an ATS would. Be honest and specific; do not inflate scores.

Score each dimension from 0 to 10 (10 = excellent, 5 = average, 0 = missing):
{rubric}

Facts measured from the resume text (use them, they are accurate):
{facts}

Return JSON with exactly these keys:
- "scores": object with keys {keys}, each {{"score": integer 0-10, "reason": one short sentence}}
- "first_impression": one sentence: what a recruiter notices in the first 6 seconds
- "matched_skills": up to 8 short skill names the job wants and the resume has
- "missing_skills": up to 8 short skill names the job wants but the resume lacks
- "strengths": 2-3 short phrases on what makes this candidate stand out for this job
- "suggestions": 3-4 items, each {{"priority": "high" | "medium" | "low", "text": one specific sentence}}, most important first
- "summary": 1-2 sentences: overall fit and whether to apply now

RESUME:
{resume}

JOB POST:
{job}
"""


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _clamp(value, lo=0, hi=10) -> int:
    try:
        return max(lo, min(hi, round(float(value))))
    except (TypeError, ValueError):
        return 0


def _strings(value, limit: int) -> list[str]:
    return [str(v).strip() for v in (value or []) if str(v).strip()][:limit] if isinstance(value, list) else []


def build_scorecard(ai: dict) -> tuple[list[dict], float]:
    """Turn the AI's raw scores into a clean list + weighted 0-100 score."""
    raw = ai.get("scores") if isinstance(ai.get("scores"), dict) else {}
    dims, total = [], 0.0
    for key, (label, weight, _) in RUBRIC.items():
        item = raw.get(key) if isinstance(raw.get(key), dict) else {}
        score = _clamp(item.get("score"))
        dims.append({"key": key, "label": label, "weight": int(weight * 100), "score": score,
                     "reason": str(item.get("reason", "")).strip()})
        total += score * weight
    return dims, round(total * 10, 1)


def _suggestions(value) -> list[dict]:
    out = []
    for s in value if isinstance(value, list) else []:
        if isinstance(s, dict) and str(s.get("text", "")).strip():
            p = str(s.get("priority", "medium")).lower()
            out.append({"priority": p if p in ("high", "medium", "low") else "medium", "text": str(s["text"]).strip()})
        elif isinstance(s, str) and s.strip():
            out.append({"priority": "medium", "text": s.strip()})
    return out[:4]


def match_resume(provider: AIProvider, resume: str, job: str) -> dict:
    checks = analyze(resume)

    # 1) Quick similarity from embeddings (0-100): how close the texts are in meaning.
    resume_vec, job_vec = provider.embed([resume, job])
    similarity = round(max(0.0, cosine_similarity(resume_vec, job_vec)) * 100, 1)

    # 2) Recruiter-style scorecard from the AI. Long inputs are trimmed: faster + fits free limits.
    ai = provider.generate_json(PROMPT.format(
        rubric="\n".join(f"- {k}: {label} ({int(w * 100)}%). {how}" for k, (label, w, how) in RUBRIC.items()),
        facts=facts_for_prompt(checks),
        keys=", ".join(RUBRIC),
        resume=resume[:8000],
        job=job[:8000],
    ))
    dimensions, recruiter_score = build_scorecard(ai)

    return {
        "match_score": similarity,
        "recruiter_score": recruiter_score,
        "dimensions": dimensions,
        "first_impression": str(ai.get("first_impression", "")).strip(),
        "matched_skills": _strings(ai.get("matched_skills"), 8),
        "missing_skills": _strings(ai.get("missing_skills"), 8),
        "strengths": _strings(ai.get("strengths"), 3),
        "suggestions": _suggestions(ai.get("suggestions")),
        "summary": str(ai.get("summary", "")).strip(),
        "checks": checks,
    }
