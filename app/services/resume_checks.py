"""Fast, rule-based resume checks (no AI, no cost).

Based on what recruiters and applicant tracking systems (ATS) look for:
- contact info and links (LinkedIn / GitHub / portfolio)
- standard sections (experience, education, skills, projects)
- bullet points that start with action verbs
- numbers that show impact ("cut load time by 40%")
- a length that fits 1-2 pages
These facts are also given to the AI so its scores are grounded in the real resume.
"""
import re

ACTION_VERBS = {
    "achieved", "analyzed", "automated", "built", "collaborated", "configured", "coordinated", "created",
    "debugged", "deployed", "designed", "developed", "documented", "drove", "enhanced", "established",
    "implemented", "improved", "increased", "integrated", "launched", "led", "maintained", "managed",
    "migrated", "optimized", "organized", "reduced", "refactored", "resolved", "streamlined",
    "supported", "tested", "trained", "upgraded",
}

SECTIONS = {
    "experience": r"\b(work )?experience|employment|internship|work history",
    "education": r"\beducation|university|college|bachelor|bs ?it|bsit|bscs|degree",
    "skills": r"\b(technical )?skills|technologies|tech stack|tools",
    "projects": r"\bprojects?\b|capstone|thesis",
    "certifications": r"\bcertifications?|certificates?|licenses?",
    "summary": r"\bsummary|objective|profile|about me",
}

BULLET = re.compile(r"^\s*([-•*▪●◦‣]|\d+[.)])\s+")
NUMBER = re.compile(r"\d")  # any number in a bullet ("3 departments", "40%", "25 PCs") counts as a measurable result


def analyze(text: str) -> dict:
    lower = text.lower()
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-]*", text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Lines that describe work: bullets, or longer lines starting with a verb.
    bullets = [
        BULLET.sub("", ln) for ln in lines
        if BULLET.match(ln) or (len(ln.split()) >= 6 and ln.split()[0].lower().rstrip(",.:") in ACTION_VERBS)
    ]
    first_words = [b.split()[0].lower().rstrip(",.:") for b in bullets if b.split()]
    action = sum(w in ACTION_VERBS for w in first_words)
    quantified = sum(bool(NUMBER.search(b)) for b in bullets)

    return {
        "word_count": len(words),
        "estimated_pages": round(max(1, len(words)) / 450, 1),
        "has_email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)),
        "has_phone": bool(re.search(r"(\+?63|0)9\d{2}[\s-]?\d{3}[\s-]?\d{4}|\+?\d[\d\s()-]{8,}\d", text)),
        "has_linkedin": "linkedin.com" in lower,
        "has_github": "github.com" in lower or "github.io" in lower,
        "sections": {name: bool(re.search(rx, lower)) for name, rx in SECTIONS.items()},
        "bullet_count": len(bullets),
        "action_verb_bullets": action,
        "quantified_bullets": quantified,
    }


def facts_for_prompt(c: dict) -> str:
    found = [k for k, v in c["sections"].items() if v] or ["none detected"]
    missing = [k for k, v in c["sections"].items() if not v]
    return (
        f"- Length: about {c['word_count']} words (~{c['estimated_pages']} pages)\n"
        f"- Contact: email={'yes' if c['has_email'] else 'no'}, phone={'yes' if c['has_phone'] else 'no'}, "
        f"LinkedIn={'yes' if c['has_linkedin'] else 'no'}, GitHub={'yes' if c['has_github'] else 'no'}\n"
        f"- Sections found: {', '.join(found)}; not found: {', '.join(missing) or 'none'}\n"
        f"- Bullet points: {c['bullet_count']}, starting with action verbs: {c['action_verb_bullets']}, "
        f"with numbers/metrics: {c['quantified_bullets']}"
    )
