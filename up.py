#!/usr/bin/env python3
"""Hero dot comment: correct two figures the value changes left behind.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-14 with
every dot pass landed. Fails loudly if the base has moved. Run from repo root.

Comment-only. No declaration changes, nothing renders differently.

TWO STALE FIGURES, both left by changes made earlier today:

  "The FILL is 2.37:1"  -> 2.43:1. That was #8b2c3b's ratio on --bg-2; the
  value moved to #a5034e and the number did not follow.

  "gold on --bg-2, 10.15:1"  -> 6.09:1. That was the 1px ring. The paragraph
  SIX LINES BELOW already says 0.75px reads 6.09:1, so this comment has been
  carrying two figures for the same value, disagreeing with itself.

That second one is the third instance of this pattern today -- brand.py line
124 against 131, BRAND_COLORS.md line 139 against 256, and now this. Each time
a value moved, the sentence that stated it got updated and a sentence that
mentioned it in passing did not. **The mention is always the one that survives,
because the person editing is looking at the declaration.**

Also drops "the 1px ring" from the flex-shrink comment above: true when the
ellipse was found, misleading now that the ring is 0.75px, and the sentence
does not need the number to make its point.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

EDITS = [
    (
        "         its height stays pinned -- a circle becomes an ellipse, and the 1px ring\n"
        "         traces the distortion.",
        "         its height stays pinned -- a circle becomes an ellipse, and the ring\n"
        "         traces the distortion.",
    ),
    (
        "      /* box-shadow, not border: sits outside the box, costs no layout. This ring\n"
        "         carries WCAG 1.4.11 \u2014 gold on --bg-2, 10.15:1, and it never dims, so the\n"
        "         boundary holds at every frame. The FILL is 2.37:1 and deliberately does\n"
        "         not carry it.",
        "      /* box-shadow, not border: sits outside the box, costs no layout. This ring\n"
        "         carries WCAG 1.4.11 \u2014 gold on --bg-2 at 6.09:1, and it never dims, so the\n"
        "         boundary holds at every frame. The FILL is 2.43:1 and deliberately does\n"
        "         not carry it.",
    ),
]

for i, (old, new) in enumerate(EDITS, 1):
    n = s.count(old)
    assert n == 1, f"edit {i}: expected 1 match, found {n}. Base has moved:\n{old[:80]}"
    s = s.replace(old, new)

# The 1px and 10.15:1 figures survive exactly once each, in the paragraph that
# compares the three ring weights. That is a mention of a retired value in a
# sentence about retired values, which is correct and must not be swept.
assert s.count("2.37:1") == 0, "stale fill ratio survives"
assert s.count("10.15:1") == 1, f"expected 10.15:1 once (the comparison), found {s.count('10.15:1')}"
assert "1px reads 10.15:1, 0.75px reads 6.09:1" in s, "the comparison paragraph was disturbed"
assert s.count("0 0 0 0.75px var(--accent)") == 1, "the ring declaration changed"
assert s.count("flex-shrink: 0;") == 2, "a flex-shrink declaration was lost"

P.write_text(s, encoding="utf-8")
print("hero dot comment: fill 2.37 -> 2.43, ring 10.15 -> 6.09")
