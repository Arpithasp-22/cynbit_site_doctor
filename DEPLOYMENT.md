# Deployment Guide for Streamlit Community Cloud

This guide walks you through deploying the Cynbit Site Doctor to Streamlit Community Cloud.

## Prerequisites

1. A GitHub account
2. Your code in a GitHub repository
3. (Optional) An Anthropic API key for LLM features

## Step 1: Prepare Your Repository

Ensure these files are in your repository:

- ✅ `app.py` - Main application entry point
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.streamlit/secrets.toml.example` - Example secrets file
- ✅ `.gitignore` - Excludes `.streamlit/secrets.toml` from version control

## Step 2: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Streamlit Cloud deployment"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git push -u origin main
```

## Step 3: Deploy on Streamlit Community Cloud

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app" button
   - Select your repository from the dropdown
   - Choose your branch (usually `main`)
   - Set main file path to `app.py`
   - Click "Deploy"

3. **Wait for Deployment**
   - Streamlit will install dependencies and launch your app
   - This takes 2-5 minutes for the first deployment
   - You'll see logs in real-time

## Step 4: Configure Secrets (Optional)

The app works fully without API keys. To enable LLM features:

1. **Access Settings**
   - In your deployed app, click the menu (⋮) in the top right
   - Select "Settings"

2. **Add Secrets**
   - Go to the "Secrets" section
   - Paste your secrets in TOML format:
     ```toml
     ANTHROPIC_API_KEY = "your-actual-api-key-here"
     
     # Optional: override the default Claude model
     # CLAUDE_MODEL = "claude-sonnet-5-5"
     ```

3. **Save and Restart**
   - Click "Save"
   - The app will automatically restart with the new configuration

## Features That Work Without API Keys

✅ Live website scanning  
✅ All 23 diagnostic checks  
✅ Scorecard and prioritized findings  
✅ Fix Pack generation  
✅ Claim auditing  
✅ Title and meta description drafts (extractive)  
✅ Ask Cynbit assistant (extractive answers)  
✅ Lead capture  
✅ Content gap analysis  

## Features Enhanced by API Keys

🔑 Ask Cynbit: Fluent LLM-phrased answers (vs. extractive sentences)  
🔑 Meta descriptions: LLM-polished versions (with number preservation guardrails)  
🔑 Case study drafter: Improved wording  
🔑 SkillBridge: LLM explanations (vs. template)  

## Troubleshooting

### App Won't Start

**Check logs:**
- View deployment logs in the Streamlit Cloud dashboard
- Common issues:
  - Missing dependency in `requirements.txt`
  - Python version incompatibility (app uses Python 3.10+)
  - Import errors

**Solution:** Fix the issue locally, commit, and push. Streamlit auto-redeploys.

### Import Errors

```
ModuleNotFoundError: No module named 'X'
```

**Solution:** Add the missing package to `requirements.txt`:
```bash
echo "package-name>=version" >> requirements.txt
git add requirements.txt
git commit -m "Add missing dependency"
git push
```

### Secrets Not Working

**Symptoms:**
- LLM features not activating even with API key configured

**Check:**
1. Secrets are in correct TOML format (with quotes around strings)
2. Key name matches exactly: `ANTHROPIC_API_KEY`
3. No extra whitespace or characters
4. App restarted after adding secrets

**Test locally:**
```powershell
# Create .streamlit/secrets.toml
echo 'ANTHROPIC_API_KEY = "test-key"' > .streamlit\secrets.toml
python -m streamlit run app.py
```

### Resource Limits

Streamlit Community Cloud has limits:
- **Memory:** 1 GB (usually sufficient for this app)
- **CPU:** Shared resources
- **Runtime:** Apps sleep after inactivity

If you hit memory limits:
- Reduce `max_pages` when scanning
- The snapshot mode uses minimal resources

## Automatic Updates

After initial deployment, updates are automatic:

```bash
# Make changes to your code
git add .
git commit -m "Update feature X"
git push
```

Streamlit detects the push and redeploys automatically (takes 1-2 minutes).

## Custom Domain (Optional)

Streamlit Community Cloud provides a URL like:
```
https://your-app-name-abc123.streamlit.app
```

For a custom domain:
1. Upgrade to Streamlit Teams or Enterprise plans
2. Follow [Streamlit's custom domain guide](https://docs.streamlit.io/streamlit-community-cloud/manage-your-app/custom-domains)

## Monitoring

**View App Metrics:**
- Go to your app dashboard on share.streamlit.io
- Click "Manage app"
- View logs, metrics, and usage

**Check App Health:**
- Visit your app URL
- Test core features: snapshot mode, scanning, Fix Pack, Ask Cynbit

## Security Best Practices

✅ Never commit API keys or secrets to Git  
✅ Use Streamlit secrets for sensitive configuration  
✅ Review `.gitignore` to ensure `.streamlit/secrets.toml` is excluded  
✅ Rotate API keys if accidentally exposed  
✅ Set appropriate API key usage limits in your Anthropic account  

## Cost Considerations

**Streamlit Community Cloud:**
- Free for public repositories
- Sufficient resources for this app

**Anthropic API Usage:**
- LLM features are optional
- Each Ask Cynbit query: ~1-3¢
- Meta description polish: <1¢ per page
- Monitor usage in Anthropic console

## Support Resources

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io/)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io/)
- **Status Page:** [status.streamlit.io](https://status.streamlit.io/)

## Success Checklist

After deployment, verify:

- [ ] App loads at your Streamlit Cloud URL
- [ ] Snapshot mode works (default)
- [ ] Can scan a live website
- [ ] Fix Pack generates correctly
- [ ] Ask Cynbit responds to questions
- [ ] (If using API key) LLM features activate
- [ ] No console errors in browser developer tools
- [ ] All pages navigate correctly

🎉 **Congratulations!** Your app is live on Streamlit Community Cloud.
