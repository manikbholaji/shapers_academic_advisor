import os
from datetime import date
from pathlib import Path
import streamlit as st

# Streamlit runs this file from the `app/` directory, so sibling modules are
# importable directly by filename. Using local imports avoids relying on the
# repository root being present on sys.path in every environment.
from api_client import AIClient
import recommender
import appointments
import sentiment
import analytics_module
import json
import io
from typing import Optional

st.set_page_config(page_title="SHAPERS Academic Advisor", page_icon=":mortar_board:")
st.title("SHAPERS Academic Advisor for Punjab Students")
st.caption("An experienced, friendly academic guide for CBSE, ICSE, and Punjab board learners.")


def _load_secrets():
    try:
        return {
            "OPENAI_API_KEY": st.secrets.get("OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY"),
            "GOOGLE_API_KEY": st.secrets.get("GOOGLE_API_KEY", None) or os.environ.get("GOOGLE_API_KEY"),
            "DIALOGFLOW_PROJECT_ID": st.secrets.get("DIALOGFLOW_PROJECT_ID", None) or os.environ.get("DIALOGFLOW_PROJECT_ID"),
            "DIALOGFLOW_ACCESS_TOKEN": st.secrets.get("DIALOGFLOW_ACCESS_TOKEN", None) or os.environ.get("DIALOGFLOW_ACCESS_TOKEN"),
        }
    except Exception:
        return {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
            "DIALOGFLOW_PROJECT_ID": os.environ.get("DIALOGFLOW_PROJECT_ID"),
            "DIALOGFLOW_ACCESS_TOKEN": os.environ.get("DIALOGFLOW_ACCESS_TOKEN"),
        }


def _resolve_provider(choice, secrets):
    if choice == "Auto (recommended)":
        if secrets.get("OPENAI_API_KEY"):
            return "OpenAI"
        if secrets.get("GOOGLE_API_KEY"):
            return "Google"
        return "Mock"
    if choice == "Dialogflow (advanced)":
        return "Dialogflow"
    return choice


def _provider_key(provider, secrets, manual_values):
    provider_key_map = {
        "OpenAI": ("OPENAI_API_KEY", "openai_api_key"),
        "Google": ("GOOGLE_API_KEY", "google_api_key"),
        "Dialogflow": ("DIALOGFLOW_ACCESS_TOKEN", "dialogflow_access_token"),
    }
    secret_key, manual_key = provider_key_map.get(provider, (None, None))
    if secret_key and secrets.get(secret_key):
        return secrets.get(secret_key)
    if manual_key:
        return manual_values.get(manual_key)
    return None


def _setup_status(provider, secrets):
    if provider == "Mock":
        return "No API key found yet, so the app is using Mock mode."
    if provider == "OpenAI" and secrets.get("OPENAI_API_KEY"):
        return "Using your saved OpenAI key."
    if provider == "Google" and secrets.get("GOOGLE_API_KEY"):
        return "Using your saved Google key."
    if provider == "Dialogflow" and secrets.get("DIALOGFLOW_ACCESS_TOKEN"):
        return "Using your saved Dialogflow credentials."
    return "Add a key in Secrets or use the manual fields below."


def _backend_source(provider, secrets, manual_values):
    key_sources = {
        "OpenAI": ("OPENAI_API_KEY", "openai_api_key"),
        "Google": ("GOOGLE_API_KEY", "google_api_key"),
        "Dialogflow": ("DIALOGFLOW_ACCESS_TOKEN", "dialogflow_access_token"),
    }
    secret_key, manual_key = key_sources.get(provider, (None, None))
    if secret_key and secrets.get(secret_key):
        return "secret"
    if manual_key and manual_values.get(manual_key):
        return "manual"
    return "none"


def _advisor_persona():
    return (
        "You are an experienced and creative academic advisor in India, specializing in Punjab students. "
        "Give practical, supportive, board-aware guidance for CBSE, ICSE, and PSEB learners. "
        "Be clear, kind, and action-oriented. Prefer short steps, study plans, and exam-focused advice. "
        "When helpful, mention the Indian academic year (April to March), school attendance norms, "
        "subject selection after Class 10, and board-specific preparation strategies."
    )


def _student_profile_choices():
    return {
        "board": ["Auto", "CBSE", "ICSE", "PSEB", "State Board", "Other"],
        "class_level": ["Auto", "Class 1-5", "Class 6-8", "Class 9", "Class 10", "Class 11", "Class 12"],
        "medium": ["Auto", "English", "Punjabi", "Hindi"],
        "goal": ["Board exam prep", "Stream selection", "Doubt solving", "Career guidance", "Study plan", "Admission help"],
    }


