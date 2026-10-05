"""
Ticket triage WITH AI.
Uses a pretrained instruction-following AI model (google/flan-t5-large) that
reads each ticket and answers which category and priority it belongs to.
Unlike keyword rules, the model understands the meaning of the sentence.

First run downloads the model (~3 GB); later runs use the cached copy.
"""
import csv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

CATEGORIES = ["Bug", "Performance", "Billing", "Security",
              "Feature Request", "Question", "Resolved"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]

print("Loading AI model (first run downloads it, please wait)...")
MODEL = "google/flan-t5-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)


def ask(question):
    inputs = tokenizer(question, return_tensors="pt", truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=10)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def match(answer, options):
    answer_low = answer.lower()
    for opt in options:
        if opt.lower() in answer_low:
            return opt
    return options[-1]  # fall back to the safest option


def triage(subject, body):
    text = (subject + ". " + body).replace("\n", " ")

    cat_q = (
        "Classify this customer support ticket into exactly one category "
        f"from this list: {', '.join(CATEGORIES)}. "
        "A ticket that says a problem is already fixed is Resolved. "
        f"Ticket: \"{text}\". Category:"
    )
    category = match(ask(cat_q), CATEGORIES)

    pri_q = (
        "What is the priority of this support ticket? Choose exactly one: "
        f"{', '.join(PRIORITIES)}. A security or data leak, or something that "
        "stops customers, is Critical. A fixed issue or a nice-to-have is Low. "
        f"Ticket: \"{text}\". Priority:"
    )
    priority = match(ask(pri_q), PRIORITIES)

    return category, priority


def main():
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))

    rows = []
    for t in tickets:
        cat, pri = triage(t["subject"], t["body"])
        rows.append({
            "id": t["id"],
            "subject": t["subject"],
            "predicted_category": cat,
            "predicted_priority": pri,
        })
        print(f"  #{t['id']:>2}  {cat:<16} {pri:<10} {t['subject']}")

    with open("output_with_ai.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "subject", "predicted_category", "predicted_priority"])
        w.writeheader()
        w.writerows(rows)

    print("\nAI triage complete. Saved to output_with_ai.csv")


if __name__ == "__main__":
    main()
