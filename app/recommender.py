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
            # Treat PSEB and 'pseb' equivalently to state board tag
            if board in ("pseb", "punjab") and any(t for t in tags if "state" in t or "pseb" in t or "punjab" in t):
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

if __name__ == "__main__":
    demo = {"interests": ["Programming", "Python"], "completed": [], "goals": "software developer"}
    kb = load_kb()
    print(recommend_courses(demo, kb))
