# Architecture & API Flow

This document explains the core components of the SHAPERS Academic Advisor app and how they interact.

Components:

- Streamlit App (`app/streamlit_app.py`): UI layer with a Punjab-focused advisor persona, student profile panel, board-aware Chat, Knowledge Base, Appointments, Analytics, and Admin.
- AI Client (`app/api_client.py`): abstracts provider calls (OpenAI, Google, Dialogflow, or Mock) and returns assistant responses.
- Knowledge Base (`app/knowledge_base.json`): Indian board JSON store for academic policies and course metadata.
- Recommender (`app/recommender.py`): rule-based recommendation engine using student profile and KB.
- Appointments (`app/appointments.py`): simple JSON-backed booking store for advisor appointments.
- Sentiment (`app/sentiment.py`): VADER-based sentiment analysis for user feedback and logs.
- Analytics (`app/analytics_module.py`): logs conversations and provides summary stats via pandas.
- Tests (`tests/conversational_tests.py`): simple smoke tests for conversational replies.

API Flow (high-level):

1. User sets a student profile (board, class, medium, goal) in the sidebar.
2. User submits a question in the Streamlit chat UI.
3. Streamlit adds the user message, builds a Punjab-aware system prompt, and calls `AIClient.send_message()`.
4. The response is returned and displayed; both user message and assistant reply are logged by `analytics_module.log_interaction()`.
5. `sentiment.analyze_sentiment()` can run on the user's message for dashboards and monitoring.
6. For course recommendations, the app calls `recommender.recommend_courses()` with the student's profile.
7. For bookings, `appointments.book_appointment()` creates an entry in `data/appointments.json`.

Security & Deployment:

- Do not commit secrets. Use `.streamlit/secrets.toml` locally and Streamlit Community Cloud secrets for deployment.
- For production-grade deployments use authenticated APIs, HTTPS endpoints for booking integrations, and a persistent database.

