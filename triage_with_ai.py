"""
Ticket triage WITH AI (local flan-t5-large model).
Reads tickets.csv, triages each ticket, writes output_with_ai.csv.
The model + prompt logic lives in triage_lib.py (ai_triage).

First run downloads the model (~3 GB); later runs use the cached copy.
"""
import csv
from triage_lib import ai_triage


def main():
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))

    print("Running AI triage (first run loads the model, please wait)...\n")
    rows = []
    for t in tickets:
        cat, pri = ai_triage(t["subject"], t["body"])
        rows.append({"id": t["id"], "subject": t["subject"],
                     "predicted_category": cat, "predicted_priority": pri})
        print(f"  #{t['id']:>2}  {cat:<16} {pri:<10} {t['subject']}")

    with open("output_with_ai.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "subject", "predicted_category", "predicted_priority"])
        w.writeheader()
        w.writerows(rows)

    print("\nAI triage complete. Saved to output_with_ai.csv")


if __name__ == "__main__":
    main()
