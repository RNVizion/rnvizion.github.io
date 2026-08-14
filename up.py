#!/usr/bin/env python3
"""Hero signal dot, pass 3: fill 8px -> 10px. Ring unchanged at 1px.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-14, with
apply_signals.py, dot_pass2.py and signal_live_value.py already landed. Fails
loudly otherwise. Run from repo root.

The ring gets thinner by the fill getting bigger; 1px is the floor, because a
sub-pixel ring renders on retina and disappears on a 1x display. Ring-to-
footprint goes 1:10 -> 1:12.

CEILING, so the next pass does not overshoot: .hero-tag sets font-size 12px,
so its line box is roughly 14px. A dot footprint under that rides inside the
existing pill height. At 10px fill + 1px ring the footprint is 12px and the
pill does not move. Past about 13px of fill the dot starts driving the pill's
height instead of the text, and the pill grows.

WHY THIS HAS DIMINISHING RETURNS, worth knowing before a pass 4: the ring reads
strong for a reason geometry cannot fix. Gold on --bg-2 is 10.15:1; the wine
fill is 2.43:1. The bright element dominates a small mark regardless of how
much area the dim one occupies. Growing the fill narrows the ratio but does not
change which one the eye goes to. The alternative lever is dimming the ring,
and that is the one to refuse: it is the only thing carrying WCAG 1.4.11 here,
and it clears 3:1 with margin only at full opacity.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

assert ".hero-tag .dot::after" in s, "dot_pass2.py has not landed; run it first"

OLD = "      width: 8px; height: 8px; border-radius: 50%;\n      background: transparent;"
NEW = "      width: 10px; height: 10px; border-radius: 50%;\n      background: transparent;"

n = s.count(OLD)
assert n == 1, f"expected 1 match, found {n}. Either already applied or the base has moved."
s = s.replace(OLD, NEW)

dot_rule = s[s.index(".hero-tag .dot {"):s.index(".hero-tag .dot::after")]
assert "width: 10px" in dot_rule, "the size did not land on the dot rule"
assert "0 0 0 1px var(--accent)" in dot_rule, "the ring was disturbed"

P.write_text(s, encoding="utf-8")
print("hero dot: fill 8px -> 10px, ring still 1px, footprint 12px")
