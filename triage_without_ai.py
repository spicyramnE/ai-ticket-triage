"""
Ticket triage WITHOUT AI.
Uses simple keyword matching rules to assign a category and priority.
This is the traditional, rule-based approach.
"""
import csv

# Keyword rules for category: first match wins
CATEGORY_KEYWORDS = [
    ("Billing", ["invoice", "charged", "refund", "payment", "billing", "subscription"]),
    ("Security", ["leak", "breach", "hacked", "password stolen", "vulnerability"]),
    ("Performance", ["slow", "lag", "takes", "seconds", "loading", "freeze", "freezing"]),
    ("Bug", ["crash", "crashing", "broken", "error", "cannot", "not working", "bug"]),
    ("Feature Request", ["add", "would be great", "nice to have", "feature", "request"]),
]

# Keyword rules for priority
HIGH_WORDS = ["crash", "crashing", "broken", "cannot", "charged twice", "freeze", "freezing"]
CRITICAL_WORDS = ["urgent", "critical", "emergency", "losing sales", "down"]


def triage(subject, body):
    text = (subject + " " + body).lower()

    category = "Uncategorized"
    for cat, words in CATEGORY_KEYWORDS:
        if any(w in text for w in words):
            category = cat
            break

    priority = "Low"
    if any(w in text for w in HIGH_WORDS):
        priority = "High"
    if any(w in text for w in CRITICAL_WORDS):
        priority = "Critical"

    return category, priority


def main():
    rows = []
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        for t in csv.DictReader(f):
            cat, pri = triage(t["subject"], t["body"])
            rows.append({
                "id": t["id"],
                "subject": t["subject"],
                "predicted_category": cat,
                "predicted_priority": pri,
            })

    with open("output_without_ai.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "subject", "predicted_category", "predicted_priority"])
        w.writeheader()
        w.writerows(rows)

    print("Rule-based triage complete. Results:\n")
    for r in rows:
        print(f"  #{r['id']:>2}  {r['predicted_category']:<16} {r['predicted_priority']:<10} {r['subject']}")
    print("\nSaved to output_without_ai.csv")


if __name__ == "__main__":
    main()
