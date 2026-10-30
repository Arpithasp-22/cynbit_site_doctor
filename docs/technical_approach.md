# Technical Approach Report: SkillBridge and ProofKit

Sections 1-9 cover **SkillBridge** (the Cynbit Studio product demo). Section 10 covers **ProofKit** (the claim auditor and case-study drafter that back up the website's claims).

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
python -m pytest -q                      # 30 tests
python -m skillbridge.evaluate           # ablation table
streamlit run app.py                     # UI
python -m skillbridge.cli resume.txt     # CLI
export ANTHROPIC_API_KEY=...             # optional LLM explanation
```

The Streamlit app is multi-page: `app.py` is the SkillBridge demo, and `pages/` holds Claim Audit and Case Study Drafter.

## 10. ProofKit

### 10.1 Problem

The website's offer is clear but its evidence is thin: headline numbers have no period, baseline or source, and there are no case-study write-ups. ProofKit has two parts: (a) find claims a reader cannot verify and say what to add; (b) draft case studies from structured client evidence without ever publishing a number that lacks backing.

### 10.2 Claim auditor (`proofkit/claims.py`)

```
text or claim list --> detect claim types --> check context --> issues --> severity --> fix suggestion
```

| Step | Detail |
|---|---|
| Detect | Regexes for percentages, multipliers (3x), counts (50k+, 1000+), always-on promises (24/7), the absolute "100%", and a short list of vague superlatives ("revolutionary", "premier", "globally recognized"). |
| Check | For measured claims: is there a time period, a baseline ("from", "vs", "compared to") and a source ("source", "according to", "audited", a URL)? For 24/7 claims: is coverage defined (channels, response time)? Structured fields (source, period, baseline) can be supplied alongside the text. |
| Severity | High: absolute claim or three missing items. Medium: two. Low: one. OK: none. |
| Output | Findings sorted by severity, each with the reasons and a plain-language suggestion. Exportable as CSV from the page. |

Design choice: rules rather than an LLM, because the check is a definable list of properties, results must be explainable line by line, and the auditor must never say a claim is false. It only reports that the page does not let a reader check it.

**Result on real input:** 13 claims taken from the homepage and Our Story pages produced 9 high, 1 medium, 3 low and 0 fully supported.

### 10.3 Case-study drafter (`proofkit/casestudy.py`)

Input is structured evidence: client, industry, problem, solution, services, an optional quote with a consent flag, and metrics. Each metric has value, baseline, unit, time period, source and a verified flag.

- **Gate.** A metric is published only if baseline, period, source and verification are all present. Others are held back.
- **Computed change.** The percentage change is calculated from baseline and value, never typed in by hand, so the numbers in the text always agree.
- **Quotes.** Included only when consent is true.
- **Empty results.** If nothing passes the gate, the Results section says "No verified metrics yet" rather than filling the space.
- **Client request.** For every held-back metric, the tool lists exactly what to ask the client (baseline, period, source, confirmation), and asks for quote permission if missing.
- **Draft notice.** Every draft ends by stating that client approval is required.

### 10.4 LLM wording pass and its guardrail

The optional LLM step receives the finished draft and may only improve flow and tone (system prompt in `casestudy.py`). A guardrail compares the set of numbers in the original and the edit; if any number is added, changed or removed, the edit is discarded and the original is returned, and the page shows why. This is the automated check that SkillBridge's explanation step still lacks (section 5), and a good candidate to port back.

### 10.5 Testing and limits

18 tests cover: bare claims flagged for all three gaps; a well-supported claim passing; absolute and vague claims; the 24/7 case; structured context; multi-line page audit and ordering; the metric gate; computed percentage change including zero and text baselines; unverified metrics hidden or labelled; quote consent; no invented results; the evidence request; the number guardrail; and the no-API-key path. The three Streamlit pages were also exercised headlessly, including invalid JSON input.

Limits to be aware of:

- Regex context checks are per sentence and English only. A claim whose source is on another page will be over-flagged; a claim containing words like "from" in another sense can be under-flagged. Output is a review list, not a verdict.
- No labelled accuracy evaluation of the auditor exists yet. Next step is to hand-label 100+ claims from several sites and report precision and recall.
- The sample client and all its numbers are fictional. Nothing in the drafter is based on a real Cynbit client.
- The LLM pass preserves numbers but cannot check that its wording stays faithful in meaning; a human reviews every draft.

### 10.6 Next steps

1. Crawl the whole site from its sitemap and audit every page, tracking the share of claims with period, baseline and source over time.
2. Pull evidence directly from client analytics exports (CSV upload first, connectors later) so metrics arrive with their source attached.
3. Add an LLM-assisted classifier for ambiguous claims, evaluated against the hand-labelled set before it is allowed to change any severity.
4. Add approval workflow: client sign-off link, version history, and publishing only after sign-off.
