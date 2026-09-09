#!/usr/bin/env python3
"""Generic sweep: point a family reader at its pool, settle what can be
settled, and record a reason for everything that cannot.

The pool is rebuilt from the corpus index on every run.  No sweep here ever
reads a saved candidate list.
"""
import sys, os, json, time, pickle, importlib, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recur, automaton

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
BRUTE_BUDGET = 200_000


def load_index():
    return pickle.load(open(os.path.join(DATA, "index.pkl"), "rb"))


def candidates(entry_conj):
    out = []
    seen = set()
    for f, i, ln in entry_conj:
        r = recur.parse_recurrence(ln)
        if r and tuple(r[0]) not in seen:
            seen.add(tuple(r[0]))
            out.append((f, i, ln, r))
    return out


def settle(fam, anum, meta, terms, cj, cap=3_000_000, margin=6, rowcap=8192):
    nm, off, kw, au, mod, nt, rev = meta
    rec = {"anum": anum, "name": nm, "offset": off, "family": fam.FAMILY}
    spec = fam.parse(nm)
    if spec is None:
        return dict(rec, status="refused", reason="name not parsed")
    if spec.get("kind") != "seq":
        return dict(rec, status="refused", reason="table entry")
    cands = candidates(cj)
    if not cands:
        return dict(rec, status="refused", reason="no parsable recurrence")
    T = list(terms)
    if len(T) < 8:
        return dict(rec, status="refused", reason="too few published terms")
    valid, first_ok, whole_ok, W, q = fam.make(spec)
    if q ** W > rowcap:
        return dict(rec, status="refused", reason=f"row alphabet {q}^{W} over cap")
    m = automaton.Model(W, q, valid, first_ok, cap=cap)
    t0 = time.time()
    try:
        m.build()
    except automaton.TooBig as e:
        return dict(rec, status="refused", reason=str(e))
    build_t = time.time() - t0
    S = m.S
    need = len(T) + off + 4
    a = m.counts(need)
    got = [a[off + i - 1] for i in range(len(T))]
    if got != T:
        k = next(i for i in range(len(T)) if got[i] != T[i])
        return dict(rec, status="refused", reason="model does not reproduce data",
                    first_bad=k, model=str(got[k]), published=str(T[k]))
    # independent count, written against the finished array
    bf = []
    n = 1
    while q ** (W * n) <= BRUTE_BUDGET and n <= len(T):
        bf.append(automaton.brute(n, W, q, whole_ok))
        n += 1
    if bf and bf != a[:len(bf)]:
        return dict(rec, status="refused", reason="brute force disagrees with model",
                    brute=[str(x) for x in bf], model=[str(x) for x in a[:len(bf)]])
    out = []
    for f, i, ln, (coeffs, nmin, body) in cands:
        D = len(coeffs)
        N = S + D + len(T) + margin
        u = m.residuals(coeffs, N)
        last = 0
        for j in range(len(u) - 1, -1, -1):
            if u[j] != 0:
                last = j + 1
                break
        if last > len(u) - S:
            out.append({"line": ln, "field": f, "idx": i,
                        "coeffs": coeffs, "nmin": nmin, "order": D,
                        "status": "inconclusive",
                        "reason": "residuals nonzero inside the bound"})
            continue
        thresh_n = last + D + off - 1
        first_n = D + off
        out.append({"line": ln, "field": f, "idx": i, "coeffs": coeffs,
                    "nmin": nmin, "order": D, "threshold": thresh_n,
                    "first_meaningful_n": first_n,
                    "holds_everywhere": thresh_n < first_n,
                    "status": "proved", "S": S})
    return dict(rec, status="done", S=S, nfull=m.nfull, ntrim=m.ntrim,
                W=W, q=q, spec=fam.jsonspec(spec),
                brute_checked=len(bf),
                build_seconds=round(build_t, 2), claims=out,
                nterms=len(T), modified=mod, author=au, keywords=kw,
                revision=rev, terms=[str(x) for x in T[:12]])


def run(famname, out, limit=0, start=0, only=None, cap=3_000_000, rowcap=8192,
        quiet=False):
    fam = importlib.import_module(famname)
    D = load_index()
    meta, terms, conj = D["meta"], D["terms"], D["conj"]
    pool = fam.pool(meta, conj)
    if only:
        pool = [a for a in pool if a in set(only)]
    pool = pool[start:]
    if limit:
        pool = pool[:limit]
    reasons, nproved = {}, 0
    with open(out, "a") as fh:
        for a in pool:
            t0 = time.time()
            try:
                r = settle(fam, a, meta[a], terms[a], conj[a], cap=cap, rowcap=rowcap)
            except Exception as e:
                r = {"anum": a, "family": fam.FAMILY, "status": "error",
                     "reason": f"{type(e).__name__}: {e}"}
            r["seconds"] = round(time.time() - t0, 2)
            key = r.get("reason", r["status"])
            if r["status"] == "done":
                st = {c["status"] for c in r["claims"]}
                key = "done:" + ("proved" if "proved" in st else "inconclusive")
                nproved += sum(1 for c in r["claims"] if c["status"] == "proved")
            reasons[key] = reasons.get(key, 0) + 1
            fh.write(json.dumps(r) + "\n")
            fh.flush()
    if not quiet:
        print(json.dumps(reasons, indent=1))
        print("entries with a proved claim:",
              sum(v for k, v in reasons.items() if k == "done:proved"))
        print("claims proved:", nproved)
    return reasons


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("family")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--cap", type=int, default=3_000_000)
    ap.add_argument("--rowcap", type=int, default=8192)
    a = ap.parse_args()
    run(a.family, a.out, a.limit, a.start, cap=a.cap, rowcap=a.rowcap)
