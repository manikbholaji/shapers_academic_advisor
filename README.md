<<<<<<< HEAD
# shapers_academic_advisor
=======
# SHAPERS Academic Advisor

This repository contains the SHAPERS Academic Advisor — a Streamlit-based academic advising chatbot with provider-agnostic AI client, Indian-board knowledge base, recommender, and appointment booking.

## What I prepared for you
- Expanded Google failure-mode unit tests (`tests/test_google_failure_modes.py`).
- Provider health-check script (`scripts/run_health_checks.py`).
- CI workflow with daily scheduled health checks (`.github/workflows/ci.yml`).
- Updated `requirements.txt` (includes `requests`).

## Run locally
1. Create and activate a Python 3.11 virtualenv.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
pip install pytest
```

3. Run the Streamlit app:

```powershell
streamlit run app/streamlit_app.py
```

4. Run tests:

```powershell
pytest -q
```

## Deploy from GitHub (Streamlit Community Cloud)
1. Push this repository to GitHub (create a new repo or use existing). Example commands:

```powershell
cd "f:\My Project\shapers_academic_advisor"
git init
git remote add origin https://github.com/<your-username>/<repo>.git
git checkout -b main
git add .
git commit -m "chore: prepare repo for deployment and CI"
git push --set-upstream origin main
```

2. Open https://share.streamlit.io and click **New app** → connect your GitHub repo → select branch `main` and file `app/streamlit_app.py`.

3. In the Streamlit app settings, add required secrets under **Advanced settings > Secrets** (or in the app Settings UI):

- `OPENAI_API_KEY` (if using OpenAI)
- `GOOGLE_API_KEY` (if using Google Generative API)
- `DIALOGFLOW_PROJECT_ID` and `DIALOGFLOW_ACCESS_TOKEN` (if using Dialogflow)

4. The app will be deployed and a public URL (https://share.streamlit.io/...) will be available.

## CI and scheduled health checks
- The GitHub Actions workflow runs tests on push/PR and runs a daily scheduled provider health-check job that calls `scripts/run_health_checks.py`.
- To enable health checks with real keys, add the secrets to your GitHub repo (Settings → Secrets): `GOOGLE_API_KEY`, `DIALOGFLOW_PROJECT_ID`, `DIALOGFLOW_ACCESS_TOKEN`, and `OPENAI_API_KEY`.

## Demo cheat-sheets (live preview and downloads)

- The `Demo` page now generates live image previews and downloadable PNG/PDF cheat-sheets for English, Hindi, Hinglish, and Punjabi.
- PDF and PNG generation use `reportlab` and `Pillow` respectively; these are listed in `requirements.txt` so Streamlit will install them automatically when deployed.
- Locally, run `pip install -r requirements.txt` to enable in-app generation of images and PDFs.

## Opening a PR (optional)
If you'd like me to open a PR with these changes but I don't have access to your GitHub account here. You can use the GitHub CLI locally:

```powershell
gh auth login
git checkout -b feature/ci-health-checks
git add .
git commit -m "ci: add scheduled health-checks and provider health script; add Google failure-mode tests"
git push --set-upstream origin feature/ci-health-checks
gh pr create --title "ci: add provider health checks and expanded tests" --body "Adds expanded Google failure-mode unit tests and scheduled provider health checks in CI." --base main
```

If you'd like, tell me when you've pushed or give me temporary `git`/`gh` access (not recommended). I can then open the PR for you.

## Next steps I can do for you
- Open the PR for you (if you enable `git`/`gh` on this machine or provide secure access).
- Add a GitHub Action to automatically deploy to a cloud host (requires service tokens).
- Add more end-to-end conversational tests.
# SHAPERS Academic Advisor for Punjab Students

Punjab-focused academic advisor chatbot built with Python and Streamlit. This repo includes a low-code Streamlit UI, a lightweight AI client wrapper (OpenAI, Google, Dialogflow, or mock), an Indian board knowledge base, a rule-based recommender, appointment booking, sentiment analysis, and analytics logging.

**What's included**
- `app/streamlit_app.py`: Streamlit UI with Punjab advisor persona, student profile, board-aware chat, Knowledge Base, Appointments, Analytics, and Admin
- `app/api_client.py`: AI provider abstraction (OpenAI, Google, Dialogflow, or Mock)
- `app/knowledge_base.json`: Indian board policies and course metadata
- `app/recommender.py`: Simple course recommendation logic
- `app/appointments.py`: JSON-backed appointment store
- `app/sentiment.py`: VADER sentiment wrapper
- `app/analytics_module.py`: Conversation logging and summary stats
- `tests/conversational_tests.py`: Smoke tests (mock mode)
- `requirements.txt`: Python dependencies
- `.streamlit/secrets.toml.sample`: sample secrets file (do NOT commit keys)
- `DEPLOY.md`: Deployment instructions for GitHub + Streamlit Cloud

## Quick start (Windows)

Open PowerShell and run these commands inside the project folder:

```powershell
cd "f:\My Project\shapers_academic_advisor"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m tests.conversational_tests
streamlit run app/streamlit_app.py
```

If the `python` command points to the Microsoft Store stub, locate your real executable (example):

```powershell
Get-Command python -All
where.exe python
py -0p
```

## Deploy to Streamlit Community Cloud

Follow `DEPLOY.md` for step-by-step instructions to push to GitHub and deploy to Streamlit Community Cloud. Add your `OPENAI_API_KEY` under the app's Secrets on Streamlit Cloud (do not commit it).

## Notes for beginners

- Never commit API keys. Use `.streamlit/secrets.toml` locally or Streamlit secrets.
- Use the `Student profile` panel in the sidebar to set your board, class, medium, and goal for better advice.
- Keep `Auto (recommended)` selected if you want the app to choose the best available provider automatically.
- The project uses file-based data storage for simplicity (`data/`); for production use a proper database.

## Want me to finish pushing this to GitHub?

I can prepare the `git` commands and (optionally) create the remote repo skeleton for you. If you want me to run tests and deploy from this machine, confirm that I can use the located Python executable at `C:\Users\PB915\AppData\Local\Programs\Python\Python311\python.exe` to create the `.venv` and install dependencies.

If you'd like me to continue, reply `yes — use located python` and I'll proceed to create the venv and run tests here.
>>>>>>> 3513b51 (chore: prepare repo for deployment and CI)
