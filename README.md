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
| `prompt.txt` | The prompt given to Claude to triage the same tickets |
| `output_with_ai.csv` | Claude's triage results |
| `compare.py` | Scores both methods against the true labels |

## How to run

```bash
python triage_without_ai.py   # produces output_without_ai.csv
python compare.py             # prints the comparison table
```

## Result

| Metric | Without AI | With AI |
|--------|-----------|---------|
| Category correct | 6/10 (60%) | 10/10 (100%) |
| Priority correct | 5/10 (50%) | 10/10 (100%) |
| Both correct | 3/10 (30%) | 10/10 (100%) |

### Why the rule-based method failed

- **"NOT crashing anymore"** → keyword rule sees `crashing` and tags it a Bug,
  even though the ticket says the problem is fixed.
- **"not urgent"** → rule sees `urgent` and marks it Critical.
- **"where can I download my invoices"** → `download` contains `down`, so the
  rule marks it Critical; `invoice` makes it Billing instead of a Question.
- **Data leak** → no urgency keyword, so the rule marks a Critical security
  issue as Low.

AI understands the *meaning* of the sentence, so it handles negation, context,
and real-world urgency that simple keyword rules cannot.
