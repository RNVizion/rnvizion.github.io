#!/usr/bin/env python3
"""post-template.html: BRAND_WEB_CODE -> BRAND_TEAL. Two comments, nothing else.

Built against rnvizion.github.io/_templates/post-template.html @ main, read
2026-09-15. Run from repo root.

    python3 rename.py            # DRY RUN
    python3 rename.py --apply

Scope is exactly what Brand Infrastructure specified: two edits, the constant
name, and nothing else. A wider version was built and rejected -- it removed the
constant reference entirely and dropped the register-owned ratios. That is a
house-style call about this template and the narrow fix is the one chosen.

WHAT IS NOT BEING CHANGED, so it is not re-raised as an oversight:

  The ratios at line 61 stay. They re-measure correct -- 6.3277 on --bg-3,
  14.96px -- and they are owned by BRAND_COLORS.md. Pointing at the register
  instead of restating them is the durable form and is worth doing on the next
  substantive edit to this block, not as a pass of its own.

  The constant is still named here at all. That is the coupling no check can
  see: verify_tokens compares var(--rnv-*) against the emitted set, so it reads
  token names and not constant names, and no check reads prose in another
  repository. **Renaming keeps that trap armed for the next rename.** Recorded
  rather than fixed, because scope was the call and this is what the call costs.

ONE NUANCE THE SWAP INTRODUCES, worth knowing rather than fixing silently. Line
61 will read "Registered as BRAND_TEAL 2026-09-12". The VALUE was registered that
day; the NAME arrived on 2026-09-13. The sentence does not claim otherwise and
most readers take it as the value's registration date -- but if you want it
exact, "registered 2026-09-12, renamed BRAND_TEAL 2026-09-13" is five more words
and makes the history legible. Left plain, per the narrow scope.

STILL OUT OF REACH: `the-warning-not-the-gate` is not on main. Its working copy
carries the same stale name at line 40 and needs the same edit before
republication.
"""
import pathlib
import sys

APPLY = "--apply" in sys.argv
P = pathlib.Path("_templates/post-template.html")

assert P.exists(), "run from the repo root"
s = P.read_text(encoding="utf-8")
assert "BRAND_WEB_CODE" in s, "already renamed, or the base has moved"

EDITS = [
    ("      /* Inline code. Registered as BRAND_WEB_CODE 2026-09-12 and emitted",
     "      /* Inline code. Registered as BRAND_TEAL 2026-09-12 and emitted"),
    ("       upstream as BRAND_WEB_CODE and emitted there as --rnv-code. It used to say",
     "       upstream as BRAND_TEAL and emitted there as --rnv-code. It used to say"),
]

for i, (old, new) in enumerate(EDITS, 1):
    n = s.count(old)
    assert n == 1, f"edit {i}: expected 1 anchor, found {n}. Base has moved."

if not APPLY:
    print("both anchors found. DRY RUN -- nothing written.")
    print("re-run with --apply.")
    sys.exit(0)

for old, new in EDITS:
    s = s.replace(old, new)
P.write_text(s, encoding="utf-8")

after = P.read_text(encoding="utf-8")
assert "BRAND_WEB_CODE" not in after, "the retired constant survives"
assert after.count("BRAND_TEAL") == 2, "expected exactly the two renamed mentions"
# Everything else in the block is untouched: the token, the rule, the figures.
assert after.count("--code: #00b0a0;") == 1, "the token declaration was disturbed"
assert after.count("color: var(--code);") == 1, "the code rule was disturbed"
for figure in ("6.3277", "7.2588", "14.96px", "0.93"):
    assert figure in after, f"{figure} was removed; this pass changes names only"

print("post-template.html: BRAND_WEB_CODE -> BRAND_TEAL, two comments.")
print("  nothing else touched -- token, rule and figures all unchanged.")
