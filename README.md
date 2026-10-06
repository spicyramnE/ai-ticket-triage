# AI vs Rule-Based Ticket Triage

## DevOps features in this project (where each concept lives)

| DevOps concept | Where it is in this project |
|----------------|------------------------------|
| **Version control** | Git + GitHub (this repository) |
| **CI/CD pipeline** | GitHub Actions (`.github/workflows/ci.yml`) runs on every push: installs deps, runs the triage, runs automated tests, runs the comparison |
| **Automated testing** | `test_triage.py` (pytest), executed by the CI pipeline |
| **Containerization** | `Dockerfile` packages the web app into a container (`docker build` / `docker run`) |
| **Incident management / AIOps** | The triage feature itself - routing support tickets to the right team at the right priority, improving MTTR using AI |

MTTR (Mean Time To Resolution) is one of the four DORA DevOps metrics; faster,
more accurate triage lowers it. Using AI to do operations work like this is
called **AIOps**.

---


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
| `triage_lib.py` | Shared triage logic (rule-based + AI), used by everything |
| `triage_without_ai.py` | CLI: rule-based triage using keyword matching (no AI) |
| `triage_with_ai.py` | CLI: AI triage using a local model (google/flan-t5-large) |
| `webapp.py` | **Web app** to demo both methods live in the browser |
| `prompt.txt` | The instructions (prompts) the AI model is given |
| `compare.py` | Scores both methods against the true labels |
| `requirements_ai.txt` | Python libraries needed for the AI + web app |

Both CLI scripts write their predictions to `output_without_ai.csv` /
`output_with_ai.csv`, and `compare.py` scores them.

## Web app (live demo)

```bash
pip install -r requirements_ai.txt
python webapp.py
# open http://localhost:5000
```

A "Help Desk" simulator that tells the story in three stages:

1. **Incoming queue** - 10 raw tickets arrive, untriaged.
2. **Triage the usual way (rules)** - keyword rules auto-triage them and
   *mis-route* several (a Critical data leak marked Low, a resolved ticket
   reopened as a Bug, a question sent to Finance as Critical). Mis-handled
   rows are shown in red with the reason.
3. **Triage with AI** - the AI model re-reads the same tickets and routes them
   correctly; fixed rows turn green.

There is also a **"Try it live"** box that runs the real AI model on any ticket
you type (first run loads the model, ~20 seconds).

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
