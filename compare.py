"""
Compare the rule-based (without AI) triage against the AI triage.
Measures how many categories and priorities each method got right,
using the true labels in tickets.csv as the answer key.
"""
import csv


def load(path, cat_field, pri_field):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["id"]] = (r[cat_field], r[pri_field])
    return out


def score(predictions, truth):
    cat_ok = pri_ok = both_ok = 0
    total = len(truth)
    for tid, (tcat, tpri) in truth.items():
        pcat, ppri = predictions.get(tid, ("", ""))
        c = pcat == tcat
        p = ppri == tpri
        cat_ok += c
        pri_ok += p
        both_ok += c and p
    return cat_ok, pri_ok, both_ok, total


def pct(n, total):
    return f"{n}/{total} ({100*n/total:.0f}%)"


def main():
    truth = load("tickets.csv", "true_category", "true_priority")
    without = load("output_without_ai.csv", "predicted_category", "predicted_priority")
    with_ai = load("output_with_ai.csv", "predicted_category", "predicted_priority")

    wc, wp, wb, total = score(without, truth)
    ac, ap, ab, _ = score(with_ai, truth)

    print("=" * 60)
    print("  TICKET TRIAGE: WITHOUT AI  vs  WITH AI")
    print("=" * 60)
    print(f"{'Metric':<22}{'Without AI':<20}{'With AI':<20}")
    print("-" * 60)
    print(f"{'Category correct':<22}{pct(wc, total):<20}{pct(ac, total):<20}")
    print(f"{'Priority correct':<22}{pct(wp, total):<20}{pct(ap, total):<20}")
    print(f"{'Both correct':<22}{pct(wb, total):<20}{pct(ab, total):<20}")
    print("=" * 60)

    print("\nTicket-by-ticket (T=true, R=rule-based, A=AI):\n")
    for tid in sorted(truth, key=int):
        tc, tp = truth[tid]
        rc, rp = without[tid]
        ac2, ap2 = with_ai[tid]
        rflag = "OK " if (rc, rp) == (tc, tp) else "XX "
        aflag = "OK " if (ac2, ap2) == (tc, tp) else "XX "
        print(f"  #{tid:>2} | true: {tc:<15}{tp:<9}"
              f"| rule {rflag}{rc:<15}{rp:<9}"
              f"| ai {aflag}{ac2:<15}{ap2}")


if __name__ == "__main__":
    main()
