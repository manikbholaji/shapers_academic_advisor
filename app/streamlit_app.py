import os
from datetime import date, datetime
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
st.title("SHAPERS Academic Advisor for Indian Students")
st.caption("An experienced, friendly academic guide for CBSE, ICSE, State Board, and stream-selection support.")


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
        "You are an experienced and creative academic advisor for Indian students. "
        "Give practical, supportive, board-aware guidance for CBSE, ICSE, and State Board learners. "
        "Be clear, kind, and action-oriented. Prefer short steps, study plans, and exam-focused advice. "
        "When helpful, mention the Indian academic year (April to March), school attendance norms, "
        "subject selection after Class 10, stream choice for Classes 11 and 12, and board-specific preparation strategies."
    )


def _student_profile_choices():
    return {
        "board": ["Auto", "CBSE", "ICSE", "State Board", "Other"],
        "class_level": ["Auto", "Class 1-5", "Class 6-8", "Class 9", "Class 10", "Class 11", "Class 12"],
        "medium": ["Auto", "English", "Hindi", "Bilingual", "Regional"],
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
    class_level = profile.get("class_level")
    if class_level in ("Class 11", "Class 12") or profile.get("goal") == "Stream selection":
        return [
            "Help me choose between Humanities, Commerce, Medical, and Non-medical after Class 10.",
            "What stream should I choose for Class 11 if I like biology and writing equally?",
            "Which subjects should I focus on if I want both strong marks and future flexibility?",
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
        "Tailor advice to Indian school realities and local board context where relevant."
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


def _sync_profile_draft_to_saved():
    st.session_state.student_profile_draft = _profile_from_keys("profile_draft")
    st.session_state.student_profile_saved = dict(st.session_state.student_profile_draft)


def _render_profile_form():
    choices = _student_profile_choices()
    with st.form("student_profile_form", clear_on_submit=False):
        st.selectbox("Board", choices["board"], index=choices["board"].index(st.session_state.get("profile_draft_board", "Auto")), key="profile_draft_board")
        st.selectbox("Class", choices["class_level"], index=choices["class_level"].index(st.session_state.get("profile_draft_class_level", "Auto")), key="profile_draft_class_level")
        st.selectbox("Preferred medium", choices["medium"], index=choices["medium"].index(st.session_state.get("profile_draft_medium", "Auto")), key="profile_draft_medium")
        st.selectbox("Primary goal", choices["goal"], index=choices["goal"].index(st.session_state.get("profile_draft_goal", "Board exam prep")), key="profile_draft_goal")
        st.text_input("City / district (optional)", value=st.session_state.get("profile_draft_city", ""), key="profile_draft_city")
        save_profile = st.form_submit_button("Save profile")

    st.session_state.student_profile_draft = _profile_from_keys("profile_draft")
    if save_profile:
        _sync_profile_draft_to_saved()
        st.success("Student profile saved. Chat responses will now use this profile.")
        st.rerun()

    st.caption("Saved profile")
    st.caption(_profile_summary(st.session_state.student_profile_saved))
    if st.session_state.student_profile_draft != st.session_state.student_profile_saved:
        draft_profile = st.session_state.student_profile_draft
        unsaved_bits = []
        for label, key in [
            ("Board", "board"),
            ("Class", "class_level"),
            ("Medium", "medium"),
            ("Goal", "goal"),
            ("City", "city"),
        ]:
            if draft_profile.get(key) != st.session_state.student_profile_saved.get(key):
                unsaved_bits.append(f"{label}: {draft_profile.get(key) or '—'}")
        if unsaved_bits:
            st.warning("Unsaved changes: " + " | ".join(unsaved_bits))



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


def _pair_messages(messages):
    pairs = []
    pending_user = None
    for idx, message in enumerate(messages[1:], start=1):
        role = message.get("role")
        if role == "user":
            pending_user = {"index": idx, "content": message.get("content", "")}
        elif role == "assistant" and pending_user is not None:
            pairs.append(
                {
                    "user_index": pending_user["index"],
                    "user_content": pending_user["content"],
                    "assistant_index": idx,
                    "assistant_content": message.get("content", ""),
                }
            )
            pending_user = None
    if pending_user is not None:
        pairs.append(
            {
                "user_index": pending_user["index"],
                "user_content": pending_user["content"],
                "assistant_index": None,
                "assistant_content": "",
            }
        )
    return pairs


def _generate_assistant_reply(client, saved_student_profile, academic_year, prompt_text, context_messages):
    system_message = {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)}
    return client.send_message([system_message, *context_messages, {"role": "user", "content": prompt_text}])


def _format_download_name(format_choice: str):
    safe = format_choice.lower().replace(" ", "_")
    return f"ai_response.{ 'txt' if safe == 'text' else 'png' if safe == 'png' else 'pdf' }"


def _appointment_time_slots():
    return appointments.list_working_hours(start_hour=10, end_hour=18, step_minutes=30)


def _filtered_appointment_slots(selected_date):
    slots = _appointment_time_slots()
    if selected_date != date.today():
        return slots

    available = []
    now = datetime.now()
    for slot in slots:
        slot_time = datetime.strptime(slot, "%H:%M").time()
        if datetime.combine(selected_date, slot_time) > now:
            available.append(slot)
    return available


def _reset_conversation():
    st.session_state.messages = [{"role": "system", "content": _advisor_persona()}]


def _render_prompt_history_editor(saved_student_profile, academic_year, client):
    pairs = _pair_messages(st.session_state.messages)
    if not pairs:
        return

    st.markdown("---")
    st.subheader("Edit and resubmit previous prompts")
    st.caption("Select any earlier prompt, change it, choose a response format, and regenerate it in place.")

    selectable_pairs = [pair for pair in pairs if pair.get("user_content")]
    selected_pair = st.selectbox(
        "Choose a previous prompt",
        selectable_pairs,
        format_func=lambda item: item["user_content"][:90] + ("..." if len(item["user_content"]) > 90 else ""),
        key="prompt_history_selector",
    )

    edited_prompt = st.text_area("Edit selected prompt", value=selected_pair["user_content"], height=120, key=f"edited_prompt_{selected_pair['user_index']}")
    resend_format = st.radio(
        "Resubmitted response format",
        ["Text", "PNG", "PDF"],
        horizontal=True,
        key=f"resubmit_format_{selected_pair['user_index']}",
    )

    action_left, action_right = st.columns([1, 1])
    with action_left:
        if st.button("Resubmit edited prompt", key=f"resubmit_prompt_{selected_pair['user_index']}"):
            if not edited_prompt.strip():
                st.warning("Please enter a prompt before resubmitting.")
                return

            user_index = selected_pair["user_index"]
            assistant_index = selected_pair.get("assistant_index")
            current_history = st.session_state.messages[1:user_index]

            reply = _generate_assistant_reply(client, saved_student_profile, academic_year, edited_prompt.strip(), current_history)
            st.session_state.messages[user_index]["content"] = edited_prompt.strip()
            if assistant_index is not None and assistant_index < len(st.session_state.messages):
                st.session_state.messages[assistant_index]["content"] = reply
            else:
                st.session_state.messages.append({"role": "assistant", "content": reply})

            if resend_format == "Text":
                st.session_state.latest_export_bytes = reply.encode("utf-8")
                st.session_state.latest_export_format = "text"
                st.session_state.latest_export_name = "ai_response.txt"
            elif resend_format == "PNG":
                st.session_state.latest_export_bytes = generate_png_bytes(reply)
                st.session_state.latest_export_format = "png"
                st.session_state.latest_export_name = "ai_response.png"
            else:
                st.session_state.latest_export_bytes = generate_pdf_bytes(reply)
                st.session_state.latest_export_format = "pdf"
                st.session_state.latest_export_name = "ai_response.pdf"

            st.success("Prompt updated and resubmitted.")
            st.rerun()

    with action_right:
        if st.button("Reset conversation", type="secondary", key=f"reset_from_history_{selected_pair['user_index']}"):
            _reset_conversation()
            st.session_state.latest_export_bytes = None
            st.session_state.latest_export_format = None
            st.session_state.latest_export_name = None
            st.success("Conversation cleared.")
            st.rerun()


def generate_png_bytes(text: str, width: int = 1200, padding: int = 20) -> Optional[bytes]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    from textwrap import wrap

    def _load_font(name, size, fallback_default=False):
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            return ImageFont.load_default() if fallback_default else None

    title_font = _load_font("DejaVuSans-Bold.ttf", 34, fallback_default=True)
    subtitle_font = _load_font("DejaVuSans.ttf", 18, fallback_default=True)
    body_font = _load_font("DejaVuSans.ttf", 22, fallback_default=True)

    page_width = 1240
    page_height = 1754
    margin = 72
    img = Image.new("RGB", (page_width, page_height), color="#f8fafc")
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((margin, margin, page_width - margin, margin + 150), radius=28, fill="#0f172a")
    draw.text((margin + 36, margin + 28), "SHAPERS Academic Advisor", fill="#ffffff", font=title_font)
    draw.text((margin + 36, margin + 86), "Formatted AI response", fill="#cbd5e1", font=subtitle_font)

    content_top = margin + 190
    draw.rounded_rectangle((margin, content_top, page_width - margin, page_height - margin), radius=28, fill="#ffffff", outline="#dbe3ef", width=2)

    def wrap_line(line, max_width):
        if not line.strip():
            return [""]
        words = line.split()
        wrapped = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=body_font)
            if bbox[2] - bbox[0] <= max_width or not current:
                current = candidate
            else:
                wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)
        return wrapped

    y = content_top + 36
    max_text_width = page_width - (margin * 2) - 40
    for raw_line in (text or "").splitlines() or [text or ""]:
        if not raw_line.strip():
            y += 14
            continue
        bullet_prefix = ""
        content = raw_line.strip()
        if content.startswith(("- ", "* ", "• ")):
            bullet_prefix = "• "
            content = content[2:].strip() if content[:2] in ("- ", "* ") else content[1:].strip()

        available_width = max_text_width - (30 if bullet_prefix else 0)
        wrapped_lines = wrap_line(content, available_width)
        for line_index, wrapped_line in enumerate(wrapped_lines):
            x = margin + 32 if bullet_prefix and line_index == 0 else margin + 62 if bullet_prefix else margin + 32
            prefix = bullet_prefix if line_index == 0 else ""
            draw.text((x, y), f"{prefix}{wrapped_line}", fill="#0f172a", font=body_font)
            line_bbox = draw.textbbox((0, 0), wrapped_line or "Ag", font=body_font)
            y += (line_bbox[3] - line_bbox[1]) + 12
        y += 6
        if y > page_height - margin - 60:
            break

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def generate_pdf_bytes(text: str) -> Optional[bytes]:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from xml.sax.saxutils import escape
    except Exception:
        return None

    bio = io.BytesIO()

    doc = SimpleDocTemplate(
        bio,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="SHAPERS Academic Advisor Response",
        author="SHAPERS Academic Advisor",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ExportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "ExportSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "ExportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceAfter=5,
        alignment=TA_LEFT,
    )

    story = [
        Paragraph("SHAPERS Academic Advisor", title_style),
        Paragraph("Formatted response for reading, sharing, and printing on A4 paper.", subtitle_style),
    ]

    for line in (text or "").splitlines() or [text or ""]:
        clean_line = escape(line.strip())
        if not clean_line:
            story.append(Spacer(1, 4))
            continue
        if clean_line.startswith(("- ", "* ", "• ")):
            clean_line = f"• {clean_line[2:].strip()}" if clean_line[:2] in ("- ", "* ") else clean_line
        story.append(Paragraph(clean_line.replace("\n", "<br/>").replace("  ", " &nbsp;"), body_style))

    def _add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.line(doc_obj.leftMargin, 16 * mm, A4[0] - doc_obj.rightMargin, 16 * mm)
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(doc_obj.leftMargin, 11 * mm, "SHAPERS Academic Advisor")
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, 11 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
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

