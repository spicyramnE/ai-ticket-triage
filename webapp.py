"""
Ticket Triage web app - demonstrates WITHOUT AI vs WITH AI live.
Run:  python webapp.py   then open http://localhost:5000
"""
import csv
from flask import Flask, request, render_template_string
from triage_lib import rule_triage, ai_triage

app = Flask(__name__)

PRIORITY_COLOR = {"Critical": "#c0392b", "High": "#e67e22",
                  "Medium": "#f1c40f", "Low": "#27ae60"}

PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>Ticket Triage</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#f4f6f9;margin:0;color:#222}
 .wrap{max-width:900px;margin:30px auto;padding:0 16px}
 h1{color:#1f3864}
 .card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:20px}
 input,textarea{width:100%;padding:10px;border:1px solid #ccc;border-radius:6px;font-size:14px;box-sizing:border-box}
 textarea{height:90px;resize:vertical}
 label{font-weight:600;font-size:13px;color:#555}
 button{background:#1f3864;color:#fff;border:0;padding:11px 22px;border-radius:6px;font-size:15px;cursor:pointer;margin-top:10px}
 button:hover{background:#163055}
 .cols{display:flex;gap:16px}
 .col{flex:1;border:1px solid #e3e3e3;border-radius:8px;padding:16px}
 .col h3{margin:0 0 10px;font-size:15px}
 .rule{background:#fafafa}.ai{background:#eef4ff}
 .badge{display:inline-block;padding:4px 12px;border-radius:14px;color:#fff;font-weight:600;font-size:13px}
 .cat{background:#34495e}
 table{width:100%;border-collapse:collapse;font-size:13px}
 th,td{border:1px solid #ddd;padding:6px 8px;text-align:left}
 th{background:#1f3864;color:#fff}
 .ok{color:#27ae60;font-weight:700}.xx{color:#c0392b;font-weight:700}
 a{color:#1f3864}
 .ex{font-size:12px;color:#666}
</style></head><body><div class="wrap">
<h1>Support Ticket Triage &mdash; Without AI vs With AI</h1>
<div class="card">
 <form method="post" action="/">
  <label>Subject</label>
  <input name="subject" value="{{subject}}" placeholder="e.g. Checkout broken">
  <label>Ticket text</label>
  <textarea name="body" placeholder="Describe the issue...">{{body}}</textarea>
  <button type="submit">Triage this ticket</button>
  <span class="ex">&nbsp; or <a href="/batch">run all 10 sample tickets &raquo;</a></span>
 </form>
</div>

{% if result %}
<div class="card">
 <div class="cols">
  <div class="col rule">
   <h3>&#128462; Without AI (keyword rules)</h3>
   Category: <span class="badge cat">{{result.rule_cat}}</span><br><br>
   Priority: <span class="badge" style="background:{{result.rule_pri_c}}">{{result.rule_pri}}</span>
  </div>
  <div class="col ai">
   <h3>&#129302; With AI (flan-t5-large)</h3>
   Category: <span class="badge cat">{{result.ai_cat}}</span><br><br>
   Priority: <span class="badge" style="background:{{result.ai_pri_c}}">{{result.ai_pri}}</span>
  </div>
 </div>
</div>
{% endif %}

{% if batch %}
<div class="card">
 <h3>All 10 sample tickets &mdash; accuracy vs correct answers</h3>
 <table>
  <tr><th>Metric</th><th>Without AI</th><th>With AI</th></tr>
  <tr><td>Category correct</td><td>{{batch.cat_rule}}</td><td>{{batch.cat_ai}}</td></tr>
  <tr><td>Priority correct</td><td>{{batch.pri_rule}}</td><td>{{batch.pri_ai}}</td></tr>
  <tr><td>Both correct</td><td>{{batch.both_rule}}</td><td>{{batch.both_ai}}</td></tr>
 </table>
 <br>
 <table>
  <tr><th>#</th><th>Subject</th><th>True</th><th>Rule-based</th><th>With AI</th></tr>
  {% for r in batch.rows %}
  <tr>
   <td>{{r.id}}</td><td>{{r.subject}}</td>
   <td>{{r.true_cat}} / {{r.true_pri}}</td>
   <td class="{{r.rule_flag}}">{{r.rule_cat}} / {{r.rule_pri}}</td>
   <td class="{{r.ai_flag}}">{{r.ai_cat}} / {{r.ai_pri}}</td>
  </tr>
  {% endfor %}
 </table>
 <p class="ex">OK (green) = matches the correct answer, XX (red) = wrong.</p>
</div>
{% endif %}
</div></body></html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    subject = body = ""
    result = None
    if request.method == "POST":
        subject = request.form.get("subject", "")
        body = request.form.get("body", "")
        rc, rp = rule_triage(subject, body)
        ac, ap = ai_triage(subject, body)
        result = {
            "rule_cat": rc, "rule_pri": rp, "rule_pri_c": PRIORITY_COLOR.get(rp, "#555"),
            "ai_cat": ac, "ai_pri": ap, "ai_pri_c": PRIORITY_COLOR.get(ap, "#555"),
        }
    return render_template_string(PAGE, subject=subject, body=body, result=result, batch=None)


@app.route("/batch")
def batch():
    rows = []
    cr = pr = br = ca = pa = ba = 0
    with open("tickets.csv", newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))
    for t in tickets:
        rc, rp = rule_triage(t["subject"], t["body"])
        ac, ap = ai_triage(t["subject"], t["body"])
        tc, tp = t["true_category"], t["true_priority"]
        cr += rc == tc; pr += rp == tp; br += (rc, rp) == (tc, tp)
        ca += ac == tc; pa += ap == tp; ba += (ac, ap) == (tc, tp)
        rows.append({
            "id": t["id"], "subject": t["subject"],
            "true_cat": tc, "true_pri": tp,
            "rule_cat": rc, "rule_pri": rp, "rule_flag": "ok" if (rc, rp) == (tc, tp) else "xx",
            "ai_cat": ac, "ai_pri": ap, "ai_flag": "ok" if (ac, ap) == (tc, tp) else "xx",
        })
    n = len(tickets)
    fmt = lambda x: f"{x}/{n} ({100*x//n}%)"
    batch = {
        "rows": rows,
        "cat_rule": fmt(cr), "pri_rule": fmt(pr), "both_rule": fmt(br),
        "cat_ai": fmt(ca), "pri_ai": fmt(pa), "both_ai": fmt(ba),
    }
    return render_template_string(PAGE, subject="", body="", result=None, batch=batch)


if __name__ == "__main__":
    print("Open http://localhost:5000  (first AI triage loads the model, ~20s)")
    app.run(host="0.0.0.0", port=5000, debug=False)
