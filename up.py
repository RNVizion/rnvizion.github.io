#!/usr/bin/env python3
"""Hero signal dot: add a fill-coloured glow. TRIAL, not a ruling.

Built against rnvizion.github.io/index.html @ main, fetched 2026-08-16.
Fails loudly if the base has moved. Run from repo root.
Reverting is one line: drop the second shadow layer.

WHAT THIS IS: a 12px glow in --signal-live, matching the nav mark dot's blur
radius. Added to look at, not because anything ruled it. The comment below says
so in those words -- a trial described in the voice of a ruling is a claim
wearing confidence it has not earned, and the next reader cannot tell them
apart.

IT REVERSES A RECORDED DECISION, deliberately and knowingly. On 2026-08-13 the
hero dot's glow was removed on the reasoning that "a ring plus a glow is two
treatments doing one job, and the ring is the one carrying contrast." The
retired glow was `0 0 8px #4ade80` -- fill-coloured, which is the precedent this
follows. If the trial sticks, it needs a Brand Book decision row saying the 08-13
reasoning was reconsidered; if it does not, nothing was ruled and nothing needs
retracting.

THE RING IS UNTOUCHED AND STAYS FIRST IN THE LIST. Shadow layers paint in order,
first on top, so the gold ring paints above the glow and stays crisp. That is
load-bearing rather than tidy: the ring is the only element carrying WCAG 1.4.11
here, at 6.09:1, and a blurred wine glow bleeding across it would tint the one
value the component's accessibility rests on. A glow cannot take that job at any
radius -- blur means partial coverage, and partial coverage has no single
contrast value to carry.

THE GLOW DOES NOT BREATHE, AND THAT IS A CHOICE TO REVISIT AFTER LOOKING. The
fill lives on .dot::after and animates; this glow lives on .dot and does not, so
the halo holds while its source dims. Physically that is backwards -- a light
source that dims should dim its own halo. It is done this way because making it
breathe means either painting the glow over the ring (::after paints above .dot's
shadow) or adding a ::before layer behind, and neither is worth building before
knowing whether the glow is wanted at all. Expect the mismatch to be invisible:
#a5034e is 2.43:1 on --bg-2, so a blurred instance of it on near-black may barely
register. That is the actual open question this trial answers.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

OLD = "      box-shadow: 0 0 0 0.75px var(--accent);"
NEW = (
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

n = s.count(OLD)
assert n == 1, f"expected 1 match, found {n}. Base has moved."
s = s.replace(OLD, NEW)

# The ring must remain the first layer and must remain 0.75px gold.
decl = next(l for l in s.splitlines() if "0 0 12px var(--signal-live)" in l)
assert decl.index("0 0 0 0.75px var(--accent)") < decl.index("0 0 12px var(--signal-live)"), \
    "the glow is painting above the ring"
assert "flex-shrink: 0;" in s, "the circle fix was disturbed"
assert s.count("0 0 12px var(--accent)") == 1, "the nav dot's glow was touched"

P.write_text(s, encoding="utf-8")
print("hero dot: wine glow added as a trial; ring unchanged and still on top")