def _build_student_profile():
    choices = _student_profile_choices()
    return {
        "board": st.selectbox("Board", choices["board"], index=0),
        "class_level": st.selectbox("Class", choices["class_level"], index=0),
        "medium": st.selectbox("Preferred medium", choices["medium"], index=0),
        "goal": st.selectbox("Primary goal", choices["goal"], index=0),
        "city": st.text_input("City / district (optional)", value=""),
    }


def _profile_summary(profile):
    bits = []
    for label, key in [("Board", "board"), ("Class", "class_level"), ("Medium", "medium"), ("Goal", "goal")]:
        value = profile.get(key)
        if value and value != "Auto":
            bits.append(f"{label}: {value}")
    if profile.get("city"):
        bits.append(f"Location: {profile['city']}")
    return " • ".join(bits) if bits else "No student profile selected yet."


def _starter_prompts(profile):
    board = profile.get("board")
    class_level = profile.get("class_level")
    if board == "PSEB" or profile.get("medium") == "Punjabi":
        return [
            "How should I prepare for Punjab board exams this year?",
            "Suggest a weekly study plan for Class 10 board prep.",
            "Which subjects should I focus on first for strong marks?",
        ]
    if class_level == "Class 10":
        return [
            "Help me build a Class 10 board exam revision plan.",
            "Which chapters need more focus for board prep?",
            "How can I score better in maths and science?",
        ]
    return [
        "What should I study next based on my board and class?",
        "Give me a simple 7-day study plan.",
        "How do I improve marks without burning out?",
    ]


def _build_system_message(profile, academic_year):
    summary = _profile_summary(profile)
    return (
        f"{_advisor_persona()} Current academic year: {academic_year}. "
        f"Student profile: {summary}. "
        "If the user does not specify their board or class, ask one concise follow-up before giving a detailed plan. "
        "Tailor advice to Indian school realities and the Punjab context where relevant."
    )


def _current_academic_year(today=None):
    current_date = today or date.today()
    start_year = current_date.year if current_date.month >= 4 else current_date.year - 1
    end_year = (start_year + 1) % 100
    return f"{start_year}-{end_year:02d}"


def _default_student_profile():
    return {
        "board": "Auto",
        "class_level": "Auto",
        "medium": "Auto",
        "goal": "Board exam prep",
        "city": "",
    }


def _profile_from_keys(prefix: str):
    return {
        "board": st.session_state.get(f"{prefix}_board", "Auto"),
        "class_level": st.session_state.get(f"{prefix}_class_level", "Auto"),
        "medium": st.session_state.get(f"{prefix}_medium", "Auto"),
        "goal": st.session_state.get(f"{prefix}_goal", "Board exam prep"),
        "city": st.session_state.get(f"{prefix}_city", ""),
    }


def _assistant_message_entries(messages):
    entries = []
    assistant_number = 0
    for idx, message in enumerate(messages[1:], start=1):
        if message.get("role") == "assistant":
            assistant_number += 1
            content = (message.get("content") or "").strip()
            snippet = content[:72] + ("..." if len(content) > 72 else "")
            entries.append(
                {
                    "index": idx,
                    "label": f"AI response {assistant_number}: {snippet or 'empty response'}",
                    "content": content,
                }
            )
    return entries


def _latest_assistant_response(messages):
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return ""


def generate_png_bytes(text: str, width: int = 1200, padding: int = 20) -> Optional[bytes]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    lines = text.splitlines() or [text]
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    # estimate height
    line_h = 20
    height = padding * 2 + line_h * (len(lines) + 2)
    img = Image.new('RGB', (width, max(height, 200)), color='white')
    draw = ImageDraw.Draw(img)
    y = padding
    for line in lines:
        draw.text((padding, y), line, fill='black', font=font)
        y += line_h
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    return bio.getvalue()


def generate_pdf_bytes(text: str) -> Optional[bytes]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return None
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    y = height - 50
    lines = text.splitlines()
    for line in lines:
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(40, y, line)
        y -= 14
    c.save()
    bio.seek(0)
    return bio.read()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": _advisor_persona()}
    ]

if "student_profile_saved" not in st.session_state:
    st.session_state.student_profile_saved = _default_student_profile()

