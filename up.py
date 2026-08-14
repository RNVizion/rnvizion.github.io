#!/usr/bin/env python3
"""Hero signal dot, pass 2: the ring stops breathing and the fill grows.

Built against rnvizion.github.io @ main AFTER apply_signals.py, fetched
2026-08-14. Fails loudly if apply_signals hasn't run or the base has moved.
Run from repo root.

WHAT CHANGES AND WHY IT IS AN ACCESSIBILITY GAIN, NOT A COST:

Pass 1 animated the whole element, so the gold ring dimmed with the fill. That
is the only reason `breathe` had to bottom out at 0.5 -- at 0.4 the ring read
2.57:1 and dropped under the 3:1 UI floor for part of every cycle.

Splitting the fill onto ::after means the ring never moves. It sits at 10.15:1
on --bg-2 permanently, so the boundary is perceivable at every frame instead of
at its worst frame. The dim-end constraint that governed the keyframe is gone.

`breathe`'s values are UNCHANGED, deliberately: rnv-live uses the same 0.5->1.0
curve and the two dots are meant to read as one mark. The dip is now an
aesthetic choice rather than a floor -- see the note at the bottom of this file
if the fill reads too empty at the dim end.

Sizing: 6px -> 8px fill, ring stays 1px. "Thinner ring" is achieved by growing
the fill, not by shrinking the stroke; 1px is the smallest ring that renders
crisply on a 1x display, and sub-pixel values disappear there entirely.
Footprint goes 8px -> 10px. .hero-tag is inline-flex, align-items center,
gap 10px, so nothing reflows.
"""
import pathlib

P = pathlib.Path("index.html")
s = P.read_text(encoding="utf-8")

OLD = """    .hero-tag .dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--signal-live);
      /* box-shadow, not border: sits outside the box, costs no layout. This ring
         carries WCAG 1.4.11 \u2014 gold on --bg-2 is 10.15:1 at full opacity, 3.35:1 at
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
    @keyframes breathe { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }"""

NEW = """    /* Two elements on purpose. The ring is the component's static chrome and the
       fill is the state; separating them is what lets the fill breathe while the
       boundary holds still. Do not put the fill back on .dot to "simplify" \u2014 that
       re-couples the ring to the animation and re-imposes a floor on the keyframe. */
    .hero-tag .dot {
      position: relative;
      width: 8px; height: 8px; border-radius: 50%;
      background: transparent;
      /* box-shadow, not border: sits outside the box, costs no layout. This ring
         carries WCAG 1.4.11 \u2014 gold on --bg-2, 10.15:1, and it never dims, so the
         boundary holds at every frame. The FILL is 2.37:1 and deliberately does
         not carry it. Do not remove the ring to "simplify"; without it this
         colour fails. 1px is the floor: sub-pixel rings vanish on a 1x display. */
      box-shadow: 0 0 0 1px var(--accent);
    }
    .hero-tag .dot::after {
      content: ""; position: absolute; inset: 0;
      border-radius: 50%;
      background: var(--signal-live);
    }
    @media (prefers-reduced-motion: no-preference) {
      .hero-tag .dot::after { animation: breathe 3s ease-in-out infinite; }
    }
    /* breathe is NOT redundant with pulse, and the reason changed on 2026-08-14.
       It used to be a floor: the ring animated too, and pulse's 0.4 dip put it at
       2.57:1, under the 3:1 UI minimum. The ring no longer animates, so that
       constraint is retired \u2014 breathe survives because rnv-live uses this exact
       curve and the two dots are meant to read as one mark. Parity, not physics.
       Still do not merge them: pulse is nav chrome, breathe is a signal. */
    @keyframes breathe { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }"""

n = s.count(OLD)
assert n == 1, (
    f"expected 1 match, found {n}. Either apply_signals.py has not run, "
    "or this block has already been changed."
)
s = s.replace(OLD, NEW)

assert s.count(".hero-tag .dot::after") == 2, "fill pseudo-element not wired to both rule and animation"
assert "#4ade80" not in s, "retired green reappeared"

P.write_text(s, encoding="utf-8")
print("hero dot: fill 6px -> 8px, ring static, animation moved to ::after")

# ---------------------------------------------------------------------------
# IF THE DIM END READS TOO EMPTY:
# At opacity 0.5 the wine composites to #4e1e2a over --bg-2, which is 1.38:1 --
# nearly the pill's own colour, so the dot reads as a hollow gold ring at the
# bottom of each cycle. That is now safe (the ring holds the boundary) but it may
# not be what you want to look at. Raising the dip to 0.65 gives #60222f and keeps
# the wine legible throughout. One character, in the keyframe:
#     @keyframes breathe { 0%, 100% { opacity: 0.65; } 50% { opacity: 1; } }
# If you take it, take it on rnv-live in the same pass or the two marks diverge.