if "latest_export_bytes" not in st.session_state:
    st.session_state.latest_export_bytes = None

if "latest_export_format" not in st.session_state:
    st.session_state.latest_export_format = None

if "latest_export_name" not in st.session_state:
    st.session_state.latest_export_name = None

for field, default in {
    "board": st.session_state.student_profile_draft.get("board", "Auto"),
    "class_level": st.session_state.student_profile_draft.get("class_level", "Auto"),
    "medium": st.session_state.student_profile_draft.get("medium", "Auto"),
    "goal": st.session_state.student_profile_draft.get("goal", "Board exam prep"),
    "city": st.session_state.student_profile_draft.get("city", ""),
}.items():
        st.session_state.setdefault(f"profile_draft_{field}", default)

PROJECT_PAGES = ["Chat", "Demo", "Knowledge Base", "Book Appointment", "Analytics", "Admin"]

with st.sidebar:
    st.header("Navigation")
    st.caption("Go to")
    page = st.radio("", PROJECT_PAGES, label_visibility="collapsed")
    st.caption("Chat · Knowledge Base · Book Appointment · Analytics · Admin")
    st.markdown("---")
    st.header("AI settings")
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
    _render_profile_form()

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
    st.write("An India-wide academic chatbot for school guidance, board exam planning, stream selection, and career direction.")
    if provider == "Mock":
        st.info("You can start chatting now. Add a key later to switch from Mock mode.")
    st.success(f"Active academic year: {academic_year}")
    st.caption(f"Active saved profile: {_profile_summary(saved_student_profile)}")

    st.caption("Choose the answer format first, then send one focused prompt.")

    with st.form("prompt_composer_form", clear_on_submit=True):
        st.subheader("Compose your question")
        prompt_text = st.text_area("Ask anything", placeholder="Ask for study plans, stream guidance, admission help, exam tips, and more...", height=120)
        response_format = st.radio(
            "Reply format",
            ["Text", "PNG", "PDF"],
            horizontal=True,
            help="Choose Text for a chat reply, PNG for an image-style response, or PDF for a document-style response.",
        )
        composer_col_left, composer_col_right = st.columns([1, 1])
        with composer_col_left:
            send_prompt = st.form_submit_button("Generate reply")
        with composer_col_right:
            st.caption("You can revise and resubmit earlier prompts below.")

    if send_prompt and prompt_text.strip():
        st.session_state.messages.append({"role": "user", "content": prompt_text.strip()})
        with st.spinner("Generating response..."):
            reply = _generate_assistant_reply(client, saved_student_profile, academic_year, prompt_text.strip(), st.session_state.messages[1:-1])
        if response_format == "Text":
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.latest_export_bytes = None
            st.session_state.latest_export_format = "text"
            st.session_state.latest_export_name = "ai_response.txt"
        elif response_format == "PNG":
            png_bytes = generate_png_bytes(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.latest_export_bytes = png_bytes
            st.session_state.latest_export_format = "png"
            st.session_state.latest_export_name = _format_download_name("PNG")
        else:
            pdf_bytes = generate_pdf_bytes(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.latest_export_bytes = pdf_bytes
            st.session_state.latest_export_format = "pdf"
            st.session_state.latest_export_name = _format_download_name("PDF")

        s = sentiment.analyze_sentiment(prompt_text.strip())
        analytics_module.log_interaction(user="anonymous", role="user", message=prompt_text.strip(), sentiment_label=s["label"], compound=s["compound"])
        analytics_module.log_interaction(user="anonymous", role="assistant", message=reply, sentiment_label="", compound=0.0)
        st.rerun()

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

    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            st.chat_message("assistant").write(msg["content"])

    if getattr(st.session_state, "latest_export_bytes", None):
        st.markdown("---")
        st.subheader("Latest generated file")
        export_name = st.session_state.get("latest_export_name", "ai_response.txt")
        export_format = st.session_state.get("latest_export_format", "text")
        if export_format == "png":
            st.image(st.session_state.latest_export_bytes)
            st.download_button("Download PNG", data=st.session_state.latest_export_bytes, file_name=export_name, mime="image/png")
        elif export_format == "pdf":
            st.download_button("Download PDF", data=st.session_state.latest_export_bytes, file_name=export_name, mime="application/pdf")
        else:
            st.download_button("Download text", data=st.session_state.latest_export_bytes, file_name=export_name, mime="text/plain")

    _render_prompt_history_editor(saved_student_profile, academic_year, client)

    st.markdown("---")
    st.markdown("**Tip:** Keep your board, class, and goal updated for sharper advice.")

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
    regional_resources = kb.get("regional_resources", [])
    if regional_resources:
        st.subheader("Regional study tips")
        for res in regional_resources:
            with st.expander(res.get("label", "Study tip"), expanded=False):
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
    st.caption("Quick examples to try — tailored for Indian students across CBSE, ICSE, and State Boards. Use the button in each card to open the prompt in Chat.")

    academic_year = _current_academic_year()

    demo_cases = [
        {
            "title": "Weekly study plan — Class 10",
            "prompt": "Suggest a weekly study plan for Class 10 board exams, focusing on Maths and Science, including daily tasks and revision slots.",
            "expected": "A 7-day schedule splitting topics by chapter, daily practice problems, 30-40 minute revision at day end, weekly test on Sunday, and tips to balance school work with revision."
        },
        {
            "title": "Improve marks in Mathematics",
            "prompt": "I get low marks in maths in tests. What are 5 practical steps I can take this month to improve for Class 10 boards?",
            "expected": "Focus on NCERT problems, practice previous year board questions, maintain formula sheet, time-bound mock tests, and targeted revision of weak chapters."
        },
        {
            "title": "Stream selection after Class 10",
            "prompt": "I like biology and computers but my marks are mixed. Which stream should I pick after Class 10 to keep options open?",
            "expected": "Explain Science (Medical/Non-medical), Commerce, Humanities, tradeoffs, and suggest subject combinations that keep college options open."
        },
        {
            "title": "College admission guidance",
            "prompt": "Which colleges offer good BSc Computer Science and what are the typical cutoffs and application timelines?",
            "expected": "List a few well-known colleges, general cutoff ranges, application portals and typical timelines for admissions."
        },
        {
            "title": "Scholarships & exam registrations",
            "prompt": "Tell me about common scholarships for Class 11 students and upcoming important exam registration dates.",
            "expected": "Summarize common scholarship schemes, eligibility basics, and registration windows for board exams and competitive exams; recommend official sites for verification."
        },
    ]

    cols = st.columns(1)
    lang = st.selectbox("Language / भाषा", ["English", "हिन्दी", "Hinglish", "Regional"], index=0)
    asset_map = {
        "English": "cheatsheet_en.md",
        "हिन्दी": "cheatsheet_hi.md",
        "Hinglish": "cheatsheet_hinglish.md",
        "Regional": "cheatsheet_pa.md",
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
    st.write("Tip: Update your profile (Board, Class, City) in the sidebar — this helps the advisor tailor responses to your board and academic goals.")

elif page == "Book Appointment":
    st.header("Book an Appointment with an Advisor")
    name = st.text_input("Student name")
    email = st.text_input("Email")
    appointment_date = st.date_input("Appointment date", min_value=date.today(), value=date.today())
    available_slots = _filtered_appointment_slots(appointment_date)
    if available_slots:
        appointment_time = st.selectbox(
            "Appointment time (peak hours only)",
            available_slots,
            format_func=lambda value: datetime.strptime(value, "%H:%M").strftime("%I:%M %p"),
        )
        appointment_when = datetime.combine(appointment_date, datetime.strptime(appointment_time, "%H:%M").time()).isoformat(timespec="minutes")
        st.caption(f"Selected time window: {appointment_when}")
    else:
        appointment_time = None
        appointment_when = None
        st.info("No remaining peak-hour slots are available for today. Please choose a future date.")
    notes = st.text_area("Notes (optional)", value=f"Board: {saved_student_profile.get('board', 'Auto')} | Class: {saved_student_profile.get('class_level', 'Auto')} | Goal: {saved_student_profile.get('goal', 'Board exam prep')}")
    if st.button("Book"):
        if not name or not email or not appointment_when:
            st.error("Please fill in your name, email, and select a working-hour slot.")
        else:
            appt = appointments.book_appointment(name, email, appointment_when, notes=notes)
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
        st.info("Use this dashboard to watch which topics need clearer guidance or new examples.")
    except Exception as e:
        st.error("No interaction data yet or failed to load: " + str(e))

elif page == "Admin":
    st.header("Admin Tools")
    st.subheader("Course Recommendations (demo)")
    interests = st.text_input("Interests (comma separated)", value="math, science, programming")
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

    st.subheader("Stream guidance for Class 11/12")
    stream_interests = st.text_input("Stream interests (comma separated)", value="biology, maths, coding")
    stream_strengths = st.text_input("Stream strengths (comma separated)", value="math, writing, problem solving")
    stream_marks = st.text_input("Subject marks (optional, e.g. maths:82, science:78, commerce:70)", value="")
    if st.button("Suggest streams"):
        marks = {}
        for item in stream_marks.split(","):
            if ":" not in item:
                continue
            subject, score = item.split(":", 1)
            try:
                marks[subject.strip().lower()] = float(score.strip())
            except ValueError:
                continue

        stream_profile = {
            "board": saved_student_profile.get("board", "Auto"),
            "class_level": saved_student_profile.get("class_level", "Auto"),
            "interests": [item.strip() for item in stream_interests.split(",") if item.strip()],
            "strengths": [item.strip() for item in stream_strengths.split(",") if item.strip()],
            "goals": goals,
            "marks": marks,
        }
        stream_recs = recommender.recommend_streams(stream_profile)
        for rec in stream_recs:
            with st.expander(f"{rec.get('name')} - {rec.get('subjects')}", expanded=False):
                st.write(rec.get("best_for"))
                if rec.get("evidence"):
                    st.caption(f"Matched signals: {rec.get('evidence')}")