if "student_profile_draft" not in st.session_state:
    st.session_state.student_profile_draft = dict(st.session_state.student_profile_saved)

for field, default in {
    "board": st.session_state.student_profile_draft.get("board", "Auto"),
    "class_level": st.session_state.student_profile_draft.get("class_level", "Auto"),
    "medium": st.session_state.student_profile_draft.get("medium", "Auto"),
    "goal": st.session_state.student_profile_draft.get("goal", "Board exam prep"),
    "city": st.session_state.student_profile_draft.get("city", ""),
}.items():
    st.session_state.setdefault(f"profile_draft_{field}", default)

if "chat_reset_requested" not in st.session_state:
    st.session_state.chat_reset_requested = False

PROJECT_PAGES = ["Chat", "Demo", "Knowledge Base", "Book Appointment", "Analytics", "Admin"]

with st.sidebar:
    st.header("Project Tasks")
    st.caption("Go to")
    page = st.radio("", PROJECT_PAGES, label_visibility="collapsed")
    st.caption("Chat · Knowledge Base · Book Appointment · Analytics · Admin")
    st.markdown("---")
    st.header("Quick setup")
    secrets = _load_secrets()
    provider_choice = st.selectbox(
        "AI provider",
        ["Auto (recommended)", "OpenAI", "Google", "Mock", "Dialogflow (advanced)"],
        help="Auto uses saved keys when available and falls back to Mock mode.",
    )
    provider = _resolve_provider(provider_choice, secrets)
    st.caption(_setup_status(provider, secrets))

    st.markdown("---")
    st.header("Student profile")
    with st.form("student_profile_form", clear_on_submit=False):
        st.selectbox("Board", _student_profile_choices()["board"], index=_student_profile_choices()["board"].index(st.session_state.get("profile_draft_board", "Auto")), key="profile_draft_board")
        st.selectbox("Class", _student_profile_choices()["class_level"], index=_student_profile_choices()["class_level"].index(st.session_state.get("profile_draft_class_level", "Auto")), key="profile_draft_class_level")
        st.selectbox("Preferred medium", _student_profile_choices()["medium"], index=_student_profile_choices()["medium"].index(st.session_state.get("profile_draft_medium", "Auto")), key="profile_draft_medium")
        st.selectbox("Primary goal", _student_profile_choices()["goal"], index=_student_profile_choices()["goal"].index(st.session_state.get("profile_draft_goal", "Board exam prep")), key="profile_draft_goal")
        st.text_input("City / district (optional)", value=st.session_state.get("profile_draft_city", ""), key="profile_draft_city")
        save_profile = st.form_submit_button("Save profile")

    st.session_state.student_profile_draft = _profile_from_keys("profile_draft")
    if save_profile:
        st.session_state.student_profile_saved = dict(st.session_state.student_profile_draft)
        st.success("Student profile saved. Chat responses will now use this profile.")
        st.rerun()

    st.caption("Saved profile")
    st.caption(_profile_summary(st.session_state.student_profile_saved))
    if st.session_state.student_profile_draft != st.session_state.student_profile_saved:
        st.warning("You have unsaved profile changes. Click Save profile to apply them to the chatbot.")

    manual_values = {
        "openai_api_key": None,
        "google_api_key": None,
        "dialogflow_project_id": None,
        "dialogflow_access_token": None,
    }

    with st.expander("Advanced settings", expanded=False):
        model = st.text_input("Custom model name (optional)", value="")
        st.caption("Leave this blank to use a sensible default for the selected provider.")

        if provider == "OpenAI" and not secrets.get("OPENAI_API_KEY"):
            manual_values["openai_api_key"] = st.text_input("OpenAI API key", type="password")
        elif provider == "Google" and not secrets.get("GOOGLE_API_KEY"):
            manual_values["google_api_key"] = st.text_input("Google API key", type="password")
        elif provider == "Dialogflow":
            if not secrets.get("DIALOGFLOW_PROJECT_ID"):
                manual_values["dialogflow_project_id"] = st.text_input("Dialogflow project id", value="")
            if not secrets.get("DIALOGFLOW_ACCESS_TOKEN"):
                manual_values["dialogflow_access_token"] = st.text_input("Dialogflow access token", type="password")

    key_to_use = _provider_key(provider, secrets, manual_values)
    client = AIClient(provider=provider, api_key=key_to_use, model=model)
    backend_source = _backend_source(provider, secrets, manual_values)

    if backend_source == "none" or provider == "Mock":
        st.sidebar.warning("Active backend: Mock (no API key configured)")
    elif backend_source == "secret":
        st.sidebar.success(f"Active backend: {provider} using Streamlit secret")
    else:
        st.sidebar.info(f"Active backend: {provider} using manual key")

    if provider != "Mock":
        st.sidebar.caption(_setup_status(provider, secrets))

    if provider == "Dialogflow":
        dialogflow_project_id = secrets.get("DIALOGFLOW_PROJECT_ID") or manual_values.get("dialogflow_project_id")
        dialogflow_access_token = secrets.get("DIALOGFLOW_ACCESS_TOKEN") or manual_values.get("dialogflow_access_token")
        if dialogflow_project_id:
            st.session_state.setdefault("dialogflow_project_id", dialogflow_project_id)
            os.environ["DIALOGFLOW_PROJECT_ID"] = dialogflow_project_id
        if dialogflow_access_token:
            os.environ["DIALOGFLOW_ACCESS_TOKEN"] = dialogflow_access_token

