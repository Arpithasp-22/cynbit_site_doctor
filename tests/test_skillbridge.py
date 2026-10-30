import pytest

from skillbridge.data import load_courses, load_roles, validate
from skillbridge.explain import explain, facts
from skillbridge.extractor import extract_skills, extract_with_evidence
from skillbridge.matcher import RoleMatcher
from skillbridge.pathway import build_path


def test_data_files_are_consistent():
    assert validate() == []


def test_extractor_handles_symbols_and_aliases():
    skills = extract_skills("Built APIs in Node.js with PostgreSQL, tested in C++ and CI/CD via GitHub Actions")
    assert {"node.js", "sql", "c++", "ci/cd"} <= skills


def test_extractor_avoids_substring_false_positives():
    # 'java' must not fire on 'javascript'; 'react' must not fire on 'reaction'
    assert "java" not in extract_skills("I write JavaScript")
    assert "react" not in extract_skills("A chemical reaction experiment")
    # 'rest' alias must not fire on 'interest' or 'forest'
    assert "rest apis" not in extract_skills("Interest in random forest models")


def test_extractor_evidence_snippets():
    ev = extract_with_evidence("Trained a random forest using scikit-learn on churn data")
    assert "machine learning" in ev and "scikit-learn" in ev["machine learning"]


@pytest.fixture(scope="module")
def matcher():
    return RoleMatcher()


def test_ranking_prefers_relevant_role(matcher):
    text = "Trained PyTorch CNN models, pandas, NumPy, scikit-learn, statistics, Python, Git"
    assert matcher.rank(text)[0].role.id == "aiml"


def test_scores_are_bounded_and_sorted(matcher):
    ranked = matcher.rank("Python and SQL")
    scores = [m.score for m in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_empty_resume_does_not_crash(matcher):
    ranked = matcher.rank("")
    assert len(ranked) == len(load_roles())
    assert ranked[0].score == 0.0


def test_missing_skills_reported(matcher):
    m = next(x for x in matcher.rank("React and JavaScript only") if x.role.id == "fullstack")
    assert "node.js" in m.missing_required and "react" in m.matched_required


def test_path_closes_gaps_and_respects_catalogue(matcher):
    m = next(x for x in matcher.rank("HTML and CSS") if x.role.id == "fullstack")
    path = build_path(m)
    closed = {s for st in path.steps for s in st.closes}
    # everything required and missing is either closed by a step or reported uncovered
    assert closed | set(path.uncovered) >= set(m.missing_required)
    assert path.total_hours == sum(st.course.hours for st in path.steps)
    assert len({st.course.id for st in path.steps}) == len(path.steps)  # no duplicate courses
    levels = [st.course.level for st in path.steps]
    assert levels == sorted(levels)  # foundations first


def test_no_path_needed_when_all_skills_present(matcher):
    full = " ".join(load_roles()[0].required)  # every required skill of the first role
    m = next(x for x in matcher.rank(full) if x.role.id == load_roles()[0].id)
    assert m.missing_required == {}
    assert build_path(m).steps == []


def test_uncovered_skill_is_reported():
    m = RoleMatcher().rank("")[0]
    m.missing_required = {"skill-with-no-course": 3}
    assert build_path(m, courses=load_courses()).uncovered == ["skill-with-no-course"]


def test_explanation_template_is_grounded_in_facts(matcher, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = matcher.rank("Python, pandas")[0]
    path = build_path(m)
    text, source = explain(m, path)
    assert source == "template"
    assert m.role.title in text
    assert str(round(m.score * 100)) in text
    assert facts(m, path)["total_hours"] == path.total_hours
