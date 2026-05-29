# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]
- **AI Flow Migration**: Transformed app into a full SHAPERS Academic Advisor with multi-turn conversation support and integrated pathway/career guidance.
- **Streaming UI**: Added real-time response streaming for OpenAI and Google Gemini providers for a superior UX.
- **Workflow Optimization**: Consolidated GitHub Actions, fixed cross-platform script issues, and added automated provider health checks with issue reporting.
- **UI Refinement**: Modernized navigation and replaced deprecated Streamlit calls for better stability.
- Harden Interaction Trends with mixed-format timestamp parsing, daily interaction totals, and average sentiment trend charts.
- Harden pathway recommendations by merging AI output into canonical KB pathways so Admin always gets complete class 11/12 and city-specific details.
- Fix Streamlit deployment imports by using absolute `app.*` imports and adding a startup path guard in `app/streamlit_app.py`.
- Improve sentiment reprocess UX with progress bar/status text and stronger Admin/Analytics status indicators.
- Add automatic sentiment analysis when logging interactions (`analytics_module.log_interaction`).
- Add `analytics_module.reprocess_sentiments()` and `get_reprocess_meta()` for bulk reanalysis and metadata.
- Admin UI: add "🔁 Recompute sentiment for all logs" button and last-run badge in Analytics and Admin pages.
- Standardize `app.sentiment.analyze_sentiment(text)` output: `{ "label":..., "compound": ... }`.
- Add unit tests for sentiment and reprocessing (`tests/test_sentiment.py`, `tests/test_analytics_reprocess.py`).
- Docs updated: `README.md`, `SUBMISSION.md` include sentiment workflow notes.

## [v1.1.0] - 2026-05-21
- See Unreleased changes.

## [v1.0.0] - initial
- Initial baseline features: Streamlit UI, AI-backed recommender, analytics, and demo assets.
