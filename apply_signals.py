#!/usr/bin/env python3
"""Retire #4ade80 on rnvizion.dev; land the signal register on the hero dot.

Built against rnvizion.github.io @ main, fetched 2026-08-14.
Source of truth for the values: rnv-brand/engine/brand.py WEB[] signals block.
Fails loudly if the base has moved. Run from repo root.
"""
import pathlib, sys

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

EDITS = [
    # 1. tokens
    (
        "      --accent-2: #b794ff; --accent-warm: #ffd166; --max-width: 1200px;",
        "      --accent-2: #b794ff; --accent-warm: #ffd166; --max-width: 1200px;\n"
        "      /* Brand signals: state of a thing the brand runs. Not app STATUS.\n"
        "         signal-offline/-down equal --text-faint/--accent-warm by coincidence;\n"
        "         the seam is deliberate. Do not de-duplicate. Source: engine/brand.py. */\n"
        "      --signal-live: #8b2c3b; --signal-offline: #5a5a72; --signal-down: #ffd166;",
    ),
    # 2. the availability dot
    (
        "    .hero-tag .dot { width: 6px; height: 6px; background: #4ade80; "
        "border-radius: 50%; box-shadow: 0 0 8px #4ade80; }",
        """    .hero-tag .dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--signal-live);
      /* box-shadow, not border: sits outside the box, costs no layout. This ring
         carries WCAG 1.4.11 — gold on --bg-2 is 10.15:1 at full opacity, 3.35:1 at
         breathe's dim end. The FILL is 2.37:1 and deliberately does not carry it.
         Do not remove the ring to "simplify"; without it this colour fails. */
      box-shadow: 0 0 0 1px var(--accent);
    }
    @media (prefers-reduced-motion: no-preference) {
      .hero-tag .dot { animation: breathe 3s ease-in-out infinite; }
    }
    /* breathe is NOT redundant with pulse. pulse dips to 0.4 -> ring reads 2.57:1
       and fails the 3:1 UI floor; breathe dips to 0.5 -> 3.35:1 and passes. It is
       also the animation rnv-live uses: same dot, same motion, two mediums.
       Do not merge these two keyframes. */
    @keyframes breathe { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }""",
    ),
]

for old, new in EDITS:
    n = s.count(old)
    assert n == 1, f"expected 1 match, found {n}. Base has moved:\n{old[:90]}"
    s = s.replace(old, new)

assert "#4ade80" not in s, "a #4ade80 literal survives"
P.write_text(s, encoding="utf-8")
print("index.html updated; #4ade80 retired.")