saved_student_profile = dict(st.session_state.student_profile_saved)

if page == "Chat":
    academic_year = _current_academic_year()
    st.write("A Punjab-aware chatbot for school guidance, board exam planning, and career direction.")
    if provider == "Mock":
        st.info("You can start chatting now. Add a key later to switch from Mock mode.")
    st.success(f"Active academic year: {academic_year}")
    st.caption(f"Active saved profile: {_profile_summary(saved_student_profile)}")

    chat_top_left, chat_top_right = st.columns([1, 2])
    with chat_top_left:
        if st.button("Reset conversation", type="secondary"):
            st.session_state.messages = [{"role": "system", "content": _advisor_persona()}]
            st.session_state.chat_reset_requested = True
            st.success("Conversation cleared.")
            st.rerun()
    with chat_top_right:
        st.caption("Edit previous AI responses below and download the latest one as PNG or PDF.")

    with st.expander("Quick starter questions", expanded=True):
        cols = st.columns(3)
        prompts = _starter_prompts(saved_student_profile)
        for idx, prompt in enumerate(prompts):
            with cols[idx % 3]:
                if st.button(prompt, key=f"starter_{idx}"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.spinner("Thinking..."):
                        reply = client.send_message([
                            {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)},
                            *st.session_state.messages[1:],
                        ])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    s = sentiment.analyze_sentiment(prompt)
                    analytics_module.log_interaction(user="anonymous", role="user", message=prompt, sentiment_label=s["label"], compound=s["compound"])
                    analytics_module.log_interaction(user="anonymous", role="assistant", message=reply, sentiment_label="", compound=0.0)
                    st.rerun()

    if user_input := st.chat_input("Ask the advisor..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            reply = client.send_message([
                {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)},
                *st.session_state.messages[1:],
            ])
        st.session_state.messages.append({"role": "assistant", "content": reply})
        # sentiment and logging
        s = sentiment.analyze_sentiment(user_input)
        analytics_module.log_interaction(user="anonymous", role="user", message=user_input, sentiment_label=s["label"], compound=s["compound"])
        analytics_module.log_interaction(user="anonymous", role="assistant", message=reply, sentiment_label="", compound=0.0)

    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            st.chat_message("assistant").write(msg["content"])

    assistant_entries = _assistant_message_entries(st.session_state.messages)
    if assistant_entries:
        st.markdown("---")
        st.subheader("Edit previous AI response")
        chosen_entry = st.selectbox("Choose a response to edit", assistant_entries, format_func=lambda item: item["label"], key="chosen_ai_entry")
        edited_response = st.text_area("Edit AI response", value=chosen_entry["content"], height=220, key=f"edit_ai_response_{chosen_entry['index']}")
        edit_save_col, edit_download_col = st.columns([1, 1])
        with edit_save_col:
            if st.button("Save edited response", key="save_edited_response"):
                st.session_state.messages[chosen_entry["index"]]["content"] = edited_response.strip()
                st.success("AI response updated.")
                st.rerun()
        latest_ai_response = _latest_assistant_response(st.session_state.messages)
        with edit_download_col:
            st.caption("Download the latest AI response")
            if latest_ai_response:
                latest_png = generate_png_bytes(latest_ai_response)
                latest_pdf = generate_pdf_bytes(latest_ai_response)
                if latest_png:
                    st.download_button("Download latest AI response PNG", data=latest_png, file_name="ai_response.png", mime="image/png")
                if latest_pdf:
                    st.download_button("Download latest AI response PDF", data=latest_pdf, file_name="ai_response.pdf", mime="application/pdf")

    st.markdown("---")
    st.markdown("**Tip:** Keep your board and class updated for sharper advice.")

