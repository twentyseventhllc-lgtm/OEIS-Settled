#!/usr/bin/env python3
"""Generic sweep: point a family reader at its pool, settle what can be
settled, and record a reason for everything that cannot.

The pool is rebuilt from the corpus index on every run.  No sweep here ever
reads a saved candidate list.
"""
import sys, os, json, time, pickle, importlib, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recur, automaton, gf, claims as CL

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
BRUTE_BUDGET = 200_000


def load_index():
    return pickle.load(open(os.path.join(DATA, "index.pkl"), "rb"))


def candidates(entry_conj):
    """Every conjectural line that states a claim this engine can decide."""
    out, seen = [], set()
    for f, i, ln in entry_conj:
        cd = CL.parse_line(ln)
        if not cd:
            continue
        k = CL.key(cd)
        if k in seen:
            continue
        seen.add(k)
        cd.update(field=f, idx=i, line=ln)
        out.append(cd)
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
    t0 = time.time()
    if hasattr(fam, "model"):
        W, q = spec.get("W"), spec.get("q")
        try:
            m = fam.model(spec)
        except automaton.TooBig as e:
            return dict(rec, status="refused", reason=str(e))
        whole_ok = (fam.whole_ok_for(spec, spec.get("W"))
                    if hasattr(fam, "whole_ok_for") else None)
    else:
        valid, first_ok, whole_ok, W, q = fam.make(spec)
        if q ** W > rowcap:
            return dict(rec, status="refused",
                        reason=f"row alphabet {q}^{W} over cap")
        up, down = (fam.REACHfor(spec) if hasattr(fam, "REACHfor")
                    else getattr(fam, "REACH", (1, 1)))
        m = automaton.Model(W, q, valid, first_ok, cap=cap, up=up, down=down)
        try:
            m.build()
        except automaton.TooBig as e:
            return dict(rec, status="refused", reason=str(e))
    build_t = time.time() - t0
    S = m.S
    rowoff = spec.get("rowoff", 0)
    Dmax = max([len(cd["coeffs"]) for cd in cands]
                + [len(cd.get("poly") or []) for cd in cands])
    hi = off + len(T) + rowoff + S + Dmax + 40
    A = m.counts_from_zero(hi) if hasattr(m, "counts_from_zero") \
        else [1] + m.counts(hi)     # A[r] = number of objects of size r
    if off + len(T) - 1 + rowoff >= len(A):
        return dict(rec, status="refused", reason="index range out of model")
    got = [A[off + i + rowoff] for i in range(len(T))]
    if got != T:
        k = next(i for i in range(len(T)) if got[i] != T[i])
        return dict(rec, status="refused", reason="model does not reproduce data",
                    first_bad=k, model=str(got[k]), published=str(T[k]))
    bf = []
    n = 1
    while whole_ok is not None and q ** (W * n) <= BRUTE_BUDGET \
            and n <= len(T) + rowoff:
        bf.append(automaton.brute(n, W, q, whole_ok))
        n += 1
    if bf and bf != A[1:len(bf) + 1]:
        return dict(rec, status="refused", reason="brute force disagrees with model",
                    brute=[str(x) for x in bf],
                    model=[str(x) for x in A[1:len(bf) + 1]])
    out = []
    for cd in cands:
        out.append(CL.evaluate(cd, A, off, rowoff, S))
    return dict(rec, status="done", S=S, nfull=getattr(m, "nfull", S),
                ntrim=getattr(m, "ntrim", S),
                rowoff=rowoff,
                W=W, q=q, spec=fam.jsonspec(spec),
                brute_checked=len(bf),
                build_seconds=round(build_t, 2), claims=out,
                nterms=len(T), modified=mod, author=au, keywords=kw,
                revision=rev, terms=[str(x) for x in T[:12]],
                all_terms=[str(x) for x in T])


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
