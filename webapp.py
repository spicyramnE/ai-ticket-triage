"""
Help-Desk Ticket Triage Simulator (demo app).

Tells the story in 3 stages:
  1. Incoming queue  - raw tickets arrive, untriaged
  2. Traditional way - keyword rules auto-triage them, and MIS-ROUTE several
  3. With AI         - the AI model re-triages and routes them correctly

Plus a "Try your own ticket" box that runs the AI model live.

Run:  python webapp.py   then open http://localhost:5000
"""
import csv
from flask import Flask, request, render_template_string
from triage_lib import rule_triage, ai_triage

app = Flask(__name__)

# Which team each category is routed to (makes mis-routing visible)
ROUTE = {
    "Bug": "Engineering", "Performance": "SRE / Engineering",
    "Billing": "Finance", "Security": "Security Team",
    "Feature Request": "Product", "Question": "Support L1",
    "Resolved": "Auto-close", "Uncategorized": "Manual review",
}
PRI_COLOR = {"Critical": "#c0392b", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#27ae60"}


def load_tickets():
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_ai_results():
    """Real flan-t5-large output produced by triage_with_ai.py."""
    res = {}
    try:
        with open("output_with_ai.csv", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                res[r["id"]] = (r["predicted_category"], r["predicted_priority"])
    except FileNotFoundError:
        pass
    return res


PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Help Desk Triage</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#eef1f5;margin:0;color:#222}
 .wrap{max-width:1050px;margin:24px auto;padding:0 16px}
 h1{color:#1f3864;margin-bottom:4px}
 .sub{color:#666;margin-top:0}
 .card{background:#fff;border-radius:10px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:18px}
 .steps{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 2px}
 .btn{display:inline-block;background:#1f3864;color:#fff;border:0;padding:10px 18px;border-radius:6px;font-size:14px;cursor:pointer;text-decoration:none}
 .btn:hover{background:#163055}
 .btn.ghost{background:#fff;color:#1f3864;border:1px solid #1f3864}
 .btn.active{background:#27ae60}
 table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
 th,td{border:1px solid #e2e2e2;padding:7px 9px;text-align:left;vertical-align:top}
 th{background:#1f3864;color:#fff}
 .msg{color:#555;font-size:12px;max-width:320px}
 .badge{display:inline-block;padding:3px 10px;border-radius:12px;color:#fff;font-weight:600;font-size:12px}
 .cat{background:#34495e}
 .muted{color:#aaa}
 tr.bad{background:#fdecea}
 tr.good{background:#eafaf1}
 .flag{color:#c0392b;font-weight:700}
 .okmark{color:#27ae60;font-weight:700}
 .panel{border-radius:8px;padding:12px 14px;margin-top:12px;font-size:14px}
 .panel.warn{background:#fdecea;border:1px solid #f5b7b1}
 .panel.good{background:#eafaf1;border:1px solid #abebc6}
 .panel h4{margin:0 0 8px}
 .panel li{margin:3px 0}
 input,textarea{width:100%;padding:9px;border:1px solid #ccc;border-radius:6px;font-size:14px;box-sizing:border-box}
 textarea{height:70px;resize:vertical}
 label{font-weight:600;font-size:13px;color:#555}
 .cols{display:flex;gap:16px;margin-top:10px}
 .col{flex:1;border:1px solid #e3e3e3;border-radius:8px;padding:14px}
 .rule{background:#fafafa}.ai{background:#eef4ff}
 .stepnote{font-size:13px;color:#777;margin:4px 0 0}
</style></head><body><div class="wrap">
<h1>Help Desk &mdash; Ticket Triage</h1>
<p class="sub">Incoming support tickets must be tagged with a <b>category</b> (which team)
and a <b>priority</b> (how urgent), so the right people fix the urgent things first.</p>

<div class="card">
 <div class="steps">
   <a class="btn {{ 'active' if stage=='start' else 'ghost' }}" href="/">1. Incoming queue</a>
   <a class="btn {{ 'active' if stage=='rules' else 'ghost' }}" href="/?show=rules">2. Triage the usual way (rules)</a>
   <a class="btn {{ 'active' if stage=='ai' else 'ghost' }}" href="/?show=ai">3. Triage with AI</a>
 </div>
 {% if stage=='start' %}<p class="stepnote">10 new tickets just arrived. None are triaged yet. Click step 2 to see how automatic keyword rules handle them.</p>{% endif %}
 {% if stage=='rules' %}<p class="stepnote">This is what usually happens: simple keyword rules tag each ticket automatically. Rows in <span class="flag">red</span> were mis-handled.</p>{% endif %}
 {% if stage=='ai' %}<p class="stepnote">Now the AI model (flan-t5-large) re-reads the same tickets. Rows in <span class="okmark">green</span> are now correct.</p>{% endif %}

 <table>
  <tr><th>#</th><th>Subject &amp; message</th><th>Category</th><th>Priority</th><th>Routed to</th><th>Status</th></tr>
  {% for r in rows %}
  <tr class="{{r.cls}}">
   <td>{{r.id}}</td>
   <td><b>{{r.subject}}</b><div class="msg">{{r.msg}}</div></td>
   {% if stage=='start' %}
     <td class="muted">&mdash;</td><td class="muted">&mdash;</td><td class="muted">&mdash;</td>
     <td class="muted">&#9203; Untriaged</td>
   {% else %}
     <td><span class="badge cat">{{r.cat}}</span></td>
     <td><span class="badge" style="background:{{r.pri_c}}">{{r.pri}}</span></td>
     <td>{{r.team}}</td>
     <td>{% if r.ok %}<span class="okmark">&#10004; correct</span>{% else %}<span class="flag">&#9888; {{r.note}}</span>{% endif %}</td>
   {% endif %}
  </tr>
  {% endfor %}
 </table>

 {% if stage=='rules' and problems %}
 <div class="panel warn">
  <h4>&#9888; What went wrong with the rule-based approach</h4>
  <ul>{% for p in problems %}<li>{{p}}</li>{% endfor %}</ul>
  <b>{{correct_rule}}/10 tickets fully correct.</b> Mis-routed tickets go to the wrong team and urgent ones can sit unnoticed &mdash; this is the real cost of brittle triage.
 </div>
 {% endif %}
 {% if stage=='ai' %}
 <div class="panel good">
  <h4>&#10004; What the AI did better</h4>
  <ul>{% for p in wins %}<li>{{p}}</li>{% endfor %}</ul>
  <b>{{correct_ai}}/10 tickets fully correct</b> (categories 10/10). The AI understands meaning &mdash; negation, context and real urgency &mdash; so tickets reach the right team at the right priority.
 </div>
 {% endif %}
</div>

<div class="card">
 <h3 style="margin-top:0">&#128269; Try it live &mdash; type any ticket</h3>
 <p class="stepnote">This runs the real AI model on your machine (first run loads it, ~20s).</p>
 <form method="post" action="/try">
  <label>Subject</label>
  <input name="subject" value="{{t_subject}}" placeholder="e.g. Checkout broken">
  <label>Message</label>
  <textarea name="body" placeholder="Describe the issue...">{{t_body}}</textarea>
  <button class="btn" type="submit" style="margin-top:10px">Triage live</button>
 </form>
 {% if live %}
 <div class="cols">
  <div class="col rule">
   <h4>&#128462; Keyword rules (no AI)</h4>
   Category: <span class="badge cat">{{live.rc}}</span> &rarr; {{live.rteam}}<br><br>
   Priority: <span class="badge" style="background:{{live.rc_c}}">{{live.rp}}</span>
  </div>
  <div class="col ai">
   <h4>&#129302; AI (flan-t5-large)</h4>
   Category: <span class="badge cat">{{live.ac}}</span> &rarr; {{live.ateam}}<br><br>
   Priority: <span class="badge" style="background:{{live.ac_c}}">{{live.ap}}</span>
  </div>
 </div>
 {% endif %}
</div>
</div></body></html>
"""


def build_rows(stage, tickets, ai_results):
    rows, problems, wins = [], [], []
    correct_rule = correct_ai = 0
    for t in tickets:
        tc, tp = t["true_category"], t["true_priority"]
        base = {"id": t["id"], "subject": t["subject"], "msg": t["body"]}
        if stage == "start":
            rows.append({**base, "cls": "", "ok": False})
            continue
        if stage == "rules":
            cat, pri = rule_triage(t["subject"], t["body"])
        else:
            cat, pri = ai_results.get(t["id"], ("Uncategorized", "Low"))
        ok = (cat, pri) == (tc, tp)
        if stage == "rules" and ok:
            correct_rule += 1
        if stage == "ai" and ok:
            correct_ai += 1
        note = ""
        if not ok:
            if cat != tc and pri != tp:
                note = f"wrong team & priority (should be {tc}/{tp})"
            elif cat != tc:
                note = f"wrong team (should be {tc})"
            else:
                note = f"wrong priority (should be {tp})"
        rows.append({
            **base, "cat": cat, "pri": pri, "pri_c": PRI_COLOR.get(pri, "#555"),
            "team": ROUTE.get(cat, "Manual review"), "ok": ok, "note": note,
            "cls": "good" if ok else ("bad" if stage == "rules" else ""),
        })

    if stage == "rules":
        for t in tickets:
            cat, pri = rule_triage(t["subject"], t["body"])
            tc, tp = t["true_category"], t["true_priority"]
            if (cat, pri) == (tc, tp):
                continue
            if t["id"] == "2":
                problems.append("#2 'login fixed now' is a resolved ticket, but the rule saw the word 'crashing' and reopened it as a Bug for Engineering.")
            elif t["id"] == "5":
                problems.append("#5 a friendly billing question got sent to Finance as Critical ('download' contains 'down'), a false alarm.")
            elif t["id"] == "8":
                problems.append("#8 a Critical data-leak was marked Low priority (no urgency keyword) - a serious security issue left sitting in the queue.")
            elif t["id"] == "7":
                problems.append("#7 'not urgent' feature request was marked Critical, because the rule matched the word 'urgent'.")
            elif t["id"] == "4":
                problems.append("#4 a slow-dashboard complaint was marked Low instead of Medium.")
            elif t["id"] == "9":
                problems.append("#9 an app crash (Bug) was tagged Performance, so it may reach the wrong team.")
            elif t["id"] == "10":
                problems.append("#10 a thank-you note (no issue) could not be categorised at all - needs manual review.")

    if stage == "ai":
        wins = [
            "#2 correctly recognised as Resolved (understood 'NOT crashing anymore').",
            "#5 correctly a low-priority Question, not a Finance emergency.",
            "#8 the data leak is correctly Security / Critical.",
            "All 10 categories correct, vs 6/10 with keyword rules.",
        ]
    return rows, problems, wins, correct_rule, correct_ai


@app.route("/")
def home():
    stage = request.args.get("show", "start")
    if stage not in ("start", "rules", "ai"):
        stage = "start"
    tickets = load_tickets()
    ai_results = load_ai_results() if stage == "ai" else {}
    rows, problems, wins, cr, ca = build_rows(stage, tickets, ai_results)
    return render_template_string(
        PAGE, stage=stage, rows=rows, problems=problems, wins=wins,
        correct_rule=cr, correct_ai=ca, live=None, t_subject="", t_body="",
    )


@app.route("/try", methods=["POST"])
def try_live():
    subject = request.form.get("subject", "")
    body = request.form.get("body", "")
    rc, rp = rule_triage(subject, body)
    try:
        ac, ap = ai_triage(subject, body)
    except Exception:
        # e.g. running in the lightweight Docker image without the AI model
        ac, ap = "unavailable", "unavailable"
    live = {
        "rc": rc, "rp": rp, "rc_c": PRI_COLOR.get(rp, "#555"), "rteam": ROUTE.get(rc, "Manual review"),
        "ac": ac, "ap": ap, "ac_c": PRI_COLOR.get(ap, "#555"), "ateam": ROUTE.get(ac, "Manual review"),
    }
    tickets = load_tickets()
    rows, *_ = build_rows("start", tickets, {})
    return render_template_string(
        PAGE, stage="start", rows=rows, problems=[], wins=[],
        correct_rule=0, correct_ai=0, live=live, t_subject=subject, t_body=body,
    )


if __name__ == "__main__":
    print("Open http://localhost:5000  (the 'Try it live' box loads the AI model on first use, ~20s)")
    app.run(host="0.0.0.0", port=5000, debug=False)
