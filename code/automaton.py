#!/usr/bin/env python3
"""Row-transfer automata for fixed-width array counts, and the exact
annihilation test that settles a conjectured linear recurrence.

The whole method in one line: an array of n rows is a walk of length n in a
finite digraph, so the count is C-finite of order at most the number of
states, and a proposed recurrence is decided by finitely many exact residuals.

Nothing here is approximate and nothing is sampled.
"""
import itertools


class TooBig(Exception):
    pass


class Model:
    """A width-W array count over an alphabet of q letters whose condition on a
    row is decided by that row together with the row above and the row below.

    valid(above, row, below) -> bool, where `above` / `below` are None at the
    boundary.  first_ok(row) -> bool is any extra condition on the first row
    (Hardin's `with upper left element zero').
    """

    def __init__(self, W, q, valid, first_ok=None, cap=4_000_000,
                 up=1, down=1, workcap=25_000_000):
        self.W, self.q = W, q
        self.valid, self.first_ok = valid, first_ok or (lambda r: True)
        self.cap, self.workcap = cap, workcap
        self.up, self.down = up, down
        self.rows = None
        self.built = False

    # ------------------------------------------------------------- building
    def build(self):
        if self.up + self.down == 1:
            return self._build1()
        W, q = self.W, self.q
        R = q ** W
        if R * (R + 1) > self.cap:
            raise TooBig(f"state space {R*(R+1)} > cap {self.cap}")
        if R * R * (R + 1) > self.workcap:
            raise TooBig(f"transition work {R*R*(R+1)} > cap {self.workcap}")
        rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
        self.rows = rows
        TOP = R                      # sentinel: no row above

        # state index = p * R + c, with p in 0..R (R = TOP)
        nst = (R + 1) * R
        edges = [None] * nst         # state -> list of successor states
        acc = [0] * nst              # accepting?
        start = [0] * nst            # weight of the state after reading row 1

        valid = self.valid
        for pi in range(R + 1):
            p = None if pi == R else rows[pi]
            for ci in range(R):
                c = rows[ci]
                s = pi * R + ci
                succ = []
                base = ci * R
                for xi in range(R):
                    if valid(p, c, rows[xi]):
                        succ.append(base + xi)
                edges[s] = succ
                acc[s] = 1 if valid(p, c, None) else 0
        for ci in range(R):
            if self.first_ok(rows[ci]):
                start[TOP * R + ci] = 1
        self.edges, self.acc, self.start, self.R, self.nst = edges, acc, start, R, nst
        self._trim()
        self._lump()
        self.built = True
        return self

    def _build1(self):
        """The condition reaches only one way, so a single row is a state."""
        W, q = self.W, self.q
        R = q ** W
        if R > self.cap:
            raise TooBig(f"state space {R} > cap {self.cap}")
        if R * R > self.workcap:
            raise TooBig(f"transition work {R*R} > cap {self.workcap}")
        rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
        self.rows = rows
        valid = self.valid
        edges, acc, start = [], [0] * R, [0] * R
        if self.down == 1:                     # condition looks downwards only
            for ci in range(R):
                c = rows[ci]
                edges.append([xi for xi in range(R) if valid(None, c, rows[xi])])
                acc[ci] = 1 if valid(None, c, None) else 0
                start[ci] = 1 if self.first_ok(c) else 0
        else:                                  # condition looks upwards only
            for pi in range(R):
                p = rows[pi]
                edges.append([xi for xi in range(R) if valid(p, rows[xi], None)])
                acc[pi] = 1
                start[pi] = 1 if (self.first_ok(p) and valid(None, p, None)) else 0
        self.edges, self.acc, self.start, self.R, self.nst = edges, acc, start, R, R
        self._trim()
        self._lump()
        self.built = True
        return self

    def _trim(self):
        """Keep only states reachable from a start state and able to reach an
        accepting one.  Purely an efficiency step; it changes no count."""
        nst = self.nst
        seen = [False] * nst
        stack = [s for s in range(nst) if self.start[s]]
        for s in stack:
            seen[s] = True
        while stack:
            s = stack.pop()
            for t in self.edges[s]:
                if not seen[t]:
                    seen[t] = True
                    stack.append(t)
        # co-reachable
        rev = [[] for _ in range(nst)]
        for s in range(nst):
            if seen[s]:
                for t in self.edges[s]:
                    rev[t].append(s)
        co = [False] * nst
        stack = [s for s in range(nst) if seen[s] and self.acc[s]]
        for s in stack:
            co[s] = True
        while stack:
            s = stack.pop()
            for t in rev[s]:
                if not co[t]:
                    co[t] = True
                    stack.append(t)
        keep = [s for s in range(nst) if seen[s] and co[s]]
        idx = {s: i for i, s in enumerate(keep)}
        self.tedges = [[idx[t] for t in self.edges[s] if t in idx] for s in keep]
        self.tacc = [self.acc[s] for s in keep]
        self.tstart = [self.start[s] for s in keep]
        self.nfull = self.nst
        self.ntrim = len(keep)

    def _lump(self):
        """Merge states from which the same number of arrays can be completed,
        for every remaining number of rows.  Partition refinement: two states
        stay together only while they agree on acceptance and on how many
        edges they send into each block.  The lumped digraph counts exactly
        what the original does, and its size is the degree bound used by the
        annihilation test -- so this is not tidying, it is what makes the test
        finite and small."""
        n = self.ntrim
        blk = list(self.tacc)                     # initial partition
        while True:
            sig = []
            for s in range(n):
                d = {}
                for t in self.tedges[s]:
                    b = blk[t]
                    d[b] = d.get(b, 0) + 1
                sig.append((blk[s], tuple(sorted(d.items()))))
            uniq = {}
            newblk = []
            for s in range(n):
                k = sig[s]
                if k not in uniq:
                    uniq[k] = len(uniq)
                newblk.append(uniq[k])
            if len(uniq) == len(set(blk)) and newblk == blk:
                break
            blk = newblk
            if len(uniq) == n:
                break
        nb = len(set(blk))
        rel = {}
        for b in sorted(set(blk)):
            rel[b] = len(rel)
        blk = [rel[b] for b in blk]
        L = [[0] * nb for _ in range(nb)]
        done = [False] * nb
        for s in range(n):
            b = blk[s]
            if done[b]:
                continue
            done[b] = True
            for t in self.tedges[s]:
                L[b][blk[t]] += 1
        w = [0] * nb
        for s in range(n):
            if self.tstart[s]:
                w[blk[s]] += self.tstart[s]
        accv = [0] * nb
        for s in range(n):
            accv[blk[s]] = self.tacc[s]
        self.L, self.w, self.accv, self.S = L, w, accv, nb

    # -------------------------------------------------------------- counting
    def counts(self, N):
        """a(1..N): a(n) = w^T L^(n-1) acc."""
        L, w, acc, S = self.L, self.w, self.accv, self.S
        out = []
        v = list(acc)
        for n in range(1, N + 1):
            out.append(sum(wi * vi for wi, vi in zip(w, v) if wi and vi))
            if n < N:
                v = [sum(L[i][j] * v[j] for j in range(S) if L[i][j] and v[j])
                     for i in range(S)]
        return out

    def residuals(self, coeffs, N):
        """u_m for m = 1..N, where u_m = a(m+D) - sum c_i a(m+D-i)."""
        L, w, acc, S = self.L, self.w, self.accv, self.S
        D = len(coeffs)
        # y = q(L) acc  with q(t) = t^D - sum c_i t^(D-i)
        pw = [list(acc)]
        for _ in range(D):
            v = pw[-1]
            pw.append([sum(L[i][j] * v[j] for j in range(S) if L[i][j] and v[j])
                       for i in range(S)])
        y = [pw[D][i] - sum(coeffs[k] * pw[D - 1 - k][i] for k in range(D))
             for i in range(S)]
        out = []
        v = y
        for m in range(1, N + 1):
            out.append(sum(wi * vi for wi, vi in zip(w, v) if wi and vi))
            if m < N:
                v = [sum(L[i][j] * v[j] for j in range(S) if L[i][j] and v[j])
                     for i in range(S)]
        return out


