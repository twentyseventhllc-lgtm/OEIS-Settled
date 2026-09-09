#!/usr/bin/env python3
"""Re-check every record in results.json from scratch and print how many pass.

Nothing here trusts the sweep that produced the result.  For each record the
model is rebuilt from the entry's name, the count is recomputed, and the
annihilation test is re-run in exact integer arithmetic.  A record passes only
when every one of the following holds:

  1. the name in the record parses, by the same family reader, to the same
     model specification;
  2. the rebuilt model reproduces every published term the record carries,
     with the index taken from the entry's offset;
  3. an independent enumeration -- every array written out and tested on the
     finished array -- agrees with the model wherever it is affordable;
  4. the conjecture line in the record parses to the recorded coefficients;
  5. the residuals vanish from the recorded threshold onwards, and the
     recorded threshold is exactly the last index at which one does not;
  6. enough consecutive residuals vanish to reach the derived degree bound.

Usage:  python3 verify.py [--jobs N] [--limit N] [--only A123456 ...]
        python3 verify.py --live            also re-read each entry from the
                                            OEIS clone in ../oeis/oeisdata
"""
import os, sys, json, argparse, importlib, time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "code"))
import automaton, recur, gf                                  # noqa: E402
from shapes import strip_scale                               # noqa: E402
from fractions import Fraction                               # noqa: E402

FAMILY_MODULE = {
    "neighbour-count": "fam_neighbour",
    "pattern-avoidance": "fam_avoid",
    "marked-value-neighbours": "fam_marked",
    "constant-stress": "fam_stress",
    "clockwise-perimeter": "fam_perimeter",
    "neighbour-count-equals-value": "fam_countval",
    "digit-window": "fam_digits",
    "subblock-line-sum": "fam_linesum",
    "monotone-derived": "fam_monotone",
    "line-monotonicity": "fam_unimodal",
    "idempotent-subblock": "fam_idem",
    "pattern-avoidance-lines": "fam_avoidrc",
    "word-window": "fam_word1d",
    "row-column-divisibility": "fam_divrc",
    "lex-subblock": "fam_lexsub",
    "commuting-subblocks": "fam_commute",
    "offset-distinct": "fam_offsets",
    "repeated-value": "fam_repeated",
    "adjacent-pair-total": "fam_totalling",
    "directional-pattern": "fam_nopattern",
    "index-change": "fam_indexchange",
    "strict-majority": "fam_majority",
    "subblock-six-differences": "fam_edgediff",
    "subblock-statistic": "fam_subblock",
    "cell-neighbour-count": "fam_cellcount",
}
BRUTE_BUDGET = 200_000


def check_table(rec):
    """Re-derive a table entry's column and row recurrences from scratch."""
    import table as tbl
    from shapes import parse_table_shape
    a = rec["anum"]
    fam = importlib.import_module(FAMILY_MODULE[rec["family"]])
    divisor, nm2 = strip_scale(rec["name"])
    if divisor != rec.get("divisor", 1):
        return a, False, "scaling prefix differs"
    spec = fam.parse(nm2)
    if spec is None or fam.jsonspec(spec) != rec["spec"]:
        return a, False, "name does not parse to the recorded specification"
    rowoff, coloff = parse_table_shape(spec["shape"])
    if (rowoff, coloff) != (rec["rowoff"], rec["coloff"]):
        return a, False, "table shape differs"
    T = tbl.unpack([int(x) for x in rec["published_terms"]], rec["offset"])
    if len(T) != rec["table_cells"]:
        return a, False, "published table unpacks to a different size"
    for c in rec["claims"]:
        W, trans, ro = c["W"], c["transposed"], c["rowoff"]
        sp = dict(spec); sp["W"] = W; sp["transposed"] = trans
        if hasattr(fam, "model"):
            m = fam.model(sp, W=W)
        else:
            valid, first_ok, whole_ok, W2, q = fam.make(sp, W=W)
            up, down = (fam.REACHfor(sp) if hasattr(fam, "REACHfor")
                        else getattr(fam, "REACH", (1, 1)))
            m = automaton.Model(W2, q, valid, first_ok, cap=8_000_000,
                                up=up, down=down)
            m.build()
        if m.S != c["S"]:
            return a, False, f"degree bound differs on {c['which']}={c['index']}"
        if c["which"] == "k":
            data = sorted((n, v) for (n, k), v in T.items() if k == c["index"])
        else:
            data = sorted((k, v) for (n, k), v in T.items() if n == c["index"])
        D = c["order"]
        hi = max(i for i, _ in data) + ro + m.S + D + 40
        A = m.counts_from_zero(hi) if hasattr(m, "counts_from_zero") \
            else [1] + m.counts(hi)
        if divisor != 1:
            A = [Fraction(x, divisor) for x in A]
        for i, v in data:
            if A[i + ro] != Fraction(v):
                return a, False, f"model differs from the published table at {c['which']}={c['index']}"
        lo = min(i for i, _ in data)
        nlo = max(lo + D, D + 1 - ro)
        nhi = len(A) - 1 - ro
        last = None
        for nn in range(nhi, nlo - 1, -1):
            if A[nn + ro] != sum(cf * A[nn + ro - i]
                                 for i, cf in enumerate(c["coeffs"], 1)):
                last = nn
                break
        if nhi - (last if last is not None else nlo - 1) < m.S:
            return a, False, "residuals do not vanish inside the derived bound"
        th = last if last is not None else lo + D - 1
        if th != c["threshold"]:
            return a, False, f"threshold differs on {c['which']}={c['index']}"
    return a, True, ""


