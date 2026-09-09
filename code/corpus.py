#!/usr/bin/env python3
"""Read the OEIS internal-format corpus (github.com/oeis/oeisdata) from disk.

Everything in this project is measured against this corpus, never against a
cached candidate list.  One entry -> one dict of raw lines, keyed by the
internal-format letter.
"""
import os, re, functools

SEQDIR = os.environ.get("OEIS_SEQ", "/Users/gaspardm/conjectures/oeis/oeisdata/seq")

FIELD_RE = re.compile(r"^%(.) (A\d{6})\s?(.*)$")


def path(anum):
    return os.path.join(SEQDIR, anum[:4], anum + ".seq")


def exists(anum):
    return os.path.exists(path(anum))


def all_anums():
    """Every A-number present in the clone, in order."""
    out = []
    for d in sorted(os.listdir(SEQDIR)):
        p = os.path.join(SEQDIR, d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            if f.endswith(".seq"):
                out.append(f[:-4])
    return out


def parse(anum):
    """Return {letter: [line, ...]} for one entry, or None if absent."""
    p = path(anum)
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except FileNotFoundError:
        return None
    d = {}
    for line in raw.split("\n"):
        m = FIELD_RE.match(line)
        if not m:
            continue
        d.setdefault(m.group(1), []).append(m.group(3))
    d["_id"] = anum
    return d


def name(e):
    return " ".join(e.get("N", [])) if e else ""


def keywords(e):
    return set(",".join(e.get("K", [])).split(",")) if e and e.get("K") else set()


def offset(e):
    o = e.get("O", [""])[0]
    try:
        return int(o.split(",")[0])
    except (ValueError, IndexError):
        return 0


def author(e):
    a = e.get("A", [""])
    return a[0] if a else ""


def terms(e):
    """The entry's own published terms, in order.  Ground truth."""
    s = "".join(e.get("S", []) + e.get("T", []) + e.get("U", []))
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(int(tok))
        except ValueError:
            return out
    return out


# ---------------------------------------------------------------- conjectures

CONJ_WORDS = re.compile(
    r"onjectur|Empirical|empirical|mpirically|[Ii]t appears|[Aa]ppears to|"
    r"[Aa]ppears that|[Ss]eems to|[Ss]eems that|[Ww]e believe|[Ii]s believed|"
    r"[Pp]robably|[Gg]uess|[Uu]nproved|[Uu]nproven|[Nn]ot yet proved|"
    r"[Nn]o proof|[Hh]ypothes|[Ss]urmise|[Aa]pparently")

BLOCK_START = re.compile(
    r"(onjectur\w*|Empirical\w*|[Ff]ormulas? from|[Ii]t appears)[^:]{0,80}:?\s*\(Start\)",
    re.I)
BLOCK_START2 = re.compile(r"\(Start\)\s*$")
BLOCK_END = re.compile(r"\(End\)")

# fields that can carry a mathematical claim
CLAIM_FIELDS = ("F", "C", "e", "N")


def _scan_field(lines):
    """Yield (index, line, in_conj_block) over one field's lines.

    A `Conjectures from X: (Start)' block makes every line inside it
    conjectural, and none of those lines carries a conjectural word.  Reading
    such a line as a statement of fact is the single most expensive mistake
    available here; this is the function that stops it.
    """
    inblock = False
    block_is_conj = False
    for i, ln in enumerate(lines):
        starts = bool(BLOCK_START.search(ln)) or (
            BLOCK_START2.search(ln) and bool(CONJ_WORDS.search(ln)))
        plain_start = BLOCK_START2.search(ln) and not starts
        if starts:
            inblock, block_is_conj = True, True
            yield i, ln, True
            if BLOCK_END.search(ln):
                inblock = block_is_conj = False
            continue
        if plain_start:
            inblock, block_is_conj = True, False
            yield i, ln, False
            if BLOCK_END.search(ln):
                inblock = block_is_conj = False
            continue
        yield i, ln, inblock and block_is_conj
        if inblock and BLOCK_END.search(ln):
            inblock = block_is_conj = False


def conj_lines(e, fields=CLAIM_FIELDS):
    """Every line of the entry that is conjectural: by its own wording, or by
    sitting inside a conjecture block."""
    out = []
    for f in fields:
        for i, ln, inblk in _scan_field(e.get(f, [])):
            if inblk or CONJ_WORDS.search(ln):
                out.append((f, i, ln))
    return out


def fact_lines(e, fields=("F",)):
    """Lines that may be used as a PREMISE.  A line qualifies only when it is
    not conjectural by wording AND is not inside a conjecture block.  Nothing
    else may ever be used as a premise."""
    out = []
    for f in fields:
        for i, ln, inblk in _scan_field(e.get(f, [])):
            if inblk or CONJ_WORDS.search(ln):
                continue
            out.append((f, i, ln))
    return out


def is_conjectural(e, field, idx):
    for f, i, _ in conj_lines(e, (field,)):
        if i == idx:
            return True
    return False