elif page == "Knowledge Base":
    academic_year = _current_academic_year()
    st.header(f"Knowledge Base & Policies ({academic_year})")
    st.caption(f"Automatically aligned to the current academic year: {academic_year}.")
    kb = json.load(open("app/knowledge_base.json", "r", encoding="utf-8"))
    kb["academic_year"] = academic_year
    if kb.get("boards"):
        st.subheader("Indian Education Boards")
        for board in kb.get("boards", []):
            with st.expander(f"{board.get('name')} — {board.get('type')}", expanded=False):
                st.write(board.get("overview"))
                st.write("**Classes:**", ", ".join(board.get("classes", [])))
                st.write("**Focus areas:**", ", ".join(board.get("core_focus", [])))
                st.write("**Common streams:**", ", ".join(board.get("common_streams", [])))
    # Punjab district-specific resources
    punjab_resources = kb.get("punjab_resources", [])
    if punjab_resources and (saved_student_profile.get("board") in ("PSEB", "pseb", "Punjab") or True):
        st.subheader("Punjab District Resources")
        for res in punjab_resources:
            with st.expander(res.get("district"), expanded=False):
                st.write(res.get("tips"))
    st.subheader("Policies")
    for p in kb.get("policies", []):
        st.write(f"**{p.get('title')}** — {p.get('summary')}")
        if st.checkbox(f"Show details: {p.get('title')}"):
            st.write(p.get("details"))
    st.subheader("Courses")
    for c in kb.get("courses", []):
        st.write(f"**{c.get('code')} - {c.get('name')}**")
        st.write(c.get("description"))

elif page == "Demo":
    st.header("Demo: Sample Prompts & Expected Answers")
    st.caption("Quick examples to try — tailored for Punjab students (PSEB/Punjab, CBSE, ICSE). Use the 'Use in Chat' button to run the prompt in the Chat page.")

    academic_year = _current_academic_year()

    demo_cases = [
        {
            "title": "Weekly study plan — Class 10 (Punjab board)",
            "prompt": "Suggest a weekly study plan for Class 10 Punjab board exams, focusing on Maths and Science, including daily tasks and revision slots.",
            "expected": "A 7-day schedule splitting topics by chapter, daily practice problems, 30-40 minute revision at day end, weekly test on Sunday, and tips to balance Punjabi/English medium study."
        },
        {
            "title": "Improve marks in Mathematics",
            "prompt": "I get low marks in maths in tests. What are 5 practical steps I can take this month to improve for Class 10 boards?",
            "expected": "Focus on NCERT problems, practice previous year board questions, maintain formula sheet, time-bound mock tests, and targeted revision of weak chapters."
        },
        {
            "title": "Stream selection after Class 10",
            "prompt": "I like biology and computers but my marks are mixed. Which stream should I pick after Class 10 in Punjab to keep options open?",
            "expected": "Explain Science (Medical/Non-medical), Commerce with Computer Applications, tradeoffs, and suggest short-term bridge courses and subject choices in PSEB."
        },
        {
            "title": "College admission guidance — Punjab",
            "prompt": "Which local colleges in Punjab offer good BSc Computer Science and what are the typical cutoffs and application timelines?",
            "expected": "List a few well-known colleges (e.g., PU-affiliated colleges, GNDU departments), general cutoff ranges, application portals and typical timelines (June–Aug admissions)."
        },
        {
            "title": "Scholarships & exam registrations",
            "prompt": "Tell me about common scholarships for Class 11 students in Punjab and upcoming important exam registration dates.",
            "expected": "Summarize state scholarship schemes, eligibility basics, and common registration windows for board exams and competitive exams; recommend official sites for verification."
        },
    ]

    cols = st.columns(1)
    lang = st.selectbox("Language / ਭਾਸ਼ਾ / भाषा", ["English", "हिन्दी", "Hinglish", "ਪੰਜਾਬੀ"], index=0)
    asset_map = {
        "English": "cheatsheet_en.md",
        "हिन्दी": "cheatsheet_hi.md",
        "Hinglish": "cheatsheet_hinglish.md",
        "ਪੰਜਾਬੀ": "cheatsheet_pa.md",
    }
    asset_path = Path(__file__).resolve().parent / "demo_assets" / asset_map.get(lang, "cheatsheet_en.md")
    try:
        with open(asset_path, 'r', encoding='utf-8') as f:
            cheatsheet_text = f.read()
    except Exception:
        cheatsheet_text = ''
    st.download_button(label=f"Download cheat-sheet ({lang})", data=cheatsheet_text, file_name=f"shapers_cheatsheet_{lang}.md")

    png_bytes = generate_png_bytes(cheatsheet_text)
    pdf_bytes = generate_pdf_bytes(cheatsheet_text)
    if png_bytes:
        st.subheader("Preview (image)")
        st.image(png_bytes)
        st.download_button("Download PNG", data=png_bytes, file_name=f"shapers_cheatsheet_{lang}.png", mime='image/png')
    else:
        st.info("Image preview unavailable: `Pillow` not installed. The deployed app will install it from `requirements.txt`.")

    if pdf_bytes:
        st.download_button("Download PDF", data=pdf_bytes, file_name=f"shapers_cheatsheet_{lang}.pdf", mime='application/pdf')
    else:
        st.info("PDF download unavailable: `reportlab` not installed. The deployed app will install it from `requirements.txt`.")
    for idx, case in enumerate(demo_cases):
        with st.expander(f"{case['title']}", expanded=(idx == 0)):
            st.write("**Prompt:**")
            st.write(case["prompt"])
            st.write("**Expected answer (summary):**")
            st.info(case["expected"])
            row = st.columns([3,1])
            with row[0]:
                if st.button("Use in Chat", key=f"use_chat_{idx}"):
                    # push to messages and run a single assistant reply
                    st.session_state.messages.append({"role": "user", "content": case["prompt"]})
                    with st.spinner("Querying advisor..."):
                        reply = client.send_message([
                            {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)},
                            *st.session_state.messages[1:],
                        ])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.success("Prompt sent to Chat. Switch to the Chat page to view the full conversation.")
            with row[1]:
                if st.button("Copy prompt", key=f"copy_{idx}"):
                    st.write("Prompt copied to clipboard (use your browser feature).")
    st.markdown("---")
    st.write("Tip: Update your profile (Board, Class, City) in the sidebar — this helps the advisor tailor responses specifically for Punjab and your board.")

