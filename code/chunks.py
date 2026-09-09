#!/usr/bin/env python3
"""What no engine here reads yet, grouped by the shape of the clause,
largest group first.  Rebuilt from the corpus every time."""
import sys, os, re, pickle, collections, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FAMS = ["fam_neighbour", "fam_avoid", "fam_marked", "fam_stress",
        "fam_perimeter", "fam_countval", "fam_digits", "fam_linesum",
        "fam_monotone", "fam_unimodal", "fam_idem", "fam_avoidrc", "fam_word1d", "fam_divrc", "fam_lexsub",
        "fam_commute", "fam_offsets", "fam_repeated", "fam_totalling",
        "fam_nopattern"]


def main(top=40, author=None):
    D = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "data", "index.pkl"), "rb"))
    meta, conj = D["meta"], D["conj"]
    mods = [importlib.import_module(f) for f in FAMS]
    covered = set()
    for m in mods:
        for a in m.pool(meta, conj):
            if m.parse(meta[a][0]):
                covered.add(a)
    c = collections.Counter()
    ex = {}
    n = 0
    for a in conj:
        if a in covered:
            continue
        nm, off, kw, au, mod, nt, rev = meta[a]
        if author and author not in au:
            continue
        n += 1
        body = nm
        m = re.match(r"^(?:T\(n,\s*k\)[^:]{0,20}?[Nn]umber of|Number of)\s+(.*)$",
                     nm, re.I)
        if m:
            b = m.group(1)
            mm = re.search(r"\b(with|having|without|such that|containing|whose|avoiding)\b", b)
            body = b[mm.start():] if mm else b
        key = re.sub(r"\d+", "#", re.sub(r"\s+", " ", body)).strip().rstrip(".")
        c[key] += 1
        ex.setdefault(key, a)
    print(f"{n} entries carry a conjecture and are not read by any family here")
    print(f"{len(c)} distinct clause shapes\n")
    for k, v in c.most_common(top):
        print(f"{v:6d}  {ex[k]}  {k[:130]}")
    return c


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else None
    main(int(os.environ.get("TOP", 40)), a)
