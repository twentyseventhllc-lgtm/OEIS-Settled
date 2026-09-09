#!/usr/bin/env python3
"""How many distinct CONDITION templates cover the Hardin array names?"""
import pickle, re, collections, os
D = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "index.pkl"), "rb"))
conj = D["conj"]; meta = D["meta"]

ARRAY = re.compile(r"^(T\(n,k\)\s*=\s*)?Number of ", re.I)

def cond(nm):
    """Strip the shape prefix, leaving the condition clause."""
    s = nm
    m = re.match(r"^(?:T\(n,k\)\s*=\s*)?Number of\s+(.*)$", s, re.I)
    if not m:
        return None
    body = m.group(1)
    # cut at the first 'with', 'having', 'without', 'such that'
    m2 = re.search(r"\b(with|having|without|such that|containing|whose)\b", body)
    if not m2:
        return None
    return body[m2.start():]

def tmpl(s):
    s = re.sub(r"\d+", "#", s)
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    return s

c = collections.Counter()
hardin = 0
for a in conj:
    nm, off, kw, au, mod, nt, rev = meta[a]
    if "Hardin" not in au:
        continue
    hardin += 1
    cd = cond(nm)
    if cd is None:
        c["<no condition clause>"] += 1
    else:
        c[tmpl(cd)] += 1

print(f"Hardin entries with a conjecture: {hardin}")
print(f"distinct condition templates: {len(c)}")
tot = 0
cum = 0
vals = c.most_common()
for i, (k, v) in enumerate(vals):
    cum += v
    if i < 30:
        print(f"{v:6d} {cum:7d}  {k[:150]}")
print("...")
for n in (50, 100, 200, 400, 800, 1600, 3200):
    s = sum(v for _, v in vals[:n])
    print(f"top {n:5d} templates cover {s:6d} entries ({100*s/hardin:.1f}%)")
