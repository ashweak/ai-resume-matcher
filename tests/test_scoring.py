from app.services.matcher import RUBRIC, _suggestions, build_scorecard
from app.services.resume_checks import analyze


def test_weights_add_up_to_100_percent():
    assert round(sum(w for _, w, _ in RUBRIC.values()), 6) == 1.0


def test_scorecard_is_weighted_and_clamped():
    ai = {"scores": {"keywords": {"score": 10}, "experience": {"score": 99}, "impact": {"score": "x"}}}
    dims, total = build_scorecard(ai)
    # keywords 10*0.30 + experience clamped to 10*0.25 = 5.5 -> 55%
    assert total == 55.0
    assert {d["key"] for d in dims} == set(RUBRIC)


def test_bad_ai_output_does_not_crash():
    dims, total = build_scorecard({"scores": "nonsense"})
    assert total == 0 and len(dims) == len(RUBRIC)
    assert _suggestions(["plain text", {"priority": "urgent", "text": "x"}, 5]) == [
        {"priority": "medium", "text": "plain text"}, {"priority": "medium", "text": "x"}]


def test_resume_checks_find_facts():
    resume = """Juan Dela Cruz
juan@email.com | 09171234567 | github.com/juan | linkedin.com/in/juan
SUMMARY
Aspiring web developer.
EXPERIENCE
- Developed a Laravel inventory system used by 50 staff
- Reduced page load time by 40% with caching
- Helped with office tasks
EDUCATION
BS Information Technology
SKILLS
PHP, Laravel, MySQL"""
    c = analyze(resume)
    assert c["has_email"] and c["has_phone"] and c["has_github"] and c["has_linkedin"]
    assert c["sections"]["experience"] and c["sections"]["education"] and c["sections"]["skills"]
    assert not c["sections"]["certifications"]
    assert c["bullet_count"] == 3
    assert c["action_verb_bullets"] == 2
    assert c["quantified_bullets"] == 2
