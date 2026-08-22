#!/usr/bin/env python3
"""Hero signal dot: move the glow onto the fill, in front of the ring, breathing.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-16 with the
2026-08-16 glow trial landed. Fails loudly otherwise. Run from repo root.

ONE MOVE, BOTH REQUESTS. The glow leaves .dot's shadow list and joins .dot::after:

  - IN FRONT: .dot's box-shadow paints with its background; ::after is a
    positioned descendant and paints above it. Moving the glow to ::after puts
    it over the ring without reordering anything.
  - BREATHING: ::after already carries `animation: breathe`, so the glow now
    dims with the fill for free. That is also the physically right behaviour --
    a light source that dims should dim its own halo -- and it removes the
    mismatch the trial shipped with.

A WARNING I WROTE IS BEING RETIRED IN THE SAME CHANGE, because it was
overstated. The trial's comment said the layer order was load-bearing and the
ring must stay on top, on the reasoning that a blurred wine bleeding across it
would tint the value carrying WCAG 1.4.11. The tinting is real; the severity
was not. Composited and measured through rnv-color-mcp:

    glow at full opacity   ring reads #bd6873   4.82:1
    glow at breathe's dim   ring reads #c79283   7.03:1

Worst case is 1.6x the 3:1 UI floor, at every frame. The ring's effective value
is now coupled to the animation, which the 2026-08-14 ring/fill split was done
to prevent -- but that split mattered because the ring was dipping to 2.57:1,
UNDER the floor. Coupling above the floor is a different fact from coupling
through it, and the old comment did not distinguish them. **A caution stated at
the wrong strength gets ignored wholesale the first time someone measures it.**

THIS IS NO LONGER A TRIAL. The 2026-08-13 removal of the hero dot's glow is
reversed. That reasoning -- "a ring plus a glow is two treatments doing one job,
and the ring is the one carrying contrast" -- turns out to hold only if the two
treatments are the same colour. Gold ring plus wine glow are two treatments
doing two jobs: the ring carries the boundary, the glow carries presence. Needs
a Brand Book decision row.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

# ---------------------------------------------- 1. ring back to a single layer
OLD_RING = (
    "      /* TRIAL, added 2026-08-16, not ruled: a fill-coloured glow at the nav\n"
    "         dot's 12px radius, to be judged on the live site. The 2026-08-13\n"
    "         removal of the previous glow (`0 0 8px #4ade80`) reasoned that a ring\n"
    "         plus a glow is two treatments doing one job; this reopens that.\n"
    "         Revert by deleting the second layer.\n"
    "\n"
    "         ORDER IS LOAD-BEARING: shadow layers paint first-on-top, so the ring\n"
    "         stays above the glow and stays crisp. Do not reorder -- the ring is\n"
    "         the only element carrying WCAG 1.4.11 on this component, and a\n"
    "         blurred wine bleeding across it would tint the value that carries it. */\n"
    "      box-shadow: 0 0 0 0.75px var(--accent), 0 0 12px var(--signal-live);"
)
NEW_RING = (
    "      /* The glow lives on ::after, not here. It has to paint in FRONT of this\n"
    "         ring, and a positioned descendant paints above its parent's shadow --\n"
    "         so moving it there does the layering without reordering anything, and\n"
    "         it inherits the breathe animation as a side effect.\n"
    "\n"
    "         The ring does tint under it: 4.82:1 at the glow's full opacity, 7.03:1\n"
    "         at breathe's dim end, measured. Both clear the 3:1 UI floor, worst case\n"
    "         by 1.6x, so this ring's effective value is coupled to the animation and\n"
    "         that is FINE. The 2026-08-14 split decoupled them because the ring was\n"
    "         dipping to 2.57:1, under the floor. Coupling above the floor and\n"
    "         coupling through it are different facts. */\n"
    "      box-shadow: 0 0 0 0.75px var(--accent);"
)
n = s.count(OLD_RING)
assert n == 1, f"ring: expected 1 match, found {n}. The trial may not be landed."
s = s.replace(OLD_RING, NEW_RING)

# ------------------------------------------------------- 2. glow onto the fill
OLD_AFTER = (
    "    .hero-tag .dot::after {\n"
    '      content: ""; position: absolute; inset: 0;\n'
    "      border-radius: 50%;\n"
    "      background: var(--signal-live);\n"
    "    }"
)
NEW_AFTER = (
    "    .hero-tag .dot::after {\n"
    '      content: ""; position: absolute; inset: 0;\n'
    "      border-radius: 50%;\n"
    "      background: var(--signal-live);\n"
    "      /* Glow, same 12px radius the nav mark dot uses. It sits here rather than\n"
    "         on .dot for two reasons at once: this element paints above the parent's\n"
    "         ring, and it is the element that breathes -- so the halo dims with its\n"
    "         own source instead of holding while the fill fades. Reverses the\n"
    "         2026-08-13 removal of this dot's glow; see the Brand Book row. */\n"
    "      box-shadow: 0 0 12px var(--signal-live);\n"
    "    }"
)
n = s.count(OLD_AFTER)
assert n == 1, f"::after: expected 1 match, found {n}. Base has moved."
s = s.replace(OLD_AFTER, NEW_AFTER)

# ------------------------------------------------------------ post-conditions
ring_line = next(l for l in s.splitlines() if "0 0 0 0.75px var(--accent)" in l)
assert "signal-live" not in ring_line, "the glow is still on the ring's shadow list"
assert s.count("box-shadow: 0 0 12px var(--signal-live);") == 1, "glow did not land exactly once"
assert s.count("0 0 12px var(--accent)") == 1, "the nav dot's glow was touched"
assert "ORDER IS LOAD-BEARING" not in s, "the overstated caution survives"
assert "flex-shrink: 0;" in s, "the circle fix was disturbed"

P.write_text(s, encoding="utf-8")
print("hero dot: glow moved to ::after -- in front of the ring, breathing with the fill")
