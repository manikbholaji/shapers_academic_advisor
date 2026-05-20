import json
import os
from datetime import datetime

DATA_DIR = "data"
APPT_FILE = os.path.join(DATA_DIR, "appointments.json")

os.makedirs(DATA_DIR, exist_ok=True)


def _read():
    if not os.path.exists(APPT_FILE):
        return []
    with open(APPT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(data):
    with open(APPT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def book_appointment(student_name, email, when, advisor="Advisor", notes=""):
    """Create a simple appointment entry and return a confirmation id."""
    data = _read()
    appt = {
        "id": len(data) + 1,
        "student_name": student_name,
        "email": email,
        "advisor": advisor,
        "when": when,
        "notes": notes,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    data.append(appt)
    _write(data)
    return appt


def list_appointments():
    return _read()

if __name__ == "__main__":
    print(book_appointment("Test Student", "s@example.com", "2026-06-01T10:00:00", "Dr. Rao", "Discuss electives"))
