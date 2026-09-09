#!/usr/bin/env python3
"""Re-read each installed entry from the live OEIS and confirm the conjecture
is still there and still unproved.

The corpus this project works from is the OEIS's own daily mirror, so a
`git pull` in the clone is already a live re-check within a day; this script
is the finer check, going to oeis.org for a named sample or for the whole
roster, at a rate that is polite to the server.
"""
import json, os, sys, time, argparse, re, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


UA = "oeis-conjecture-check/1.0 (independent verification; polite rate)"


def fetch(anum, tries=3):
    url = f"https://oeis.org/search?q=id:{anum}&fmt=json"
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as fh:
                d = json.loads(fh.read().decode("utf-8", "replace"))
        except Exception:
            time.sleep(4 * (k + 1))
            continue
        r = d[0] if isinstance(d, list) else (d.get("results") or [None])[0]
        if r:
            return r
        time.sleep(4 * (k + 1))
    return None


def lines(r):
    out = []
    for k in ("comment", "formula", "example", "name"):
        v = r.get(k)
        if isinstance(v, str):
            out.append(v)
        elif v:
            out += list(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "live.jsonl"))
    a = ap.parse_args()
    recs = json.load(open(os.path.join(ROOT, "results.json")))
    done = set()
    if os.path.exists(a.out):
        for ln in open(a.out):
            try:
                done.add(json.loads(ln)["anum"])
            except Exception:
                pass
    recs = [r for r in recs if r["anum"] not in done][a.start:]
    if a.limit:
        recs = recs[:a.limit]
    ok = bad = miss = 0
    with open(a.out, "a") as fh:
        for i, rec in enumerate(recs):
            t0 = time.time()
            r = fetch(rec["anum"])
            if r is None:
                miss += 1
                fh.write(json.dumps({"anum": rec["anum"], "status": "unreachable"}) + "\n")
                continue
            L = lines(r)
            want = [c["line"] for c in rec["claims"]]
            still = [w for w in want if any(w.strip() in x for x in L)]
            gone = [w for w in want if w not in still]
            proved = bool(re.search(r"\bproof\b|\bproved\b|\bproven\b",
                                    " ".join(L), re.I))
            fh.write(json.dumps({"anum": rec["anum"], "revision": r.get("revision"),
                                 "time": r.get("time", "")[:10],
                                 "still": len(still), "gone": gone,
                                 "mentions_proof": proved}) + "\n")
            fh.flush()
            if gone:
                bad += 1
            else:
                ok += 1
            if (i + 1) % 100 == 0:
                print(f"  {i+1}/{len(recs)} ok {ok} changed {bad} unreachable {miss}",
                      flush=True)
            wait = a.sleep - (time.time() - t0)
            if wait > 0:
                time.sleep(wait)
    print(f"{ok} unchanged, {bad} with a line no longer present, {miss} unreachable")


if __name__ == "__main__":
    main()
