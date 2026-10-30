# SkillBridge + ProofKit: an AI opportunity for Cynbit

Submission for the Cynbit **AI/ML Engineer Intern** assessment ("Identify an AI Opportunity for Cynbit").

**What I found on cynbit.in:** the offer is clear, but the proof is thin. The products (Cynbit Studio, Revio AI, TenantEase) get a few words each with no demo, and headline numbers such as 99.9% uptime and 3x ROI have no period, baseline or source.

**What I built, one project in two parts:**

| Part | Answers | What it does |
|---|---|---|
| **SkillBridge** (`app.py`) | "Products are one line with no demo" | A live demo for Cynbit Studio and BitElevate: reads a resume, ranks best-fit roles, explains why with evidence, and turns skill gaps into a short learning path. |
| **Claim Audit** (`pages/1_Claim_Audit.py`) | "Big numbers with no sources" | Flags claims that give a reader no time period, baseline or source, and says what to add. It never says a claim is false. |
| **Case Study Drafter** (`pages/2_Case_Study_Drafter.py`) | "No real case studies" | Drafts a case study from structured client evidence. Publishes only metrics with a baseline, period, source and client confirmation, and lists what to ask the client for the rest. |

## Deliverables

| Deliverable | Where |
|---|---|
| AI Opportunity Report | [`docs/ai_opportunity_report.md`](docs/ai_opportunity_report.md) |
| Proof of concept | this repo: multi-page Streamlit app, CLI, packages `skillbridge/` and `proofkit/` |
| Technical Approach Report | [`docs/technical_approach.md`](docs/technical_approach.md) |

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py        # SkillBridge on the home page; Claim Audit and Case Study Drafter in the sidebar
```

Other commands:

```bash
python -m pytest -q                       # 30 tests
python -m skillbridge.evaluate            # ranking ablation on synthetic resumes
python -m skillbridge.cli resume.txt --top 3 --no-llm
```

LLM steps are optional: set `ANTHROPIC_API_KEY` (and optionally `CLAUDE_MODEL`). Without it everything runs offline on rules and templates.

## How it works

**SkillBridge**
1. **Extract** skills with a taxonomy and alias regexes, keeping an evidence snippet per skill.
2. **Rank** roles: 70% weighted skill coverage + 30% TF-IDF similarity to the role description.
3. **Plan**: greedy weighted set cover picks the courses that close the most important gaps per hour.
4. **Explain**: template by default; an LLM may rephrase the computed facts but cannot add new ones.

**ProofKit**
1. **Audit**: regexes find percentages, multipliers, counts, 24/7 promises, absolute and vague claims, then check for period, baseline and source and rate severity.
2. **Gate**: a case-study metric is published only with baseline, period, source and verification; the percentage change is computed, never typed by hand.
3. **Request**: held-back metrics become a checklist to send the client.
4. **Guardrail**: an optional LLM wording pass is discarded if it adds, changes or removes any number.

## Important caveats

- Roles, courses, sample resumes and the sample case-study client are **synthetic and illustrative**, not Cynbit's real data. The case-study client is fictional; nothing here describes a real Cynbit client.
- The website claims in `data/site_claims.json` are short paraphrases from a text read of cynbit.in on 30 Oct 2026. A flag means the page doesn't back the claim up, not that it is false.
- The SkillBridge evaluation uses 14 hand-written resumes: a sanity check, not an accuracy claim. The claim auditor has no labelled accuracy evaluation yet.
- Do not use SkillBridge to auto-reject candidates. See the responsible-AI section of the opportunity report.

## Layout

```
app.py                  Streamlit home page: SkillBridge demo
pages/                  Claim Audit, Case Study Drafter
skillbridge/            extractor, matcher, pathway, explain, evaluate, cli
proofkit/               claims (auditor), casestudy (drafter + guardrail)
data/                   skills, roles, courses, sample resumes, site claims, sample evidence (JSON)
tests/                  pytest suite
docs/                   the two written reports
```
