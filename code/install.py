#!/usr/bin/env python3
"""Turn sweep records into installed results: one paper each, one record each
in results.json.

Guards, in order:
  * the entry must still carry the conjecture, checked against a freshly
    re-read corpus entry rather than against the sweep's own copy;
  * no entry may receive two papers for the same conjecture;
  * the paper must build, and must not be empty.
"""
import os, sys, json, argparse, datetime, subprocess
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import corpus, recur, paper, mkpaper_transfer

RESULTS = os.path.join(ROOT, "results.json")
PAPERS = os.path.join(ROOT, "papers")
SOURCES = os.path.join(ROOT, "paper-sources")


def load_results():
    if os.path.exists(RESULTS):
        with open(RESULTS) as fh:
            return json.load(fh)
    return []


def save_results(rs):
    tmp = RESULTS + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rs, fh, indent=1)
    os.replace(tmp, RESULTS)


def still_open(anum, line):
    """Re-read the entry from the corpus and confirm the exact line is still
    there and still conjectural."""
    e = corpus.parse(anum)
    if e is None:
        return False, "entry gone"
    cl = [ln for _, _, ln in corpus.conj_lines(e)]
    if line not in cl:
        return False, "conjecture line no longer present or no longer conjectural"
    return True, ""


def one(job):
    rec, date = job
    a = rec["anum"]
    claims = [c for c in rec["claims"] if c["status"] == "proved"]
    e = corpus.parse(a)
    if e is None:
        return {"anum": a, "skipped": "entry gone"}
    live = [ln for _, _, ln in corpus.conj_lines(e)]
    claims = [c for c in claims if c["line"] in live]
    if not claims:
        return {"anum": a, "skipped": "no conjecture line still open"}
    rec = dict(rec, claims=claims)
    P = mkpaper_transfer.make(rec, date)
    built, err = paper.build(P.tex(date), PAPERS, a, keep_tex_dir=SOURCES)
    if not built:
        return {"anum": a, "skipped": "paper did not build: " + err[:200]}
    out = []
    for c in claims:
        who, when, signed = mkpaper_transfer.attribution(c["line"],
                                                         rec.get("author", ""))
        d = {"line": c["line"], "field": c["field"], "index": c["idx"],
             "kind": c["kind"], "coeffs": c["coeffs"], "order": c["order"],
             "nmin_claimed": c["nmin"], "threshold": c["threshold"],
             "first_meaningful_n": c["first_meaningful_n"],
             "holds_everywhere": c["holds_everywhere"],
             "contributor": who, "contributor_date": when,
             "contributor_from_line": signed}
        if c["kind"] == "gf":
            d.update(num=c["num"], den=c["den"],
                     gf_checked_to=c.get("gf_checked_to"),
                     gf_shift=c.get("gf_shift"))
        out.append(d)
    return {
        "id": a, "anum": a, "name": rec["name"], "offset": rec["offset"],
        "entry_revision": rec["revision"], "entry_modified": rec["modified"],
        "entry_author": rec.get("author", ""),
        "entry_keywords": rec.get("keywords", ""),
        "method": "transfer-matrix", "family": rec["family"],
        "spec": rec["spec"], "W": rec["W"], "q": rec["q"],
        "states_full": rec["nfull"], "states_trim": rec["ntrim"],
        "states_lumped": rec["S"],
        "brute_checked": rec.get("brute_checked", 0),
        "published_terms": rec["all_terms"],
        "claims": out,
        "paper": f"papers/{a}.pdf", "source": f"paper-sources/{a}.tex",
        "date_settled": date, "status": "proved",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", nargs="+")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    date = datetime.date.today().strftime("%d %B %Y")
    have = load_results()
    seen = {r["anum"] for r in have}
    jobs = []
    for path in a.jsonl:
        for line in open(path):
            rec = json.loads(line)
            if rec.get("status") != "done":
                continue
            if rec["anum"] in seen:
                continue
            if not any(c["status"] == "proved" for c in rec["claims"]):
                continue
            seen.add(rec["anum"])
            jobs.append((rec, date))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} new results to install")
    out, skipped = [], []
    with ProcessPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(one, jobs, chunksize=4)):
            if "skipped" in r:
                skipped.append(r)
            else:
                out.append(r)
            if i % 200 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
    have += out
    save_results(have)
    print(f"installed {len(out)}, skipped {len(skipped)}, total {len(have)}")
    if skipped:
        from collections import Counter
        print(Counter(s["skipped"][:60] for s in skipped).most_common(8))


if __name__ == "__main__":
    main()
