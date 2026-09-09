#!/usr/bin/env python3
"""Rewrite the \\author{} line of every paper source and recompile the PDF.

Used when the authorship of the work changes: the sources are edited in place
so that every paper carries the same author line, and every PDF is rebuilt
from its own source.
"""
import os, re, sys, glob, subprocess, argparse
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import paper                                          # noqa: E402

SOURCES = os.path.join(ROOT, "paper-sources")
PAPERS = os.path.join(ROOT, "papers")
AUTHOR_RE = re.compile(r"^\\author\{.*\}$", re.M)


def fix(src):
    with open(src) as fh:
        tex = fh.read()
    new = AUTHOR_RE.sub("\\\\author{" + paper.AUTHOR + "}", tex, count=1)
    changed = new != tex
    if changed:
        with open(src, "w") as fh:
            fh.write(new)
    stem = os.path.basename(src)[:-4]
    pdf = os.path.join(PAPERS, stem + ".pdf")
    cmd = ["tectonic", "-X", "compile", src, "--outdir", PAPERS,
           "-Z", "continue-on-errors"]
    r = subprocess.run(cmd[:4] + ["--only-cached"] + cmd[4:],
                       capture_output=True, text=True, timeout=300)
    if not os.path.exists(pdf):
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return (stem, os.path.exists(pdf), changed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    srcs = sorted(glob.glob(os.path.join(SOURCES, "*.tex")))
    print(f"{len(srcs)} sources; author line -> {paper.AUTHOR}")
    ok = bad = 0
    fails = []
    with ProcessPoolExecutor(a.workers) as ex:
        for i, (stem, built, ch) in enumerate(ex.map(fix, srcs, chunksize=4)):
            if built:
                ok += 1
            else:
                bad += 1
                fails.append(stem)
            if (i + 1) % 500 == 0:
                print(f"  {i+1}/{len(srcs)} rebuilt {ok} failed {bad}", flush=True)
    print(f"rebuilt {ok}, failed {bad}")
    for s in fails[:40]:
        print("  failed:", s)


if __name__ == "__main__":
    main()
