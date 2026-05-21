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

st.set_page_config(
    page_title="SHAPERS Academic Advisor",
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional custom CSS styling
st.markdown("""
<style>
    /* Global styling */
    :root {
        --primary: #0f172a;
        --accent: #3b82f6;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --light: #f8fafc;
        --border: #e2e8f0;
    }
    
    /* Main content area */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Headers */
    h1 {
        color: var(--primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: var(--primary) !important;
        font-weight: 600 !important;
        border-bottom: 3px solid var(--accent) !important;
        padding-bottom: 0.5rem !important;
        margin-top: 1.5rem !important;
    }
    
    h3 {
        color: var(--primary) !important;
        font-weight: 600 !important;
    }
    
    /* Caption and small text */
    .caption {
        color: #64748b !important;
        font-size: 0.875rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, var(--accent) 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border: 2px solid var(--border) !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Info, warning, success boxes */
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(59, 130, 246, 0.02) 100%) !important;
        border-left: 4px solid var(--accent) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.02) 100%) !important;
        border-left: 4px solid var(--success) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(245, 158, 11, 0.02) 100%) !important;
        border-left: 4px solid var(--warning) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(239, 68, 68, 0.02) 100%) !important;
        border-left: 4px solid var(--danger) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        border-radius: 0.5rem !important;
        border-left: 4px solid var(--accent) !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    }
    
    /* Divider */
    hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, var(--border) 0%, transparent 100%) !important;
        margin: 2rem 0 !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        border-radius: 0.75rem !important;
        padding: 1rem !important;
    }
    
    /* Data frames */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 SHAPERS Academic Advisor for Indian Students")
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-top: -0.5rem;'>An experienced, friendly academic guide for CBSE, ICSE, State Board, and career pathways</p>", unsafe_allow_html=True)


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
    if profile.get("goal") == "Admission help":
        return [
            "Suggest diploma, undergraduate, and postgraduate options in India for a student interested in computer science.",
            "Which universities and colleges offer B.Com., B.Sc., or MBA pathways in India?",
            "How should I compare diploma versus degree routes after Class 10 or Class 12?",
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


def _program_level_options():
    return ["Diploma", "Undergraduate", "Postgraduate"]


def _field_interest_options():
    return [
        "Engineering / Computer Science",
        "Medical / Life Sciences",
        "Commerce / Management",
        "Humanities / Psychology / Public Policy",
    ]


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
    page = st.radio("Navigation", PROJECT_PAGES, label_visibility="collapsed")
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
    
    # Header section with gradient
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2>💬 Chat with Your Academic Advisor</h2>", unsafe_allow_html=True)
        st.markdown("Ask for study plans, stream guidance, admission help, exam tips, and more...")
    with col2:
        st.metric("Academic Year", academic_year)
    
    # Status cards
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        if provider == "Mock":
            st.info("📝 Mock mode active - add an API key to enable AI responses")
        else:
            st.success(f"✅ {provider} API connected")
    with status_col2:
        st.info(f"👤 Profile: {_profile_summary(saved_student_profile) or 'Update your profile in sidebar'}")
    
    st.markdown("---")
    
    # Prompt composer
    with st.form("prompt_composer_form", clear_on_submit=True):
        st.markdown("<h3>Your Question</h3>", unsafe_allow_html=True)
        prompt_text = st.text_area(
            "Ask anything",
            placeholder="Ask for study plans, stream guidance, admission help, exam tips, and more...",
            height=120,
            label_visibility="collapsed"
        )
        
        col_format = st.columns([2, 1, 1])
        with col_format[0]:
            response_format = st.radio(
                "Response format",
                ["Text", "PNG", "PDF"],
                horizontal=True,
                help="Choose Text for a chat reply, PNG for an image-style response, or PDF for a document-style response.",
                label_visibility="collapsed"
            )
        with col_format[1]:
            send_prompt = st.form_submit_button("🚀 Generate Reply", use_container_width=True)
        with col_format[2]:
            st.caption("📋 Edit earlier prompts below")

    if send_prompt and prompt_text.strip():
        st.session_state.messages.append({"role": "user", "content": prompt_text.strip()})
        with st.spinner("🤔 Generating response..."):
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

    # Quick starter prompts
    st.markdown("---")
    with st.expander("💡 Quick Starter Questions", expanded=True):
        prompts = _starter_prompts(saved_student_profile)
        cols = st.columns(len(prompts))
        for idx, (col, prompt) in enumerate(zip(cols, prompts)):
            with col:
                if st.button(f"Q{idx+1}: {prompt[:40]}...", key=f"starter_{idx}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.spinner("🤔 Thinking..."):
                        reply = client.send_message([
                            {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)},
                            *st.session_state.messages[1:],
                        ])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    s = sentiment.analyze_sentiment(prompt)
                    analytics_module.log_interaction(user="anonymous", role="user", message=prompt, sentiment_label=s["label"], compound=s["compound"])
                    analytics_module.log_interaction(user="anonymous", role="assistant", message=reply, sentiment_label="", compound=0.0)
                    st.rerun()

    # Conversation history
    st.markdown("---")
    st.markdown("<h3>📜 Conversation</h3>", unsafe_allow_html=True)
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            st.chat_message("assistant").write(msg["content"])

    # Export section
    if getattr(st.session_state, "latest_export_bytes", None):
        st.markdown("---")
        st.markdown("<h3>💾 Latest Generated File</h3>", unsafe_allow_html=True)
        export_name = st.session_state.get("latest_export_name", "ai_response.txt")
        export_format = st.session_state.get("latest_export_format", "text")
        export_col1, export_col2 = st.columns([3, 1])
        with export_col1:
            if export_format == "png":
                st.image(st.session_state.latest_export_bytes)
            elif export_format == "pdf":
                st.info("📄 PDF generated - download to view")
            else:
                st.info("📝 Text response ready - download below")
        with export_col2:
            if export_format == "png":
                st.download_button("⬇️ PNG", data=st.session_state.latest_export_bytes, file_name=export_name, mime="image/png", use_container_width=True)
            elif export_format == "pdf":
                st.download_button("⬇️ PDF", data=st.session_state.latest_export_bytes, file_name=export_name, mime="application/pdf", use_container_width=True)
            else:
                st.download_button("⬇️ Text", data=st.session_state.latest_export_bytes, file_name=export_name, mime="text/plain", use_container_width=True)

    # Prompt history editor
    _render_prompt_history_editor(saved_student_profile, academic_year, client)

    st.markdown("---")
    st.markdown("💡 **Pro tip:** Keep your board, class, and goal updated in the sidebar for more personalized advice.")


elif page == "Knowledge Base":
    academic_year = _current_academic_year()
    st.markdown(f"<h2>📚 Knowledge Base & Policies ({academic_year})</h2>", unsafe_allow_html=True)
    st.markdown(f"Automatically aligned to the current academic year: **{academic_year}**. India-wide diploma, undergraduate, and postgraduate pathways alongside board guidance.")
    
    kb = json.load(open("app/knowledge_base.json", "r", encoding="utf-8"))
    kb["academic_year"] = academic_year
    
    st.markdown("---")
    
    # Tabs or sections
    tab1, tab2, tab3, tab4 = st.tabs(["🎓 Boards", "📖 Programs", "🌍 Regional Tips", "📋 Policies"])
    
    with tab1:
        st.markdown("<h3>Indian Education Boards</h3>", unsafe_allow_html=True)
        if kb.get("boards"):
            for board in kb.get("boards", []):
                with st.expander(f"📌 {board.get('name')} — {board.get('type')}", expanded=False):
                    col_board_1, col_board_2 = st.columns([2, 1])
                    with col_board_1:
                        st.write(board.get("overview"))
                        st.write("**Classes:**", ", ".join(board.get("classes", [])))
                    with col_board_2:
                        st.write("**Core Focus:**")
                        for area in board.get("core_focus", []):
                            st.write(f"• {area}")
                    st.write("**Common Streams:**", ", ".join(board.get("common_streams", [])))
    
    with tab2:
        st.markdown("<h3>India Program Pathways</h3>", unsafe_allow_html=True)
        if kb.get("programs"):
            for program in kb.get("programs", []):
                level_icon = "📖" if program.get("level") == "Diploma" else "🎓" if program.get("level") == "Undergraduate" else "🏆"
                with st.expander(f"{level_icon} {program.get('level')} — {program.get('title')}", expanded=False):
                    st.write(f"**Field:** {program.get('field')}")
                    st.write(program.get("best_for"))
                    
                    col_prog_1, col_prog_2 = st.columns(2)
                    with col_prog_1:
                        if program.get("entry_after"):
                            st.caption(f"**Entry after:** {', '.join(program.get('entry_after'))}")
                    with col_prog_2:
                        if program.get("note"):
                            st.info(program.get("note"))
                    
                    if program.get("institutions"):
                        st.markdown("**Example Institutions:**")
                        for institution in program.get("institutions", []):
                            st.write(f"✓ {institution}")
    
    with tab3:
        st.markdown("<h3>Regional Study Tips</h3>", unsafe_allow_html=True)
        regional_resources = kb.get("regional_resources", [])
        if regional_resources:
            for res in regional_resources:
                with st.expander(f"🌏 {res.get('label', 'Study tip')}", expanded=False):
                    st.write(res.get("tips"))
        else:
            st.info("No regional resources available yet.")
    
    with tab4:
        st.markdown("<h3>Education Policies</h3>", unsafe_allow_html=True)
        if kb.get("policies"):
            for p in kb.get("policies", []):
                with st.expander(f"📄 {p.get('title')}", expanded=False):
                    st.write(p.get("summary"))
                    if st.checkbox(f"Show full details", key=f"policy_{p.get('title')}"):
                        st.write(p.get("details"))
        else:
            st.info("No policies available yet.")
    
    st.markdown("---")
    
    st.markdown("<h3>📝 Legacy Board Prep Resources</h3>", unsafe_allow_html=True)
    st.caption("Foundation references for quick revision support")
    
    if kb.get("courses"):
        for c in kb.get("courses", []):
            with st.expander(f"📖 {c.get('code')} - {c.get('name')}", expanded=False):
                st.write(c.get("description"))
                if c.get("tags"):
                    st.caption(f"Tags: {', '.join(c.get('tags', []))}")
    else:
        st.info("No course references available.")

elif page == "Demo":
    st.markdown("<h2>🎯 Demo: Sample Prompts & Expected Answers</h2>", unsafe_allow_html=True)
    st.markdown("Quick examples to try — tailored for Indian students across CBSE, ICSE, and State Boards.")

    academic_year = _current_academic_year()

    demo_cases = [
        {
            "title": "📚 Weekly study plan — Class 10",
            "prompt": "Suggest a weekly study plan for Class 10 board exams, focusing on Maths and Science, including daily tasks and revision slots.",
            "expected": "A 7-day schedule splitting topics by chapter, daily practice problems, 30-40 minute revision at day end, weekly test on Sunday, and tips to balance school work with revision."
        },
        {
            "title": "📈 Improve marks in Mathematics",
            "prompt": "I get low marks in maths in tests. What are 5 practical steps I can take this month to improve for Class 10 boards?",
            "expected": "Focus on NCERT problems, practice previous year board questions, maintain formula sheet, time-bound mock tests, and targeted revision of weak chapters."
        },
        {
            "title": "🎓 Stream selection after Class 10",
            "prompt": "I like biology and computers but my marks are mixed. Which stream should I pick after Class 10 to keep options open?",
            "expected": "Explain Science (Medical/Non-medical), Commerce, Humanities, tradeoffs, and suggest subject combinations that keep college options open."
        },
        {
            "title": "🏫 Program pathway guidance",
            "prompt": "Recommend diploma, undergraduate, and postgraduate courses in India for a student interested in computer science, and mention specific universities or colleges that currently offer them.",
            "expected": "Compare diploma, UG, and PG routes, list example Indian institutions for each, mention eligibility, and remind the student to verify the current admission brochure and seat intake."
        },
        {
            "title": "💰 Scholarships & exam registrations",
            "prompt": "Tell me about common scholarships for Class 11 students and upcoming important exam registration dates.",
            "expected": "Summarize common scholarship schemes, eligibility basics, and registration windows for board exams and competitive exams; recommend official sites for verification."
        },
    ]

    # Cheatsheet section
    st.markdown("---")
    st.markdown("<h3>📋 Cheatsheet Downloads</h3>", unsafe_allow_html=True)
    
    lang_col = st.columns(1)[0]
    with lang_col:
        lang = st.selectbox("Select language", ["English", "हिन्दी", "Hinglish", "Regional"], index=0, label_visibility="collapsed")
    
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
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(label=f"📄 Markdown ({lang})", data=cheatsheet_text, file_name=f"shapers_cheatsheet_{lang}.md", use_container_width=True)
    
    png_bytes = generate_png_bytes(cheatsheet_text)
    pdf_bytes = generate_pdf_bytes(cheatsheet_text)
    
    with dl_col2:
        if png_bytes:
            st.download_button("🖼️ PNG", data=png_bytes, file_name=f"shapers_cheatsheet_{lang}.png", mime='image/png', use_container_width=True)
        else:
            st.info("PNG unavailable")
    
    with dl_col3:
        if pdf_bytes:
            st.download_button("📕 PDF", data=pdf_bytes, file_name=f"shapers_cheatsheet_{lang}.pdf", mime='application/pdf', use_container_width=True)
        else:
            st.info("PDF unavailable")

    if png_bytes:
        with st.expander("👁️ Preview Cheatsheet", expanded=False):
            st.image(png_bytes)

    # Demo cases
    st.markdown("---")
    st.markdown("<h3>💬 Sample Conversations</h3>", unsafe_allow_html=True)
    
    for idx, case in enumerate(demo_cases):
        with st.expander(case['title'], expanded=(idx == 0)):
            col_prompt, col_action = st.columns([3, 1])
            
            with col_prompt:
                st.markdown("**📝 Prompt:**")
                st.write(case["prompt"])
                st.markdown("**✅ Expected Summary:**")
                st.info(case["expected"])
            
            with col_action:
                if st.button("➡️ Use in Chat", key=f"use_chat_{idx}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": case["prompt"]})
                    with st.spinner("🔄 Sending..."):
                        reply = client.send_message([
                            {"role": "system", "content": _build_system_message(saved_student_profile, academic_year)},
                            *st.session_state.messages[1:],
                        ])
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.success("✅ Sent to Chat! Switch to Chat tab to view.")
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Update your Board, Class, and City in the sidebar for personalized responses.")


elif page == "Book Appointment":
    st.markdown("<h2>📅 Book an Appointment with an Advisor</h2>", unsafe_allow_html=True)
    st.markdown("Schedule a 1:1 session for personalized academic guidance during peak working hours (10 AM - 6 PM).")
    
    st.markdown("---")
    
    with st.form("appointment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h4>Personal Information</h4>", unsafe_allow_html=True)
            name = st.text_input("Full name", placeholder="Enter your name")
            email = st.text_input("Email address", placeholder="your.email@example.com")
        
        with col2:
            st.markdown("<h4>Appointment Details</h4>", unsafe_allow_html=True)
            appointment_date = st.date_input("📅 Preferred date", min_value=date.today(), value=date.today())
            available_slots = _filtered_appointment_slots(appointment_date)
            
            if available_slots:
                appointment_time = st.selectbox(
                    "⏰ Time slot (peak hours 10 AM - 6 PM)",
                    available_slots,
                    format_func=lambda value: datetime.strptime(value, "%H:%M").strftime("%I:%M %p"),
                )
                appointment_when = datetime.combine(appointment_date, datetime.strptime(appointment_time, "%H:%M").time()).isoformat(timespec="minutes")
            else:
                appointment_time = None
                appointment_when = None
                st.warning("❌ No slots available for this date. Please choose another date.")
        
        st.markdown("---")
        
        st.markdown("<h4>Additional Notes</h4>", unsafe_allow_html=True)
        notes = st.text_area(
            "Tell us about your academic goals and concerns (optional)",
            value=f"Board: {saved_student_profile.get('board', 'Not specified')} | Class: {saved_student_profile.get('class_level', 'Not specified')} | Goal: {saved_student_profile.get('goal', 'Not specified')}",
            height=100,
            placeholder="E.g., I need help with stream selection, exam preparation, etc."
        )
        
        st.markdown("---")
        
        submit_button = st.form_submit_button("✅ Confirm Booking", use_container_width=True)
    
    if submit_button:
        if not name or not email or not appointment_when:
            st.error("❌ Please fill in your name, email, and select a time slot.")
        else:
            appt = appointments.book_appointment(name, email, appointment_when, notes=notes)
            st.success(f"✅ Appointment confirmed!")
            st.balloons()
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info(f"**Appointment ID:** {appt.get('id')}")
            with col_info2:
                st.info(f"**Time:** {appt.get('when')}")
            st.caption("📧 A confirmation email has been sent to your inbox. Save this appointment ID for your records.")


elif page == "Analytics":
    st.markdown("<h2>📊 Interaction Analytics</h2>", unsafe_allow_html=True)
    st.markdown("Track user interactions, sentiment trends, and advisor performance.")
    
    try:
        df = analytics_module.load_interactions()
        stats = analytics_module.simple_stats(df)
        
        st.markdown("---")
        
        # Key metrics
        st.markdown("<h3>📈 Key Metrics</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interactions", len(df), delta=None)
        with col2:
            if stats and 'avg_sentiment' in stats:
                st.metric("Avg Sentiment", f"{stats['avg_sentiment']:.2f}", delta="Neutral" if -0.1 < stats['avg_sentiment'] < 0.1 else "Positive" if stats['avg_sentiment'] > 0 else "Negative")
            else:
                st.metric("Avg Sentiment", "N/A")
        with col3:
            positive_count = len(df[df.get('sentiment_label', 'neutral') == 'positive']) if 'sentiment_label' in df.columns else 0
            st.metric("Positive Responses", positive_count)
        with col4:
            negative_count = len(df[df.get('sentiment_label', 'neutral') == 'negative']) if 'sentiment_label' in df.columns else 0
            st.metric("Needs Improvement", negative_count)
        
        st.markdown("---")
        
        # Detailed data
        st.markdown("<h3>📋 Recent Interactions</h3>", unsafe_allow_html=True)
        
        col_count, col_display = st.columns([1, 3])
        with col_count:
            display_count = st.slider("Show last N interactions", min_value=10, max_value=100, value=50, step=10)
        
        st.dataframe(df.tail(display_count), use_container_width=True)
        
        st.markdown("---")
        
        # Statistics summary
        if stats:
            st.markdown("<h3>📊 Summary Statistics</h3>", unsafe_allow_html=True)
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.info(f"**User Engagement:** {stats.get('total_interactions', 0)} interactions logged")
            with col_stat2:
                st.success(f"**Data Quality:** {stats.get('interactions_with_sentiment', 0)} interactions with sentiment analysis")
        
        st.markdown("---")
        st.info("💡 **Dashboard Insights:** Use this to identify which topics need better explanation or new examples. Monitor sentiment trends to improve advisor responses.")
        
    except Exception as e:
        st.error(f"❌ No interaction data available yet or failed to load: {str(e)}")
        st.info("Start chatting in the Chat tab to generate analytics data.")

elif page == "Admin":
    st.markdown("<h2>⚙️ Admin Tools & Pathway Advisor</h2>", unsafe_allow_html=True)
    st.markdown("Professional academic pathway planning from Class 11 through postgraduate education.")
    
    st.markdown("---")
    
    st.markdown("<h3>🎯 Pathway Advisor Configuration</h3>", unsafe_allow_html=True)
    
    with st.form("pathway_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h4>Interest & Location</h4>", unsafe_allow_html=True)
            field_interest = st.selectbox("📚 Field of interest", _field_interest_options(), index=0)
            location = st.text_input("📍 Preferred city / state (optional)", value=saved_student_profile.get("city", ""), placeholder="E.g., Mumbai, Delhi, Bangalore")
        
        with col2:
            st.markdown("<h4>Academic Context</h4>", unsafe_allow_html=True)
            class_level = st.selectbox("🎓 Current class stage", ["Class 10", "Class 11", "Class 12", "UG completion"], index=1)
            student_signals = st.text_input("💡 Optional keywords (comma separated)", value="coding, maths, biology, business")
        
        st.markdown("---")
        
        st.markdown(f"**Current Profile:** {_profile_summary(saved_student_profile) or 'Update in sidebar'}")
        
        st.markdown("---")
        
        submit_pathway = st.form_submit_button("🚀 Build Complete Pathway", use_container_width=True)
    
    if submit_pathway:
        profile = {
            "class_level": class_level,
            "location": location,
            "city": location,
            "interests": [i.strip() for i in student_signals.split(",") if i.strip()],
        }
        recs = recommender.recommend_field_pathways(field_interest, profile)
        
        st.markdown("---")
        st.markdown("<h3>🗺️ Recommended Pathways</h3>", unsafe_allow_html=True)
        
        if not recs:
            st.warning("⚠️ No pathways found in the knowledge base yet.")
        else:
            for idx, r in enumerate(recs, 1):
                with st.expander(f"#{idx} {r.get('field')} — Complete Pathway", expanded=(idx==1)):
                    class_11 = r.get("class_11", {})
                    class_12 = r.get("class_12", {})
                    
                    # Class 11 Section
                    st.markdown("#### 📚 Class 11 - Foundation Phase")
                    col_11_1, col_11_2 = st.columns(2)
                    with col_11_1:
                        st.markdown(f"**Recommended streams:**")
                        streams = class_11.get("streams", [])
                        for stream in streams:
                            st.write(f"✓ {stream}")
                    with col_11_2:
                        st.markdown(f"**Key subjects:**")
                        subjects = class_11.get("subjects", [])
                        for subject in subjects:
                            st.write(f"• {subject}")
                    
                    if class_11.get("focus"):
                        st.info(f"💡 **Focus:** {class_11.get('focus')}")
                    
                    st.markdown("---")
                    
                    # Class 12 Section
                    st.markdown("#### 🎯 Class 12 - Specialization Phase")
                    st.markdown(f"**Action Plan:**")
                    for item in class_12.get("what_to_do", []):
                        st.write(f"→ {item}")
                    
                    if class_12.get("entrance_exams"):
                        st.info(f"**Entrance Exams:** {', '.join(class_12.get('entrance_exams', []))}")
                    
                    # Routes
                    st.markdown("---")
                    
                    col_routes_1, col_routes_2, col_routes_3 = st.columns(3)
                    
                    # Diploma Route
                    with col_routes_1:
                        diploma_route = class_12.get("diploma_route", {})
                        if diploma_route:
                            st.markdown("#### 📖 Diploma Route")
                            st.caption(f"Entry: {diploma_route.get('available_after', '—')}")
                            if diploma_route.get("institutions"):
                                st.markdown("**Top Institutions:**")
                                for institution in diploma_route.get("institutions", [])[:3]:
                                    st.write(f"- {institution}")
                    
                    # Undergraduate Route
                    with col_routes_2:
                        if class_12.get("undergraduate_routes"):
                            st.markdown("#### 🎓 Undergraduate")
                            st.caption(", ".join(class_12.get("undergraduate_routes", [])))
                            if class_12.get("undergraduate_institutions"):
                                st.markdown("**Top Universities:**")
                                for institution in class_12.get("undergraduate_institutions", [])[:3]:
                                    st.write(f"- {institution}")
                    
                    # Postgraduate Route
                    with col_routes_3:
                        if class_12.get("postgraduate_routes"):
                            st.markdown("#### 🏆 Postgraduate")
                            st.caption(", ".join(class_12.get("postgraduate_routes", [])))
                            if class_12.get("postgraduate_institutions"):
                                st.markdown("**Top Institutions:**")
                                for institution in class_12.get("postgraduate_institutions", [])[:3]:
                                    st.write(f"- {institution}")
                    
                    # Career Directions
                    if r.get("career_direction"):
                        st.markdown("---")
                        st.markdown("#### 💼 Typical Career Directions")
                        for career in r.get("career_direction", []):
                            st.write(f"→ {career}")
            
            st.markdown("---")
            st.success("✅ Pathway builder complete! Use this information to plan your academic journey.")
    
    st.markdown("---")
    st.markdown("<h3>ℹ️ About This Tool</h3>", unsafe_allow_html=True)
    st.info("""
    **The Pathway Advisor** provides an end-to-end academic roadmap:
    - **Class 11:** Stream selection and foundation building
    - **Class 12:** Subject focus and entrance exam preparation  
    - **Diploma/UG/PG:** Multiple career route options with institutions
    - **Career:** Typical professional directions for your field
    
    Remember to verify current admission cycles on official institution websites.
    """)

