import json
from collections import defaultdict

KB_PATH = "app/knowledge_base.json"

def load_kb(path=KB_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def recommend_courses(student_profile, kb=None, top_n=3):
    """Simple rule-based recommender.

    student_profile: dict with keys: interests (list), completed (list), goals (str)
    kb: loaded knowledge base
    """
    if kb is None:
        kb = load_kb()

    courses = kb.get("courses", [])
    scores = defaultdict(int)

    interests = [i.lower() for i in student_profile.get("interests", [])]
    completed = set([c.upper() for c in student_profile.get("completed", [])])
    goals = student_profile.get("goals", "").lower()
    board = (student_profile.get("board") or "").lower()
    class_level = (student_profile.get("class_level") or "").lower()

    for c in courses:
        code = c.get("code")
        name = c.get("name", "")
        tags = [t.lower() for t in c.get("tags", [])]
        desc = c.get("description", "").lower()

        # Base score
        score = 0
        # Prefer courses matching interests or goals
        for it in interests:
            if it in tags or it in desc or it in name.lower():
                score += 3
        if any(g in desc or g in name.lower() or g in tags for g in goals.split()):
            score += 2
        # Boost if course explicitly targets the student's board
        if board:
            if board in " ".join(tags) or board.replace(' ', '') in code.lower():
                score += 4
            # Treat state-board style profiles as a match for state-board content.
            if board in ("state board", "stateboard", "regional board") and any(t for t in tags if "state" in t):
                score += 3
        # Boost if course is targeted at the student's class level (e.g., class 10)
        if class_level:
            cls_tag = class_level.replace(' ', '').replace('-', '').lower()
            # common forms: "class10", "class 10", "class10-math" etc.
            if any(cls_tag in t.replace(' ', '').lower() for t in tags) or cls_tag in desc.replace(' ', ''):
                score += 3
        # Penalize if already completed
        if code in completed:
            score -= 100
        # Prefer foundational courses
        if "found" in tags or "foundations" in desc:
            score += 1
        # Add small boost for no prerequisites (good for starters)
        if not c.get("prerequisites"):
            score += 1

        scores[code] = score

    # Return top_n course dicts
    ranked = sorted([c for c in courses], key=lambda x: scores.get(x.get("code"), 0), reverse=True)
    return ranked[:top_n]


def recommend_streams(student_profile, kb=None):
    """Suggest Class 11/12 streams based on interests, goals, and strengths."""
    if kb is None:
        kb = load_kb()

    profiles = [
        {
            "name": "Science - Medical",
            "subjects": "Biology, Chemistry, Physics",
            "best_for": "students interested in medicine, life sciences, biotech, or allied health",
            "signals": ["biology", "medical", "doctor", "neet", "health", "life science"],
        },
        {
            "name": "Science - Non-medical",
            "subjects": "Mathematics, Physics, Chemistry",
            "best_for": "students who like maths, engineering, computer science, or applied problem solving",
            "signals": ["math", "maths", "engineering", "coding", "computer", "physics", "non-medical"],
        },
        {
            "name": "Commerce",
            "subjects": "Accountancy, Business Studies, Economics",
            "best_for": "students who are interested in business, finance, management, or entrepreneurship",
            "signals": ["commerce", "business", "finance", "accounting", "economics", "entrepreneur"],
        },
        {
            "name": "Humanities",
            "subjects": "History, Political Science, Sociology, Psychology",
            "best_for": "students who enjoy writing, social studies, policy, design thinking, or public service",
            "signals": ["humanities", "arts", "history", "politics", "sociology", "psychology", "writing", "design"],
        },
    ]

    interests = [item.lower() for item in student_profile.get("interests", [])]
    goals = (student_profile.get("goals") or "").lower()
    strengths = [item.lower() for item in student_profile.get("strengths", [])]
    marks = student_profile.get("marks", {}) if isinstance(student_profile.get("marks"), dict) else {}

    ranked_streams = []
    for profile in profiles:
        score = 0
        evidence = []
        for signal in profile["signals"]:
            if any(signal in text for text in interests + strengths + [goals]):
                score += 3
                evidence.append(signal)

        board = (student_profile.get("board") or "").lower()
        class_level = (student_profile.get("class_level") or "").lower()
        if "class 11" in class_level or "class 12" in class_level:
            score += 1
        if board in ("cbse", "icse", "state board"):
            score += 1

        if marks:
            science_mark = marks.get("science") or marks.get("math") or marks.get("mathematics")
            if profile["name"].startswith("Science") and isinstance(science_mark, (int, float)) and science_mark >= 75:
                score += 2
            if profile["name"] == "Commerce" and isinstance(marks.get("commerce"), (int, float)) and marks.get("commerce") >= 70:
                score += 2

        ranked_streams.append(
            {
                "name": profile["name"],
                "subjects": profile["subjects"],
                "best_for": profile["best_for"],
                "score": score,
                "evidence": ", ".join(sorted(set(evidence))) if evidence else "",
            }
        )

    ranked_streams.sort(key=lambda item: item["score"], reverse=True)
    return ranked_streams


def recommend_program_paths(student_profile, kb=None, top_n=5):
    """Recommend diploma, undergraduate, and postgraduate pathways in India."""
    if kb is None:
        kb = load_kb()

    programs = kb.get("programs", [])
    if not programs:
        return []

    interests = [item.lower() for item in student_profile.get("interests", [])]
    goals = (student_profile.get("goals") or "").lower()
    desired_level = (student_profile.get("level") or "").strip().lower()
    class_level = (student_profile.get("class_level") or "").lower()
    location = (student_profile.get("location") or student_profile.get("city") or "").lower()

    ranked = []
    for program in programs:
        score = 0
        haystack = " ".join([
            program.get("level", ""),
            program.get("field", ""),
            program.get("title", ""),
            program.get("best_for", ""),
            " ".join(program.get("keywords", [])),
            " ".join(program.get("institutions", [])),
        ]).lower()

        if desired_level and desired_level in program.get("level", "").lower():
            score += 6
        elif not desired_level:
            score += 1

        if any(term in haystack for term in interests):
            score += 4
        if any(term in haystack for term in goals.split()):
            score += 2
        if "class 10" in class_level and "Diploma" in program.get("level", ""):
            score += 3
        if "class 12" in class_level and program.get("level") == "Undergraduate":
            score += 3
        if "ug" in class_level or "graduat" in class_level or "post" in class_level:
            score += 1
        if location and any(location in institution.lower() for institution in program.get("institutions", [])):
            score += 2

        ranked.append(
            {
                "level": program.get("level", ""),
                "field": program.get("field", ""),
                "title": program.get("title", ""),
                "best_for": program.get("best_for", ""),
                "institutions": program.get("institutions", []),
                "note": program.get("note", ""),
                "entry_after": program.get("entry_after", []),
                "score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_n]

if __name__ == "__main__":
    demo = {"interests": ["Programming", "Python"], "completed": [], "goals": "software developer"}
    kb = load_kb()
    print(recommend_courses(demo, kb))
