#!/usr/bin/env python3
"""Build one paper per settled conjecture: LaTeX source and PDF.

Section 1 quotes the conjecture exactly as the entry writes it, with the
contributor and date the entry gives, and records that the entry was still
carrying it as an open conjecture at the revision named.  A paper is as long
as its result needs.
"""
import os, re, subprocess, textwrap

AUTHOR = "Adrian Perez Fontelles, Independent researcher"

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=1.1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,citecolor=blue}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\setlength{\parskip}{2pt}
"""

TEXSPECIAL = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
              "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
              "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"}


def esc(s):
    return "".join(TEXSPECIAL.get(c, c) for c in str(s))


def verb(s):
    """Quote an OEIS line verbatim, in a form LaTeX can set."""
    s = s.replace("_", "")           # OEIS marks names with underscores
    return esc(s)


class Paper:
    def __init__(self, title, ident):
        self.title = title
        self.ident = ident
        self.body = []

    def section(self, t):
        self.body.append(r"\section{" + t + "}")

    def par(self, t):
        self.body.append(t)

    def display(self, t):
        self.body.append(r"\[" + t + r"\]")

    def raw(self, t):
        self.body.append(t)

    def itemize(self, items):
        self.body.append(r"\begin{itemize}")
        for it in items:
            self.body.append(r"\item " + it)
        self.body.append(r"\end{itemize}")

    def tex(self, date):
        return (PREAMBLE
                + "\\title{" + self.title + "}\n"
                + "\\author{" + AUTHOR + "}\n"
                + "\\date{" + date + "}\n"
                + "\\begin{document}\n\\maketitle\n"
                + "\n\n".join(self.body)
                + "\n\\end{document}\n")


def build(tex, outdir, stem, keep_tex_dir=None):
    os.makedirs(outdir, exist_ok=True)
    src = os.path.join(keep_tex_dir or outdir, stem + ".tex")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w") as fh:
        fh.write(tex)
    r = subprocess.run(["tectonic", "-X", "compile", "--only-cached", src,
                        "--outdir", outdir, "-Z", "continue-on-errors"],
                       capture_output=True, text=True, timeout=180)
    pdf = os.path.join(outdir, stem + ".pdf")
    return os.path.exists(pdf), r.stderr[-800:] if not os.path.exists(pdf) else ""
