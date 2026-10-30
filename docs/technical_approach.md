# Technical Approach Report: SkillBridge

## 1. Problem

Given a candidate's resume text, (a) rank a set of target roles by fit, (b) explain the ranking, (c) identify missing skills, and (d) propose the shortest sensible learning path from Cynbit's course catalogue. The goal of the prototype is a transparent baseline that can be measured and then improved with real data.

## 2. Architecture

```
resume (txt / pdf / pasted)
        |
        v
  text extraction (pypdf for PDF)
        |
        v
  skill extractor  --->  detected skills + evidence snippets
  (taxonomy + alias regex)            |
        |                              v
        +-----> role matcher: 0.7 * weighted skill coverage
        |                     0.3 * TF-IDF cosine(resume, role text)
        v
  ranked roles with matched / missing skills
        |
        v
  learning-path builder (greedy weighted set cover over course catalogue)
        |
        v
  explainer: deterministic template  --(optional)-->  LLM rephrase of computed facts
        |
        v
  Streamlit UI / CLI
```

Code layout: `skillbridge/extractor.py`, `matcher.py`, `pathway.py`, `explain.py`, `data.py`; data in `data/*.json`; tests in `tests/`.

## 3. Data pipeline

| Stage | Detail |
|---|---|
| Inputs | Resume text; `skills.json` (taxonomy of ~55 skills with aliases); `roles.json` (12 roles with weighted required skills and nice-to-haves); `courses.json` (20 modules mapped to skills, with level and hours). |
| Normalisation | Lower-casing, unicode dash and quote cleanup, whitespace collapse. |
| Extraction | One compiled regex per skill. Boundaries are custom so `c++` and `node.js` match, while `java` does not match inside `javascript`, and `rest` does not match inside `interest`. |
| Validation | `data.validate()` checks that every skill referenced by a role or course exists in the taxonomy (covered by a test). |
| Storage | None. The app is stateless, so no resume is persisted. |

**Data caveat:** the role profiles, course catalogue and all 14 sample resumes are synthetic and illustrative, written for this assessment. They are not Cynbit's real data.

## 4. Model and algorithm choices

| Component | Choice | Why | Alternatives considered |
|---|---|---|---|
| Skill extraction | Rule-based taxonomy matching | Deterministic, free, auditable, and enough for a closed vocabulary | Sentence-embedding matching or an NER model would catch unseen phrasing but need labelled data to validate; an LLM extractor is flexible but costs money per resume and is harder to audit. Planned as a second-stage fallback. |
| Role ranking | Hybrid: skill coverage plus TF-IDF cosine | Skill coverage is interpretable; TF-IDF adds a soft signal from context words | Pure embeddings (e.g. a sentence-transformer) are likely better at semantic similarity but were left out to keep the prototype dependency-light and offline; learning-to-rank needs outcome labels that do not exist yet. |
| Weights | 0.7 skills / 0.3 text, nice-to-have counts half | Set by judgement so that explainable evidence dominates | Should be tuned on real labelled data (grid search against precision@k). |
| Learning path | Greedy weighted set cover, value per hour, then sorted by level | Small catalogue, near-optimal for set cover, easy to explain | ILP gives the exact optimum but adds a solver for little gain at this scale. Prerequisite graphs are a sensible extension. |
| Explanation | Template by default; optional LLM rephrase | Works offline; LLM adds natural tone without being a source of facts | Letting the LLM decide skills or courses directly (rejected: ungrounded, unauditable). |

## 5. Prompt engineering for the optional LLM step

The LLM never sees the resume and never makes decisions. It receives a JSON of facts computed by the code (role, fit percent, matched and missing skills, path with hours, uncovered skills) and this system prompt:

> You are a career coach inside a learning platform. You receive a JSON object of facts about a candidate's fit for a role. Write a short, encouraging explanation (max 120 words) in plain English. Use ONLY the facts provided: do not invent skills, courses, hours, or percentages. Mention matched strengths, the most important gaps, and the first course to take. Do not guarantee job outcomes.

Design decisions:

- **Grounding by construction.** Only computed facts go in, so wrong skills cannot be introduced by the resume text (also reduces prompt-injection risk from resume content).
- **Fail-safe.** No API key, a network error, or an empty reply all fall back to the template; the UI shows which source was used.
- **Configurable model.** Set `CLAUDE_MODEL`; the default is in `explain.py`.
- **Not yet done:** an automated check that the LLM output only mentions provided skills and numbers. Listed under next steps.

## 6. Evaluation

`python -m skillbridge.evaluate` compares ranking modes on the 14 synthetic resumes:

| Mode | Top-1 | Top-3 |
|---|---|---|
| Text similarity only | 86% | 100% |
| Skills only | 100% | 100% |
| Hybrid (default) | 100% | 100% |

**How to read this honestly.** The resumes and the taxonomy were written by the same person, so skills-only is expected to do very well. The result shows the pipeline is wired correctly and that TF-IDF alone is a weaker baseline. It does **not** show the hybrid beats skills-only, and it is **not** an accuracy estimate for real resumes. The 12 unit tests cover extraction edge cases (symbols, aliases, substring false positives), ranking bounds and ordering, empty input, path correctness (no duplicate courses, foundations first, uncovered gaps reported) and explanation grounding.

**Proper evaluation plan:** 100+ anonymised, consented resumes labelled by mentors with acceptable target roles; report precision@1/3, extraction precision/recall per skill, and slice results by degree type, college tier and resume length to look for uneven performance.

## 7. Known limitations

- Closed vocabulary: skills not in the taxonomy are invisible. Resumes in other languages are not handled.
- No notion of proficiency or recency: "used Docker once" and "five years of Docker" look the same.
- Negations ("no experience with AWS") and keyword stuffing are not detected.
- PDF text extraction can fail on scanned or heavily formatted resumes (no OCR).
- Role profiles and weights reflect my judgement, not market data.

## 8. Execution plan and scaling

| Phase | Work | Output |
|---|---|---|
| 0 (done) | Prototype, tests, evaluation harness | This repository |
| 1 | Replace synthetic roles/courses with Cynbit's; collect labelled resumes; error analysis | Real baseline numbers |
| 2 | Add embedding-based soft matching for unseen skills; skill-level signals; negation handling | Higher recall, measured against Phase 1 |
| 3 | Wrap as a FastAPI service with a `/match` endpoint; integrate into Studio assessments; add logging of consented outcomes | Pilot to one cohort behind a feature flag |
| 4 | Learn weights from outcomes; add prerequisite graph; fairness audit; LLM-output guardrail check | Production candidate |

Operational notes: the current engine runs in milliseconds on CPU, so cost is dominated by the optional LLM call (one short request per displayed role). Monitor extraction coverage (share of resumes with zero detected skills), score distribution drift, and user corrections as a free labelled signal.

## 9. Run it

```bash
pip install -r requirements.txt
python -m pytest -q                      # 12 tests
python -m skillbridge.evaluate           # ablation table
streamlit run app.py                     # UI
python -m skillbridge.cli resume.txt     # CLI
export ANTHROPIC_API_KEY=...             # optional LLM explanation
```
