# AI vs Rule-Based Ticket Triage

A small DevOps lab task comparing **support-ticket triage done the traditional
way (keyword rules)** against **the same triage done with AI (Claude)**.

Ticket triage = reading each incoming support ticket and tagging it with a
**category** (Bug, Billing, Security, etc.) and a **priority** (Critical, High,
Medium, Low) so the right team picks it up first. In real DevOps/support teams
this is done constantly, and doing it well directly affects response time.

## Files

| File | What it is |
|------|------------|
| `tickets.csv` | 10 sample tickets with the correct (true) category & priority |
| `triage_without_ai.py` | Rule-based triage using keyword matching (no AI) |
| `triage_with_ai.py` | AI triage using a local model (google/flan-t5-large) |
| `prompt.txt` | The instructions (prompts) the AI model is given |
| `compare.py` | Scores both methods against the true labels |
| `requirements_ai.txt` | Python libraries needed for the AI script |

Both scripts write their predictions to `output_without_ai.csv` /
`output_with_ai.csv`, and `compare.py` scores them.

## How to run

```bash
# without AI (instant)
python triage_without_ai.py

# with AI (first run downloads ~3 GB model, then runs on CPU)
pip install -r requirements_ai.txt
python triage_with_ai.py

# compare both against the correct answers
python compare.py
```

## Result (measured, not hand-written)

| Metric | Without AI (keyword rules) | With AI (flan-t5-large) |
|--------|---------------------------|-------------------------|
| Category correct | 6/10 (60%) | **10/10 (100%)** |
| Priority correct | 5/10 (50%) | 6/10 (60%) |
| Both correct | 3/10 (30%) | **6/10 (60%)** |

### Why the rule-based method failed

- **"NOT crashing anymore"** → keyword rule sees `crashing` and tags it a Bug,
  even though the ticket says the problem is fixed.
- **"not urgent"** → rule sees `urgent` and marks it Critical.
- **"where can I download my invoices"** → `download` contains `down`, so the
  rule marks it Critical; `invoice` makes it Billing instead of a Question.
- **Data leak** → no urgency keyword, so the rule marks a Critical security
  issue as Low.

### What the AI did better

The AI got **every category right (100%)**, including the cases that broke the
rules: it understood that "not crashing anymore" means **Resolved**, that a
friendly "where can I download my invoices" is a **Question** (not Billing), and
that a freezing app is a **Bug** (not Performance). It understands the *meaning*
of the sentence instead of matching words.

Priority is a harder, judgement-based task (it depends on business impact), so
the AI scored 6/10 there — still better than the rules' 5/10, and its misses
were only one level off (e.g. High vs Critical). Overall the AI doubled the
fully-correct rate (30% → 60%).
