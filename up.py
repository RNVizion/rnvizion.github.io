#!/usr/bin/env python3
"""Hero signal dot: thin the ring from 1px to 0.75px.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-14, with
every prior dot pass landed. Fails loudly otherwise. Run from repo root.
Reversible in one edit -- change 0.75px back to 1px and restore the sentence.

WHAT IS BEING SPENT, measured through rnv-color-mcp rather than estimated.
Sub-pixel box-shadow spread antialiases; partial coverage is optically the same
as reduced opacity, so a fractional ring costs contrast in proportion:

    1px    #d2bc93 on --bg-2   10.15:1   3.4x the 3:1 UI floor
    0.75px #a19174             6.09:1    2x the floor        <- this
    0.5px  #726656             3.35:1    bare pass, no margin

0.75px is the thinnest that keeps real margin. 0.5px was rejected: the ring is
the ONLY thing carrying WCAG 1.4.11 here -- the fill is 2.43:1 and deliberately
does not -- so taking the load-bearing element to the floor to save a quarter
pixel is the wrong trade.

THE COMMENT CHANGES WITH THE VALUE, and that is the point of doing both in one
edit. The line being replaced claims "1px is the floor: sub-pixel rings vanish
on a 1x display." That was overstated -- they antialias, they do not vanish --
and leaving it in place would have the file arguing against what it does.
Retire a phrase in the same change that makes it stale.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

OLD = """         not carry it. Do not remove the ring to "simplify"; without it this
         colour fails. 1px is the floor: sub-pixel rings vanish on a 1x display. */
      box-shadow: 0 0 0 1px var(--accent);"""

NEW = """         not carry it. Do not remove the ring to "simplify"; without it this
         colour fails.

         0.75px, not 1px, and not 0.5px. Sub-pixel spread antialiases rather
         than vanishing, and partial coverage costs contrast in proportion:
         1px reads 10.15:1, 0.75px reads 6.09:1, 0.5px reads 3.35:1 -- a bare
         pass with no margin. This is the only element carrying WCAG 1.4.11 on
         this component, so it keeps 2x the floor rather than sitting on it.
         Measured through rnv-color-mcp, not estimated. */
      box-shadow: 0 0 0 0.75px var(--accent);"""

n = s.count(OLD)
assert n == 1, f"expected 1 match, found {n}. Base has moved or a prior pass is missing."
s = s.replace(OLD, NEW)

assert "1px is the floor" not in s, "the overstated claim survives"
assert "0 0 0 0.75px var(--accent)" in s, "the thinner ring did not land"
assert s.count("box-shadow: 0 0 0 1px var(--accent)") == 0, "a 1px ring survives on the hero dot"
assert "flex-shrink: 0;" in s, "the circle fix was disturbed"

P.write_text(s, encoding="utf-8")
print("hero dot ring: 1px -> 0.75px, comment corrected")
