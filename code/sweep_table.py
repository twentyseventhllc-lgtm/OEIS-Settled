#!/usr/bin/env python3
"""Settle the per-column and per-row conjectures a table entry carries."""
import sys, os, json, time, pickle, argparse, importlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus, recur, gf, automaton, table, claims as CL
from shapes import strip_scale
from fractions import Fraction
from shapes import parse_table_shape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
BRUTE_BUDGET = 200_000


def build(fam, spec, W, transposed, cap, rowcap):
    sp = dict(spec)
    sp["W"] = W
    sp["transposed"] = transposed
    if hasattr(fam, "model"):
        return fam.model(sp), None, None, None
    valid, first_ok, whole_ok, W2, q = fam.make(sp, W=W)
    if q ** W2 > rowcap:
        raise automaton.TooBig(f"row alphabet {q}^{W2} over cap")
    up, down = (fam.REACHfor(sp) if hasattr(fam, "REACHfor")
                else getattr(fam, "REACH", (1, 1)))
    m = automaton.Model(W2, q, valid, first_ok, cap=cap, up=up, down=down)
    m.build()
    return m, whole_ok, W2, q


def settle(fam, anum, meta, terms, e, cap=3_000_000, rowcap=8192, margin=6):
    nm, off, kw, au, mod, nt, rev = meta
    rec = {"anum": anum, "name": nm, "offset": off, "family": fam.FAMILY,
           "table": True}
    divisor, nm2 = strip_scale(nm)
    rec["divisor"] = divisor
    spec = fam.parse(nm2)
    if spec is None or spec.get("kind") != "table":
        return dict(rec, status="refused", reason="not a table of this family")
    rowoff, coloff = parse_table_shape(spec["shape"])
    if rowoff is None:
        return dict(rec, status="refused", reason="table shape not read")
    T = table.unpack(list(terms), off)
    if not T:
        return dict(rec, status="refused", reason="no published terms")
    F = e.get("F", [])
    lines = table.claim_lines(F)
    if not lines:
        return dict(rec, status="refused", reason="no per-column or per-row lines")
    claims, reasons = [], {}
    cache = {}
    for which, idx, body, raw, li in lines:
        head = table.header_of(F, li)
        if head is None:
            reasons["line not under an Empirical header"] = \
                reasons.get("line not under an Empirical header", 0) + 1
            continue
        conjectural = bool(re.search(r"onjectur|Empirical", head, re.I))
        if not conjectural:
            reasons["header not conjectural"] = reasons.get("header not conjectural", 0) + 1
            continue
        want_col = (which == "k")
        if (want_col and "column" not in head.lower()) or \
           (not want_col and "row" not in head.lower()):
            reasons["line does not match its header"] = \
                reasons.get("line does not match its header", 0) + 1
            continue
        cd = CL.parse_line(raw, body=body)
        if cd is None:
            key = ("order-only" if re.match(r"^\[(same )?order \d+\]", body)
                   else "unread line")
            reasons[key] = reasons.get(key, 0) + 1
            continue
        coeffs, nmin = cd["coeffs"], cd["nmin"]
        # the sequence this line is about
        if want_col:
            W = idx + coloff
            trans = spec.get("transposed", False)
            ro = rowoff
            data = sorted((n, v) for (n, k), v in T.items() if k == idx)
        else:
            W = idx + rowoff
            trans = not spec.get("transposed", False)
            ro = coloff
            data = sorted((k, v) for (n, k), v in T.items() if n == idx)
        if len(data) < 6:
            reasons["fewer than six published terms in that line"] = \
                reasons.get("fewer than six published terms in that line", 0) + 1
            continue
        key = (W, trans)
        if key not in cache:
            try:
                cache[key] = build(fam, spec, W, trans, cap, rowcap)
            except automaton.TooBig as ex:
                cache[key] = str(ex)
        got = cache[key]
        if isinstance(got, str):
            reasons[got] = reasons.get(got, 0) + 1
            continue
        m, whole_ok, W2, q = got
        idxs = [i for i, _ in data]
        lo, hiN = min(idxs), max(idxs)
        D = max(len(coeffs), len(cd.get("poly") or []))
        need = hiN + ro + m.S + D + 40
        A = m.counts_from_zero(need) if hasattr(m, "counts_from_zero") \
            else [1] + m.counts(need)
        if divisor != 1:
            A = [Fraction(x, divisor) for x in A]
        bad = [i for i, v in data if A[i + ro] != v]
        if bad:
            reasons["model does not reproduce the published table"] = \
                reasons.get("model does not reproduce the published table", 0) + 1
            continue
        cl = CL.evaluate(cd, A, lo, ro, m.S)
        if cl["status"] != "proved":
            reasons[cl.get("reason", "inconclusive")] = \
                reasons.get(cl.get("reason", "inconclusive"), 0) + 1
            continue
        cl.update(which=which, index=idx, line=raw.strip(), header=head,
                  body=body, W=W2, seq_offset=lo, rowoff=ro,
                  transposed=trans, nfull=getattr(m, "nfull", m.S),
                  ntrim=getattr(m, "ntrim", m.S),
                  terms=[str(v) for _, v in data])
        claims.append(cl)
    if not claims:
        return dict(rec, status="refused", reason="no line settled",
                    line_reasons=reasons)
    return dict(rec, status="done", claims=claims, line_reasons=reasons,
                rowoff=rowoff, coloff=coloff, spec=fam.jsonspec(spec),
                q=spec.get("q"), nterms=len(terms), modified=mod, author=au,
                keywords=kw, revision=rev,
                all_terms=[str(x) for x in terms],
                terms=[str(x) for x in terms[:12]],
                table_cells=len(T))


def run(famname, out, limit=0, start=0):
    fam = importlib.import_module(famname)
    D = pickle.load(open(os.path.join(DATA, "index.pkl"), "rb"))
    meta, terms, conj = D["meta"], D["terms"], D["conj"]
    pool = [a for a in fam.pool(meta, conj)
            if (fam.parse(meta[a][0]) or {}).get("kind") == "table"]
    pool = sorted(pool)[start:]
    if limit:
        pool = pool[:limit]
    reasons, nclaims = {}, 0
    with open(out, "a") as fh:
        for a in pool:
            t0 = time.time()
            try:
                e = corpus.parse(a)
                r = settle(fam, a, meta[a], terms[a], e)
            except Exception as ex:
                r = {"anum": a, "family": fam.FAMILY, "status": "error",
                     "reason": f"{type(ex).__name__}: {ex}"}
            r["seconds"] = round(time.time() - t0, 2)
            k = r.get("reason", r["status"])
            if r["status"] == "done":
                k = "done"
                nclaims += len(r["claims"])
            reasons[k] = reasons.get(k, 0) + 1
            fh.write(json.dumps(r) + "\n")
            fh.flush()
    print(json.dumps(reasons, indent=1))
    print("claims proved:", nclaims)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("family")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    a = ap.parse_args()
    run(a.family, a.out, a.limit, a.start)
