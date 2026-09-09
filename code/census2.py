#!/usr/bin/env python3
import pickle, re, collections, os
D = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "index.pkl"), "rb"))
conj = D["conj"]; meta = D["meta"]

def norm(nm):
    s = re.sub(r"\d+", "#", nm)
    s = re.sub(r"\s+", " ", s).strip()
    return s

pre = collections.Counter()
for a in conj:
    nm = meta[a][0]
    pre[" ".join(norm(nm).split()[:5])] += 1
print("=== first-5-words of the NAME, entries carrying a conjecture")
for k, v in pre.most_common(45):
    print(f"{v:7d}  {k}")
