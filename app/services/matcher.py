import math

from app.providers.base import AIProvider

ANALYSIS_PROMPT = """You are a hiring assistant. Compare the RESUME to the JOB POST.
Return JSON with exactly these keys:
- "matched_skills": list of skills found in both
- "missing_skills": list of skills the job wants but the resume lacks
- "suggestions": list of 3-5 specific resume improvements
- "summary": one short paragraph on overall fit

RESUME:
{resume}

JOB POST:
{job}
"""


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def match_resume(provider: AIProvider, resume: str, job: str) -> dict:
    # 1) Semantic score from embeddings (0-100)
    resume_vec, job_vec = provider.embed([resume, job])
    score = round(max(0.0, cosine_similarity(resume_vec, job_vec)) * 100, 1)

    # 2) Structured analysis from the LLM
    analysis = provider.generate_json(ANALYSIS_PROMPT.format(resume=resume, job=job))

    return {"match_score": score, **analysis}
