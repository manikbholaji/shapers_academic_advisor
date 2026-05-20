import os
import csv
from datetime import datetime
import pandas as pd

DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "conversations.csv")
os.makedirs(DATA_DIR, exist_ok=True)


def _ensure_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "user", "role", "message", "sentiment", "compound"])


def log_interaction(user, role, message, sentiment_label=None, compound=0.0):
    _ensure_log()
    with open(LOG_FILE, "a", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat() + "Z", user, role, message, sentiment_label or "", compound])


def load_interactions():
    _ensure_log()
    return pd.read_csv(LOG_FILE)


def simple_stats(df=None):
    if df is None:
        df = load_interactions()
    total = len(df)
    by_sent = df["sentiment"].value_counts().to_dict() if "sentiment" in df.columns else {}
    user_counts = df["user"].value_counts().head(10).to_dict()
    return {"total": total, "by_sentiment": by_sent, "top_users": user_counts}

if __name__ == "__main__":
    # demo
    log_interaction("student1", "user", "I need course advice", "neutral", 0.0)
    print(load_interactions().tail())
    print(simple_stats())
