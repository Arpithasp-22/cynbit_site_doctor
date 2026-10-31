# Cynbit Site Doctor

Submission for the Cynbit **AI/ML Engineer Intern** assessment: *Identify an AI Opportunity for Cynbit*.

## In one minute

**The problem.** Cynbit's website says it builds AI and software, but a buyer cannot check much of it. Numbers such as "99.9% uptime" and "3x ROI" have no period, baseline or source. The case study lists 35% ROI with no starting figure. Products have no status, price or screenshots. A reader who cannot verify a claim discounts it. In a LinkedIn study of Indian small businesses reported by Business Standard, 95% said a platform's credibility matters more than cost or convenience.

**What this tool does.**

| Step | What happens | Where |
|---|---|---|
| 1. Scan | Reads the site's pages like a browser and Google do (or loads a saved snapshot) | `app.py` |
| 2. Diagnose | 23 checks across trust, content, conversion, search, accessibility and hygiene. Every finding says what, why, where and how to fix it | `app.py` |
| 3. Fix | Ready-to-use fixes: claims to back up with rewrite templates, what each offer page is missing, title and description drafts, a contact-form spec | `pages/1_Fix_Pack.py` |
| 4. Show AI working | **Ask Cynbit**: an assistant that answers visitors only from the site's own pages, says "I could not find that" otherwise, captures a lead, and turns unanswered questions into a list of content to write | `pages/2_Ask_Cynbit.py` |

**Example.** The Marketing Addict case study says "35% improvement in client ROI". The tool flags it: no starting figure, no period, no source, and the hero image is a stock photo. The Fix Pack gives the rewrite template: *"[Metric] changed from [BASELINE] to [VALUE] over [PERIOD], measured by [TOOL OR REPORT]. Client: [NAME, with permission]."*

Cynbit sells AI agents. Ask Cynbit shows that service working on Cynbit's own site, following the advice in Cynbit's own blog (ground answers in company documents; keep a human in the loop).

## Run it (Windows PowerShell, no virtual environment needed)

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the address it prints (usually http://localhost:8501). If `python` is not found, use `py` instead.

* **Saved snapshot** (default): works offline, text-only.
* **Scan a live website**: pick it in the sidebar, keep `https://www.cynbit.in`, press *Scan now*. This is the full version: it also checks titles, descriptions, alt text, links, forms, icon text and more. Needs internet.

Other commands:
```powershell
python -m pytest -q                      # 77 tests
python -m sitedoctor.assistant_eval      # assistant accuracy table
```
Optional: set `ANTHROPIC_API_KEY` to let an LLM phrase answers and polish descriptions. Everything works without it, and LLM output is rejected if it adds any number not in the source.

## What is real and what is not

* **Live scanning is tested against a local fake website** with planted problems (and a clean page that must not be flagged). I could not scan cynbit.in itself from my environment (network blocked), so **run a live scan on your computer** before presenting; results may differ from the snapshot.
* **The snapshot** is a paraphrased, text-only copy of 14 cynbit.in pages from 30 Oct 2026, plus 13 observations from reading them. It cannot show markup problems, so 18 of the 23 checks are skipped on it and those categories show "needs live scan" instead of a score.
* **Scores are heuristics**, not Google rankings.
* **Assistant accuracy** (see `docs/technical_approach.md`): on 34 questions I wrote myself it declines 100% of questions the site cannot answer and answers about 59 to 64% of answerable ones correctly. It prefers "I don't know" to guessing. It is a baseline, not a finished product.
* The case-study drafter and SkillBridge from the first iteration are kept as secondary pages. Their sample data is synthetic and the sample client is fictional.

## Layout

```
app.py                  Site Doctor: scan, scorecard, findings
pages/                  1 Fix Pack | 2 Ask Cynbit | 3 Case Study Drafter | 4 Bonus: SkillBridge
sitedoctor/             extract, crawler, checks, scoring, fixes, assistant, assistant_eval, ui
proofkit/               claim auditor and case-study drafter (used by the checks and fixes)
skillbridge/            resume-to-role matcher from the first iteration (bonus)
data/                   snapshot, assistant test questions, sample data
tests/                  77 tests incl. a local fake website
docs/                   AI Opportunity Report, Technical Approach Report
```
