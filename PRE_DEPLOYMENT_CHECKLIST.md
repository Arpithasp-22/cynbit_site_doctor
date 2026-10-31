# Pre-Deployment Checklist

Complete this checklist before deploying to Streamlit Community Cloud.

## ✅ Code Preparation

- [x] All file paths are relative (no hardcoded absolute paths)
- [x] API keys loaded from secrets/environment (not hardcoded)
- [x] .gitignore includes `.streamlit/secrets.toml`
- [x] requirements.txt contains only production dependencies
- [x] No sensitive data in code or data files

## ✅ Local Testing

Run these tests locally before deployment:

### 1. Basic Functionality (No API Key)
```powershell
python -m streamlit run app.py
```

**Test:**
- [ ] App starts without errors
- [ ] Home page loads with snapshot mode
- [ ] Scorecard displays correctly
- [ ] All findings show properly
- [ ] "Fix Pack" page works
- [ ] "Ask Cynbit" page works (extractive mode)
- [ ] "Case Study Drafter" page loads
- [ ] "SkillBridge" page loads
- [ ] All download buttons work

### 2. Live Scanning
- [ ] Can enter a URL in sidebar
- [ ] "Scan now" button works
- [ ] Pages are fetched and displayed
- [ ] Findings update based on live scan
- [ ] No crashes during scan

### 3. Import Test
```powershell
python -c "import app; from sitedoctor import *; from proofkit import *; from skillbridge import *; print('All imports OK')"
```
- [ ] No import errors

### 4. Secrets Module Test
```powershell
python -c "from sitedoctor.secrets import get_secret, has_api_key, get_model; print('OK')"
```
- [ ] Secrets module loads correctly

## ✅ Optional: LLM Features Test

Only if you have an Anthropic API key:

### Setup Secrets Locally
```powershell
# Create secrets file
New-Item -ItemType Directory -Force -Path .streamlit
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
# Edit .streamlit\secrets.toml and add your key
```

### Test LLM Features
- [ ] Ask Cynbit uses LLM mode (check mode indicator)
- [ ] Meta description polishing works in Fix Pack
- [ ] Case study polishing works
- [ ] SkillBridge uses LLM explanations
- [ ] No errors in console

## ✅ Repository Setup

### GitHub Repository
- [ ] Code pushed to GitHub
- [ ] Repository is public (for free Streamlit hosting)
- [ ] `.streamlit/secrets.toml` is NOT in repository
- [ ] `.gitignore` is properly configured
- [ ] README.md is updated

### Verify Git Status
```bash
git status
# Should NOT show .streamlit/secrets.toml
# Should NOT show .env files
```

## ✅ Required Files Present

Check these files exist:
- [ ] `app.py` (main entry point)
- [ ] `requirements.txt`
- [ ] `.streamlit/config.toml`
- [ ] `.streamlit/secrets.toml.example`
- [ ] `README.md` (with deployment instructions)
- [ ] `DEPLOYMENT.md` (detailed guide)
- [ ] `.gitignore`
- [ ] `packages.txt` (even if empty)

## ✅ Documentation Review

- [ ] README.md has clear local setup instructions
- [ ] README.md has deployment section
- [ ] DEPLOYMENT.md is complete
- [ ] Secret management is documented
- [ ] All instructions are tested

## ✅ Streamlit Cloud Account

- [ ] Account created at share.streamlit.io
- [ ] GitHub connected
- [ ] (Optional) Anthropic API key ready for secrets

## 🚀 Ready to Deploy!

Once all items are checked:

1. Push final changes to GitHub:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Click "New app"

4. Select:
   - Repository: `your-username/cynbit-site-doctor`
   - Branch: `main`
   - Main file: `app.py`

5. Click "Deploy"

6. (Optional) Add secrets after deployment:
   - Go to app settings
   - Add ANTHROPIC_API_KEY in secrets section

## Post-Deployment Verification

After deployment completes:

- [ ] App URL is accessible
- [ ] Home page loads
- [ ] Snapshot mode works
- [ ] Can navigate to all pages
- [ ] Fix Pack generates
- [ ] Ask Cynbit responds
- [ ] No console errors (check browser DevTools)
- [ ] (Optional) LLM features work if API key configured

## Update README

After successful deployment:

- [ ] Update README.md with actual deployment URL
- [ ] Commit and push the update

```bash
# In README.md, replace:
# 🚀 [Live Demo on Streamlit Cloud](https://your-app-url.streamlit.app)
# With your actual URL

git add README.md
git commit -m "Add live demo URL"
git push
```

## Troubleshooting

If deployment fails, check:

1. **Deployment logs** in Streamlit Cloud dashboard
2. **requirements.txt** - all packages spelled correctly?
3. **Python version** - app needs Python 3.10+
4. **Import errors** - test locally first
5. **File paths** - all relative, no hardcoded paths?

See DEPLOYMENT.md for detailed troubleshooting steps.

---

## Quick Command Reference

```powershell
# Test app locally
python -m streamlit run app.py

# Test imports
python -c "import app; print('OK')"

# Check secrets module
python -c "from sitedoctor.secrets import has_api_key; print(has_api_key())"

# Run tests (requires dev dependencies)
python -m pip install -r requirements-dev.txt
python -m pytest -q

# Check git status
git status

# Push to GitHub
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

---

**Good luck with your deployment! 🚀**
