#!/usr/bin/env python3
"""Sweep the `every element (un)equal to N adjacent elements' family.

Writes one record per entry, including a reason for every refusal.  The
refusal counts are the point of the run, not a by-product: they say where the
next result is.
"""
import sys, os, json, time, pickle, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus, recur, automaton, fam_neighbour as F

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def candidates(entry_conj):
    """Every conjectural line on the entry that parses as a linear recurrence."""
    out = []
    for f, i, ln in entry_conj:
        r = recur.parse_recurrence(ln)
        if r:
            out.append((f, i, ln, r))
    return out


def settle(anum, meta, terms, cj, cap=3_000_000, margin=6, tlimit=120):
    nm, off, kw, au, mod, nt, rev = meta
    rec = {"anum": anum, "name": nm, "offset": off}
    spec = F.parse(nm)
    if spec is None:
        return dict(rec, status="refused", reason="name not parsed")
    if spec["kind"] != "seq":
        return dict(rec, status="refused", reason="table entry")
    cands = candidates(cj)
    if not cands:
        return dict(rec, status="refused", reason="no parsable recurrence")
    T = list(terms)
    if len(T) < 8:
        return dict(rec, status="refused", reason="too few published terms")
    valid, first_ok, whole_ok, W, q = F.make(spec)
    if q ** W > 4096:
        return dict(rec, status="refused", reason=f"row alphabet {q}^{W} too large")
    m = automaton.Model(W, q, valid, first_ok, cap=cap)
    t0 = time.time()
    try:
        m.build()
    except automaton.TooBig as e:
        return dict(rec, status="refused", reason=str(e))
    build_t = time.time() - t0
    S = m.S
    need = len(T) + off + 4
    a = m.counts(need)                      # a[i] = model count for n = i+1
    got = [a[off + i - 1] for i in range(len(T))]
    if got != T:
        k = next(i for i in range(len(T)) if got[i] != T[i])
        return dict(rec, status="refused", reason="model does not reproduce data",
                    first_bad=k, model=got[k], published=T[k])
    out = []
    for f, i, ln, (coeffs, nmin, body) in cands:
        D = len(coeffs)
        # residual index m corresponds to the claim at n = m + D + (off-1)
        N = S + D + len(T) + margin
        u = m.residuals(coeffs, N)
        last = 0
        for j in range(len(u) - 1, -1, -1):
            if u[j] != 0:
                last = j + 1
                break
        if last and last > len(u) - S:
            out.append({"line": ln, "field": f, "idx": i, "coeffs": coeffs,
                        "nmin": nmin, "status": "inconclusive",
                        "reason": "residuals not yet all zero within bound"})
            continue
        # claim at n = m + D + off - 1 for residual index m (1-based)
        thresh_n = last + D + off - 1        # holds for all n > thresh_n
        out.append({"line": ln, "field": f, "idx": i, "coeffs": coeffs,
                    "nmin": nmin, "order": D, "threshold": thresh_n,
                    "status": "proved", "S": S})
    return dict(rec, status="done", S=S, nfull=m.nfull, ntrim=m.ntrim,
                W=W, q=q, spec_counts=spec["counts"], spec_eq=spec["eq"],
                dirname=spec["dirname"], transposed=spec["transposed"],
                build_seconds=round(build_t, 2), claims=out,
                nterms=len(T), modified=mod, author=au, keywords=kw,
                revision=rev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(DATA, "neighbour.jsonl"))
    ap.add_argument("--start", type=int, default=0)
    args = ap.parse_args()
    D = pickle.load(open(os.path.join(DATA, "index.pkl"), "rb"))
    meta, terms, conj = D["meta"], D["terms"], D["conj"]
    import re
    rx = re.compile(r"adjacent elements, with upper left element zero")
    pool = sorted(a for a in conj if rx.search(meta[a][0]))
    pool = pool[args.start:]
    if args.limit:
        pool = pool[:args.limit]
    reasons = {}
    n_proved = 0
    with open(args.out, "a") as fh:
        for a in pool:
            t0 = time.time()
            try:
                r = settle(a, meta[a], terms[a], conj[a])
            except Exception as e:
                r = {"anum": a, "status": "error", "reason": f"{type(e).__name__}: {e}"}
            r["seconds"] = round(time.time() - t0, 2)
            key = r.get("reason", r["status"])
            if r["status"] == "done":
                st = {c["status"] for c in r["claims"]}
                key = "done:" + ("proved" if "proved" in st else "inconclusive")
                n_proved += sum(1 for c in r["claims"] if c["status"] == "proved")
            reasons[key] = reasons.get(key, 0) + 1
            fh.write(json.dumps(r) + "\n")
            fh.flush()
    print(json.dumps(reasons, indent=1))
    print("claims proved:", n_proved)


if __name__ == "__main__":
    main()
