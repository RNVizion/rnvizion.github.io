#!/usr/bin/env python3
"""rnvizion.dev :root -- land signal-live at #a5034e.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-14, with
apply_signals.py and dot_pass2.py already landed. Fails loudly otherwise.
Run from repo root.

The value moved at the source on 2026-08-14, checked against STATUS.error rather
than on taste: CIEDE2000 18.22 against #dc3545, where the retired value was
17.40. The error red was always this value's nearest neighbour, and the move
toward magenta widened the gap rather than closing it. Re-measured here through
rnv-color-mcp rather than taken from the handoff.

Contrast on bg-2 goes 2.37:1 -> 2.43:1. Immaterial: the ring carries WCAG
1.4.11 at 10.15:1 and, since the split, does so at every frame. The fill has
never been asked to carry it.

Lowercase, matching engine/brand.py, which was standardised the same day. A
case-sensitive comparison reads the two forms as different colours, and the
source is what surfaces get compared against.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

assert ".hero-tag .dot::after" in s, "dot_pass2.py has not landed; run it first"

OLD = "      --signal-live: #8b2c3b; --signal-offline: #5a5a72; --signal-down: #ffd166;"
NEW = "      --signal-live: #a5034e; --signal-offline: #5a5a72; --signal-down: #ffd166;"

n = s.count(OLD)
assert n == 1, f"expected 1 match, found {n}. Either already applied or the base has moved."
s = s.replace(OLD, NEW)

assert "#8b2c3b" not in s, "retired value survives somewhere else in the file"
P.write_text(s, encoding="utf-8")
print("index.html: signal-live -> #a5034e")
