# Deployment Guide — Streamlit Community Cloud & GitHub

This document walks you through pushing the project to GitHub and deploying on Streamlit Community Cloud.

## 1) Create a GitHub repository

- Create a new repository on GitHub (e.g., `shapers_academic_advisor`).
- Locally, in PowerShell or terminal, run:

```powershell
cd "f:\My Project\shapers_academic_advisor"
git init
git add .
git commit -m "Initial project scaffold for SHAPERS Academic Advisor"
# Replace the remote URL with your repo
git remote add origin https://github.com/<your-username>/shapers_academic_advisor.git
git branch -M main
git push -u origin main
```

## 2) Add Streamlit secrets

- On Streamlit Community Cloud (https://streamlit.io/cloud), create a new app and link your GitHub repo.
- In the app settings → Secrets, add your `OPENAI_API_KEY` (if using OpenAI). Do NOT commit API keys in the repo.

Example secret name:
- `OPENAI_API_KEY` = sk-***

## 3) Configure the app entrypoint

Streamlit will run `app/streamlit_app.py` by default. If needed, set the `Main file` in Streamlit settings to `app/streamlit_app.py`.

## 4) Runtime & dependencies

Streamlit installs packages from `requirements.txt`. Ensure it contains `streamlit`, `openai`, `vaderSentiment`, `pandas`, and `plotly`.

## 5) Optional: GitHub Actions for CI

A basic `python-app.yml` is included under `.github/workflows/` to install dependencies and run optional checks on push.

## 6) Debugging deployment issues

- If app fails to start, check the `Logs` panel in Streamlit Cloud for errors.
- Common issues: missing secrets, package install errors, or an incorrect main file path.

## 7) Local testing before push

```powershell
cd "f:\My Project\shapers_academic_advisor"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m tests.conversational_tests
streamlit run app/streamlit_app.py
```

If you want I can prepare the `git` commands and create the GitHub repo skeleton for you; you'll need to push the code from your computer or provide a GitHub token to create the repo from here.
