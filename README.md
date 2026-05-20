# SHAPERS Academic Advisor

SHAPERS Academic Advisor is a Streamlit app for Punjab students that provides board-aware guidance, study planning, course suggestions, appointment booking, and downloadable AI-generated study cheat-sheets.

## Highlights

- Punjab-focused academic advisor experience for CBSE, ICSE, PSEB, and State Board students.
- Provider-agnostic AI backend with OpenAI, Google Gemini, Dialogflow, and offline Mock mode.
- Saved student profile workflow with a required **Save profile** action before advice updates.
- Chat tools to edit previous AI responses, reset the conversation, and download replies as PNG or PDF.
- Demo page with multilingual sample prompts and downloadable cheat-sheets in English, Hindi, Hinglish, and Punjabi.
- Knowledge Base, appointment booking, analytics, and admin utilities.

## Live deployment

The app is deployed on Streamlit Community Cloud:

- https://academicadvisor.streamlit.app/

## Important note about API mode

If the app shows **Mock mode** or **No API key configured**, it means the deployed Streamlit app does not currently have a valid secret configured.

To enable real API usage in Streamlit Community Cloud:

1. Open the deployed app in Streamlit Community Cloud.
2. Go to **Manage app** → **Settings** → **Secrets**.
3. Add one of the following:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
   - `DIALOGFLOW_PROJECT_ID`
   - `DIALOGFLOW_ACCESS_TOKEN`

If no secret is set, the app intentionally falls back to Mock mode so the UI still works.

   ### Secret reference

   | Secret | Purpose |
   | --- | --- |
   | `OPENAI_API_KEY` | Enables OpenAI-backed responses |
   | `GOOGLE_API_KEY` | Enables Google Gemini-backed responses |
   | `DIALOGFLOW_PROJECT_ID` | Required for Dialogflow runtime calls |
   | `DIALOGFLOW_ACCESS_TOKEN` | Required for Dialogflow runtime calls |

   If multiple secrets are present, the app follows the selected provider in the sidebar. When **Auto (recommended)** is selected, it prefers OpenAI, then Google, then Mock mode.

## Local setup

```powershell
cd "f:\My Project\shapers_academic_advisor"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## What to use in the app

### Student profile

- Choose your board, class, medium, goal, and city/district.
- Click **Save profile** to make the profile active for chatbot responses.

### Chat tools

- **Reset conversation** clears the current chat and starts fresh.
- **Edit previous AI response** lets you revise a previous assistant reply.
- **Download latest AI response** exports the latest answer as PNG or PDF.

### Demo page

- Shows multilingual sample prompts.
- Provides markdown cheat-sheets and downloadable PNG/PDF versions.

## Project structure

- `app/streamlit_app.py` - Streamlit UI
- `app/api_client.py` - OpenAI / Google / Dialogflow / Mock abstraction
- `app/knowledge_base.json` - board and policy data
- `app/recommender.py` - course recommendation helper
- `app/appointments.py` - appointment storage
- `app/sentiment.py` - sentiment analysis
- `app/analytics_module.py` - logging and summary stats
- `scripts/run_health_checks.py` - scheduled provider checks
- `scripts/generate_cheatsheets.py` - optional PNG generation helper

## Testing

```powershell
cd "f:\My Project\shapers_academic_advisor"
python -m pytest -q
```

## Deployment on Streamlit Community Cloud

1. Connect the GitHub repository to Streamlit Community Cloud.
2. Set the app entry point to `app/streamlit_app.py`.
3. Add the required secrets in the Streamlit UI.
4. Redeploy and verify the sidebar backend banner.

## Health checks and notifications

- `.github/workflows/ci.yml` runs tests and scheduled provider health checks.
- If a scheduled health check fails, the workflow creates a GitHub issue.

## Credits

Built for student-friendly academic advising, with a focus on Punjab, India.
