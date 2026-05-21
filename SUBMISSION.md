# Submission Notes — SHAPERS Academic Advisor

This document summarizes the project artifacts and how to run the demo for college evaluation.

## Project summary
- A Streamlit-based student academic advisor tailored to Indian boards (CBSE, ICSE, State Boards).
- Provider-agnostic AI integration via `app/api_client.py` supporting OpenAI, Google Gemini, Dialogflow, and a Mock fallback.
- AI-backed pathway generation: `app/recommender.py` now supports API-driven generation of end-to-end pathways including Class 11/12, diploma, UG/PG, institutions, fees, and salary outlook.
- Unit tests and Playwright UI tests included and passing in the repository.

## Evaluation checklist (what to verify)
- Code compiles and tests run locally.
  - `python -m pytest -q` — expected: all tests pass (14 passed, 2 skipped in our run).
- Demo of live chatbot interaction.
  - `python scripts/demo_chat.py` — sends a demo query and saves the assistant reply to `demos/sample_chat_output.txt`.
- Admin pathway builder demonstration.
  - Use the live deployed app or run locally via Streamlit and navigate to the Admin tab to generate full pathways.

## How to run locally (recommended)
1. Create and activate a virtual environment.

```powershell
cd "f:\My Project\shapers_academic_advisor"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Run unit tests and UI tests (optional but recommended):

```powershell
python -m pytest -q
# Playwright tests require browsers installed; install with:
# playwright install
python -m pytest tests/test_ui_admin_pathway_builder.py -q
```

3. Run the demo chat (mock will be used if no API key set):

```powershell
python scripts/demo_chat.py
# Output saved to demos/sample_chat_output.txt
```

4. Run the app locally:

```powershell
streamlit run app/streamlit_app.py
```

## Files included for submission
- `app/` — source application
- `tests/` — pytest unit and Playwright UI tests
- `scripts/demo_chat.py` — demo chat harness
- `SUBMISSION.md` — this file (submission notes)
- `README.md` — project README with setup and deployment notes

## Notes for evaluators
- The AI integration uses environment secrets for real API access. If no secret is configured, the app uses a deterministic mock reply so the UI remains functional for evaluation.
- For best AI results, provide an `OPENAI_API_KEY` or `GOOGLE_API_KEY` in the environment or Streamlit Secrets.

## Sentiment workflow (implementation notes)

- The app uses VADER via `app/sentiment.py` with a standardized function `analyze_sentiment(text) -> {"label","compound"}`.
- New interactions get sentiment automatically when written with `analytics_module.log_interaction(...)` (no extra flags required).
- Administrators can re-run sentiment across all stored logs from the Analytics page using the "🔁 Recompute sentiment for all logs" button; alternatively, call `analytics_module.reprocess_sentiments(file_path=None, sentiment_fn=None)` to reprocess programmatically or with a custom sentiment function.
- Unit tests covering sentiment and reprocessing are provided in `tests/test_sentiment.py` and `tests/test_analytics_reprocess.py`.



Good luck with the evaluation — contact the project author if you need a short walkthrough video or a live demo session.