elif page == "Book Appointment":
    st.header("Book an Appointment with an Advisor")
    name = st.text_input("Student name")
    email = st.text_input("Email")
    when = st.text_input("When (ISO datetime or simple text)")
    notes = st.text_area("Notes (optional)", value=f"Board: {saved_student_profile.get('board', 'Auto')} | Class: {saved_student_profile.get('class_level', 'Auto')} | Goal: {saved_student_profile.get('goal', 'Board exam prep')}")
    if st.button("Book"):
        if not name or not email or not when:
            st.error("Please fill in your name, email, and preferred time.")
        else:
            appt = appointments.book_appointment(name, email, when, notes=notes)
            st.success(f"Booked appointment id {appt.get('id')} for {appt.get('when')}")
            st.caption("Your board/class context has been added to the notes for better follow-up.")

elif page == "Analytics":
    st.header("Interaction Analytics")
    try:
        df = analytics_module.load_interactions()
        st.write("Total interactions:", len(df))
        st.dataframe(df.tail(50))
        stats = analytics_module.simple_stats(df)
        st.write(stats)
        st.info("Use this dashboard to watch which topics need clearer Punjab-focused guidance.")
    except Exception as e:
        st.error("No interaction data yet or failed to load: " + str(e))

elif page == "Admin":
    st.header("Admin Tools")
    st.subheader("Course Recommendations (demo)")
    interests = st.text_input("Interests (comma separated)", value="math, science, Punjabi, programming")
    completed = st.text_input("Completed courses (comma separated)")
    goals = st.text_input("Goals (short text)", value=saved_student_profile.get("goal", "Board exam prep"))
    st.caption(_profile_summary(saved_student_profile))
    if st.button("Recommend Courses"):
        profile = {
            "interests": [i.strip() for i in interests.split(",") if i.strip()],
            "completed": [c.strip() for c in completed.split(",") if c.strip()],
            "goals": goals,
        }
        recs = recommender.recommend_courses(profile)
        for r in recs:
            st.write(f"**{r.get('code')} - {r.get('name')}**: {r.get('description')}")

