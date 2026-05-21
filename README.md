# SHAPERS Academic Advisor

SHAPERS Academic Advisor is a Streamlit app for Indian students that provides board-aware guidance, Class 11/12 stream selection help, diploma/undergraduate/postgraduate program recommendations, appointment booking, and downloadable AI-generated study cheat-sheets.

## Highlights

- India-wide academic advisor experience for CBSE, ICSE, State Board, and stream-selection support.
- Provider-agnostic AI backend with OpenAI, Google Gemini, Dialogflow, and offline Mock mode.
- Saved student profile workflow with a required **Save profile** action before advice updates.
- Gemini-style prompt composer that lets you choose the output format before submission: Text, PNG, or PDF.
- Prompt history editor so you can revise a previous prompt and resubmit it without creating a new conversation.
- Demo page with multilingual sample prompts and downloadable cheat-sheets in English, Hindi, Hinglish, and Regional.
- Knowledge Base, appointment booking with peak-hour time slots, analytics, and admin utilities.

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

- Choose a response format before sending a prompt: **Text**, **PNG**, or **PDF**.
- Use the prompt history editor to revise an earlier prompt and resubmit it in place.
- **Reset conversation** clears the current chat and starts fresh.

### Stream guidance

- The admin panel includes a stream recommender for Class 11 and Class 12.
- It helps compare **Humanities**, **Commerce**, **Medical**, and **Non-medical** based on interests, strengths, and marks.

### Program pathways

- The admin panel also recommends **Diploma**, **Undergraduate**, and **Postgraduate** pathways in India.
- Each recommendation includes example universities and colleges plus a note to verify the current admission cycle.

### Demo page

- Shows multilingual sample prompts.
- Provides markdown cheat-sheets and downloadable PNG/PDF versions.
- The regional language option stays generic in the UI while still loading the regional demo asset.

### Appointment booking

- The appointment form uses a date picker plus working-hour slots.
- Available times stay within peak hours so bookings remain structured and easy to follow up.

### A4 exports

- PNG and PDF exports are formatted for readability with larger type and cleaner page layout.
- PDF output is laid out on A4 paper with footers and consistent spacing.

## Project structure

- `app/streamlit_app.py` - Streamlit UI
- `app/api_client.py` - OpenAI / Google / Dialogflow / Mock abstraction
- `app/knowledge_base.json` - board, policy, and regional guidance data
- `app/recommender.py` - course and pathway recommendation helper
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
5. Confirm the composer shows the selected response type and that the saved student profile is active after clicking **Save profile**.
6. Check that Class 11/12 stream guidance, appointment slots, and A4 export previews render correctly.

## Health checks and notifications

- `.github/workflows/ci.yml` runs tests and scheduled provider health checks.
- If a scheduled health check fails, the workflow creates a GitHub issue.

## Credits

Built for student-friendly academic advising across India.