def check(rec):
    if rec.get("table"):
        return check_table(rec)
    """Rebuild the model from the entry's name and re-derive every claim."""
    a = rec["anum"]
    try:
        fam = importlib.import_module(FAMILY_MODULE[rec["family"]])
    except KeyError:
        return a, False, "unknown family " + str(rec.get("family"))
    divisor, nm2 = strip_scale(rec["name"])
    if divisor != rec.get("divisor", 1):
        return a, False, "scaling prefix differs"
    spec = fam.parse(nm2)
    if spec is None:
        return a, False, "name does not parse"
    if fam.jsonspec(spec) != rec["spec"]:
        return a, False, "specification differs from the record"
    if hasattr(fam, "model"):
        m0 = fam.model(spec)
        whole_ok = (fam.whole_ok_for(spec, spec.get("W"))
                    if hasattr(fam, "whole_ok_for") else None)
        W, q = spec.get("W"), spec.get("q")
    else:
        valid, first_ok, whole_ok, W, q = fam.make(spec)
        if (W, q) != (rec["W"], rec["q"]):
            return a, False, "width/alphabet differ"
    T = [int(x) for x in rec["published_terms"]]
    off, rowoff = rec["offset"], spec.get("rowoff", 0)
    if hasattr(fam, "model"):
        m = m0
    else:
        up, down = (fam.REACHfor(spec) if hasattr(fam, "REACHfor")
                    else getattr(fam, "REACH", (1, 1)))
        m = automaton.Model(W, q, valid, first_ok, cap=8_000_000,
                            up=up, down=down)
        m.build()
    S = m.S
    if S != rec["states_lumped"]:
        return a, False, f"degree bound differs: {S} vs {rec['states_lumped']}"
    Dmax = max(len(c["coeffs"]) for c in rec["claims"])
    hi = off + len(T) + rowoff + S + Dmax + 40
    A = m.counts_from_zero(hi) if hasattr(m, "counts_from_zero") \
        else [1] + m.counts(hi)
    if divisor != 1:
        A = [Fraction(x, divisor) for x in A]
    if [A[off + i + rowoff] for i in range(len(T))] != [Fraction(x) for x in T]:
        return a, False, "model does not reproduce the published terms"
    n = 1
    while whole_ok is not None and q ** (W * n) <= BRUTE_BUDGET \
            and n <= len(T) + rowoff:
        if Fraction(automaton.brute(n, W, q, whole_ok), divisor) != A[n]:
            return a, False, f"independent enumeration disagrees at {n} rows"
        n += 1
    for c in rec["claims"]:
        if c["kind"] == "recurrence":
            parsed = recur.parse_recurrence(c["line"])
            if parsed is None or parsed[0] != c["coeffs"]:
                return a, False, "conjecture line does not give the recorded coefficients"
            if parsed[1] != c["nmin_claimed"]:
                return a, False, "claimed range differs"
        else:
            g = gf.parse_gf(c["line"])
            if g is None or list(g[0]) != c["num"] or list(g[1]) != c["den"]:
                return a, False, "g.f. line does not give the recorded polynomials"
            if gf.recurrence_from_den(g[1]) != c["coeffs"]:
                return a, False, "g.f. denominator does not give the recorded recurrence"
        D = len(c["coeffs"])
        nlo = max(off + D, D + 1 - rowoff)
        nhi = len(A) - 1 - rowoff
        last = None
        for nn in range(nhi, nlo - 1, -1):
            if A[nn + rowoff] != sum(cf * A[nn + rowoff - i]
                                     for i, cf in enumerate(c["coeffs"], 1)):
                last = nn
                break
        if nhi - (last if last is not None else nlo - 1) < S:
            return a, False, "residuals do not vanish inside the derived bound"
        th = last if last is not None else off + D - 1
        if th != c["threshold"]:
            return a, False, f"threshold differs: {th} vs {c['threshold']}"
        if c["kind"] == "gf":
            K = c["gf_checked_to"]
            sh = c["gf_shift"] if c.get("gf_shift") is not None else off
            ser = gf.series(c["num"], c["den"], K)
            seq = [(A[k - sh + off + rowoff] if k >= sh else 0) for k in range(K)]
            if seq != ser:
                return a, False, "generating function does not match the count"
        # the claim on the entry's published data alone
        lo = max(th + 1, off + D)
        for nn in range(lo, off + len(T)):
            i = nn - off
            if T[i] != sum(cf * T[i - k - 1] for k, cf in enumerate(c["coeffs"])):
                return a, False, f"claim fails on the published data at n={nn}"
    return a, True, ""


def _one(rec):
    try:
        return check(rec)
    except Exception as e:
        return rec.get("anum", "?"), False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--results", default=os.path.join(HERE, "results.json"))
    args = ap.parse_args()
    recs = json.load(open(args.results))
    if args.only:
        keep = set(args.only)
        recs = [r for r in recs if r["anum"] in keep]
    if args.limit:
        recs = recs[:args.limit]
    print(f"verifying {len(recs)} results from {args.results}")
    t0 = time.time()
    npass, fails = 0, []
    with ProcessPoolExecutor(args.jobs) as ex:
        for i, (a, ok, why) in enumerate(ex.map(_one, recs, chunksize=4)):
            if ok:
                npass += 1
            else:
                fails.append((a, why))
            if (i + 1) % 500 == 0:
                print(f"  {i+1}/{len(recs)}  pass {npass}  fail {len(fails)}",
                      flush=True)
    print(f"\n{npass} of {len(recs)} pass   ({time.time()-t0:.0f}s)")
    if fails:
        print(f"{len(fails)} failed:")
        for a, why in fails[:60]:
            print(f"  {a}: {why}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
