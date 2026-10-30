# SkillBridge: an AI opportunity for Cynbit

Submission for the Cynbit **AI/ML Engineer Intern** assessment ("Identify an AI Opportunity for Cynbit").

SkillBridge reads a resume, ranks best-fit roles, explains why (with evidence), and turns the skill gaps into a short learning path. It is designed as a feature for **Cynbit Studio** (job matching, career preparation) and **BitElevate** (training).

## Deliverables

| Deliverable | Where |
|---|---|
| AI Opportunity Report | [`docs/ai_opportunity_report.md`](docs/ai_opportunity_report.md) |
| Proof of concept | this repo: Streamlit app (`app.py`), CLI, Python package `skillbridge/` |
| Technical Approach Report | [`docs/technical_approach.md`](docs/technical_approach.md) |

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Other commands:

```bash
python -m pytest -q                       # unit tests
python -m skillbridge.evaluate            # ranking ablation on synthetic resumes
python -m skillbridge.cli resume.txt --top 3 --no-llm
```

An LLM-written explanation is optional: set `ANTHROPIC_API_KEY` (and optionally `CLAUDE_MODEL`). Without it, a deterministic template is used, so the demo works offline.

## How it works

1. **Extract** skills from the resume with a taxonomy and alias regexes, keeping an evidence snippet per skill.
2. **Rank** roles: 70% weighted skill coverage + 30% TF-IDF similarity to the role description.
3. **Plan**: greedy weighted set cover picks the courses that close the most important gaps per hour.
4. **Explain**: template by default; an LLM may rephrase the computed facts but cannot add new ones.

## Important caveats

- Roles, courses and all sample resumes are **synthetic and illustrative**, not Cynbit's real data. Replace `data/*.json` with the real catalogue.
- The evaluation uses 14 hand-written resumes. It is a sanity check, not an accuracy claim.
- Do not use this to auto-reject candidates. See the responsible-AI section of the opportunity report.

## Layout

```
app.py                  Streamlit UI
skillbridge/            extractor, matcher, pathway, explain, evaluate, cli
data/                   skills, roles, courses, synthetic resumes (JSON)
tests/                  pytest suite
docs/                   the two written reports
```