class GraphModel(Model):
    """A counting automaton whose states are arbitrary hashable objects.

    `starts' is a list of initial states, `step(state, letter)' returns the
    next state or None, `accept(state)' says whether a walk may stop there.
    The trimming, lumping, counting and residual machinery is inherited, so a
    family only has to describe its state and its step.
    """

    sentinel_start = True

    def counts_from_zero(self, N):
        """A[r] = number of objects of size r, r = 0..N.  The start state is a
        sentinel carrying no row, so a walk of length r places r rows."""
        c = self.counts(N + 1)
        return [1] + c[1:N + 1]

    def __init__(self, starts, step, accept, alphabet, cap=4_000_000,
                 workcap=25_000_000):
        self.starts, self.step, self.accept = starts, step, accept
        self.alphabet = list(alphabet)
        self.cap, self.workcap = cap, workcap
        self.built = False

    def build(self):
        idx = {}
        order = []

        def num(s):
            if s not in idx:
                idx[s] = len(order)
                order.append(s)
                if len(order) > self.cap:
                    raise TooBig(f"state space > cap {self.cap}")
            return idx[s]

        stack = []
        start = []
        for s in self.starts:
            i = num(s)
            while len(start) <= i:
                start.append(0)
            start[i] += 1
            stack.append(s)
        seen = set(self.starts)
        edges = {}
        work = 0
        while stack:
            s = stack.pop()
            e = []
            for r in self.alphabet:
                work += 1
                if work > self.workcap:
                    raise TooBig(f"transition work > cap {self.workcap}")
                t = self.step(s, r)
                if t is None:
                    continue
                num(t)
                e.append(t)
                if t not in seen:
                    seen.add(t)
                    stack.append(t)
            edges[s] = e
        n = len(order)
        self.nst = n
        self.edges = [[num(t) for t in edges[order[i]]] for i in range(n)]
        self.acc = [1 if self.accept(order[i]) else 0 for i in range(n)]
        self.start = start + [0] * (n - len(start))
        self._trim()
        self._lump()
        self.built = True
        self.nfull = n
        return self


def brute(n, W, q, whole_ok):
    """Independent count: write out every array and test the condition on the
    finished array.  No transfer matrix, no row window."""
    tot = 0
    for cells in itertools.product(range(q), repeat=n * W):
        A = [cells[i * W:(i + 1) * W] for i in range(n)]
        if whole_ok(A):
            tot += 1
    return tot
