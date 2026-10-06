"""
Ticket triage WITHOUT AI (keyword rules).
Reads tickets.csv, triages each ticket, writes output_without_ai.csv.
The rule logic lives in triage_lib.py (rule_triage).
"""
import csv
from triage_lib import rule_triage


def main():
    rows = []
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        for t in csv.DictReader(f):
            cat, pri = rule_triage(t["subject"], t["body"])
            rows.append({"id": t["id"], "subject": t["subject"],
                         "predicted_category": cat, "predicted_priority": pri})

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
