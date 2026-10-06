"""
Shared triage logic used by both the command-line scripts and the web app.

- rule_triage()  -> the WITHOUT-AI method (keyword matching)
- ai_triage()    -> the WITH-AI method (local flan-t5-large model)
"""

CATEGORIES = ["Bug", "Performance", "Billing", "Security",
              "Feature Request", "Question", "Resolved"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]

# ----------------------------------------------------------------------
# WITHOUT AI : simple keyword rules
# ----------------------------------------------------------------------
CATEGORY_KEYWORDS = [
    ("Billing", ["invoice", "charged", "refund", "payment", "billing", "subscription"]),
    ("Security", ["leak", "breach", "hacked", "password stolen", "vulnerability"]),
    ("Performance", ["slow", "lag", "takes", "seconds", "loading", "freeze", "freezing"]),
    ("Bug", ["crash", "crashing", "broken", "error", "cannot", "not working", "bug"]),
    ("Feature Request", ["add", "would be great", "nice to have", "feature", "request"]),
]
HIGH_WORDS = ["crash", "crashing", "broken", "cannot", "charged twice", "freeze", "freezing"]
CRITICAL_WORDS = ["urgent", "critical", "emergency", "losing sales", "down"]


def rule_triage(subject, body):
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


# ----------------------------------------------------------------------
# WITH AI : local flan-t5-large instruction model (loaded once)
# ----------------------------------------------------------------------
_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model
    if _model is None:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        name = "google/flan-t5-large"
        _tokenizer = AutoTokenizer.from_pretrained(name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(name)
    return _tokenizer, _model


def _ask(question):
    tok, mdl = _load_model()
    inputs = tok(question, return_tensors="pt", truncation=True)
    out = mdl.generate(**inputs, max_new_tokens=10)
    return tok.decode(out[0], skip_special_tokens=True).strip()


def _match(answer, options):
    low = answer.lower()
    for opt in options:
        if opt.lower() in low:
            return opt
    return options[-1]


def ai_triage(subject, body):
    text = (subject + ". " + body).replace("\n", " ")
    cat_q = (
        "Classify this customer support ticket into exactly one category from this list: "
        f"{', '.join(CATEGORIES)}. A ticket that says a problem is already fixed is Resolved. "
        f"Ticket: \"{text}\". Category:"
    )
    pri_q = (
        "What is the priority of this support ticket? Choose exactly one: "
        f"{', '.join(PRIORITIES)}. A security or data leak, or something that stops customers, "
        f"is Critical. A fixed issue or a nice-to-have is Low. Ticket: \"{text}\". Priority:"
    )
    return _match(_ask(cat_q), CATEGORIES), _match(_ask(pri_q), PRIORITIES)
