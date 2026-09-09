#!/usr/bin/env python3
"""Build the working index straight from the OEIS clone.

Rebuilt from the corpus every time; never read back from a saved candidate
list.  Produces data/index.pkl:

    anums   : list of every A-number in the clone
    meta    : anum -> (name, offset, keywords, author, modified, nterms)
    terms   : anum -> tuple of published terms
    conj    : anum -> list of (field, idx, line) conjectural lines
    facts   : anum -> list of (field, idx, line) usable premises (%F only)
"""
import os, pickle, sys, re
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus

SEQ = corpus.SEQDIR
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

MOD_RE = re.compile(r"#(\d+) (\w{3} \d{2} \d{4}) ")


def modified(e):
    for ln in e.get("I", []):
        m = MOD_RE.search(ln)
        if m:
            return m.group(2)
    return ""


def revision(e):
    for ln in e.get("I", []):
        m = MOD_RE.search(ln)
        if m:
            return int(m.group(1))
    return 0


def do_dir(d):
    p = os.path.join(SEQ, d)
    meta, terms, conj, facts = {}, {}, {}, {}
    for f in sorted(os.listdir(p)):
        if not f.endswith(".seq"):
            continue
        a = f[:-4]
        e = corpus.parse(a)
        if e is None:
            continue
        t = corpus.terms(e)
        meta[a] = (corpus.name(e), corpus.offset(e),
                   ",".join(sorted(corpus.keywords(e))), corpus.author(e),
                   modified(e), len(t), revision(e))
        terms[a] = tuple(t)
        c = corpus.conj_lines(e)
        if c:
            conj[a] = c
            facts[a] = corpus.fact_lines(e)
    return meta, terms, conj, facts


def main():
    dirs = sorted(x for x in os.listdir(SEQ) if os.path.isdir(os.path.join(SEQ, x)))
    meta, terms, conj, facts = {}, {}, {}, {}
    with Pool(8) as pool:
        for i, (m, t, c, fa) in enumerate(pool.imap(do_dir, dirs)):
            meta.update(m); terms.update(t); conj.update(c); facts.update(fa)
            if i % 50 == 0:
                print(f"  {i}/{len(dirs)} dirs, {len(meta)} entries", flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "index.pkl"), "wb") as fh:
        pickle.dump({"anums": sorted(meta), "meta": meta, "terms": terms,
                     "conj": conj, "facts": facts}, fh, protocol=4)
    print(f"entries {len(meta)}  with-conjecture {len(conj)}")


if __name__ == "__main__":
    main()
