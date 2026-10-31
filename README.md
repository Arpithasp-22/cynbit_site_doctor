# Cynbit Site Doctor

Submission for the Cynbit **AI/ML Engineer Intern** assessment: *Identify an AI Opportunity for Cynbit*.

**🚀 [Live Demo on Streamlit Cloud](https://your-app-url.streamlit.app)** *(Update this URL after deployment)*

> New to this? Read [docs/explainer.md](docs/explainer.md) (also the "How it works" page inside the app) for the plain-language version.

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

---

## 🚀 Quick Start

### Run Locally

**Windows PowerShell:**
```powershell
# Install dependencies
python -m pip install -r requirements.txt

# Run the app
python -m streamlit run app.py
```

**Mac/Linux:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Open the address it prints (usually http://localhost:8501).

* **Saved snapshot** (default): works offline, text-only.
* **Scan a live website**: pick it in the sidebar, keep `https://www.cynbit.in`, press *Scan now*. This is the full version: it also checks titles, descriptions, alt text, links, forms, icon text and more. Needs internet.

### Optional: Enable LLM Features

The app works completely without API keys. To enable optional LLM-powered features (answer phrasing, meta description polishing), add your Anthropic API key:

**Local development:**
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your API key:
   ```toml
   ANTHROPIC_API_KEY = "your-api-key-here"
   ```

**Streamlit Cloud:** Add secrets in the app settings (see deployment section below).

---

## 📦 Deploy to Streamlit Community Cloud

### Prerequisites
1. A GitHub account
2. Your code pushed to a GitHub repository
3. (Optional) An Anthropic API key for LLM features

### Step-by-Step Deployment

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository, branch (usually `main`), and main file path (`app.py`)
   - Click "Deploy"

3. **Configure Secrets (Optional)**
   
   To enable LLM features:
   - In your deployed app dashboard, click the menu (⋮) → "Settings"
   - Go to the "Secrets" section
   - Add your secrets in TOML format:
     ```toml
     ANTHROPIC_API_KEY = "your-api-key-here"
     # Optional: override the default model
     # CLAUDE_MODEL = "claude-sonnet-5-5"
     ```
   - Click "Save"
   - The app will automatically restart with the new secrets

4. **Update the README**
   
   Replace the demo URL at the top of this README with your actual Streamlit Cloud URL.

### Deployment Notes

- **No API key required**: The app works fully without any API keys (uses extractive text methods)
- **API key optional**: Add `ANTHROPIC_API_KEY` in Streamlit secrets for LLM-enhanced features
- **Automatic updates**: Push to your GitHub repository to trigger automatic redeployment
- **Free tier**: Streamlit Community Cloud offers free hosting for public repositories

---

## 🧪 Development

### Run Tests

```powershell
# Install dev dependencies
python -m pip install -r requirements-dev.txt

# Run all tests (77 tests)
python -m pytest -q

# Run assistant accuracy evaluation
python -m sitedoctor.assistant_eval
```

### Project Structure

```
app.py                  Site Doctor: scan, scorecard, findings
pages/                  1 Fix Pack | 2 Ask Cynbit | 3 Case Study Drafter | 4 Bonus: SkillBridge
sitedoctor/             extract, crawler, checks, scoring, fixes, assistant, assistant_eval, ui, secrets
proofkit/               claim auditor and case-study drafter (used by the checks and fixes)
skillbridge/            resume-to-role matcher from the first iteration (bonus)
data/                   snapshot, assistant test questions, sample data
tests/                  77 tests incl. a local fake website
docs/                   AI Opportunity Report, Technical Approach Report
.streamlit/             Streamlit configuration and secrets template
```

---

## 🔒 Security & Privacy

- **No data collection**: Nothing is stored to disk. Leads and chat history exist only in your browser session.
- **Safe crawling**: The crawler respects robots.txt, never visits private addresses (SSRF protection), and stays within the target domain.
- **API keys**: Stored securely in Streamlit secrets (not in code). App works without them.
- **Open source**: All code is reviewable in this repository.

---

## 📊 What is Real and What is Not

* **Live scanning is tested against a local fake website** with planted problems (and a clean page that must not be flagged). I could not scan cynbit.in itself from my environment (network blocked), so **run a live scan on your computer** before presenting; results may differ from the snapshot.
* **The snapshot** is a paraphrased, text-only copy of 14 cynbit.in pages from 30 Oct 2026, plus 13 observations from reading them. It cannot show markup problems, so 18 of the 23 checks are skipped on it and those categories show "needs live scan" instead of a score.
* **Scores are heuristics**, not Google rankings.
* **Assistant accuracy** (see `docs/technical_approach.md`): on 34 questions I wrote myself it declines 100% of questions the site cannot answer and answers about 59 to 64% of answerable ones correctly. It prefers "I don't know" to guessing. It is a baseline, not a finished product.
* The case-study drafter and SkillBridge from the first iteration are kept as secondary pages. Their sample data is synthetic and the sample client is fictional.

---

## 📝 License

This is a submission project for Cynbit's AI/ML Engineer Intern assessment.

---

## 🙋 Questions or Issues?

This is an assessment project. For questions about deployment or functionality, please refer to:
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Community Forum](https://discuss.streamlit.io/)
