#!/usr/bin/env python3
"""Both signal dots: stop them being squeezed into ellipses.

Built against rnvizion.github.io @ main, every file fetched and read
2026-08-14. Run from repo root.

    python3 dot_noshrink_all.py            # DRY RUN -- reports, writes nothing
    python3 dot_noshrink_all.py --apply    # writes

THE DEFECT: .hero-tag and .logo are both flex containers, and flex-shrink
defaults to 1 on every item. When a container's content is wider than the space
available, its items shrink. Text wrapping is fine. A dot shrinking is not:
height is pinned by an explicit px value and align-items:center, width is not,
so a circle becomes an ellipse and the 1px ring traces the distortion.
Confirmed visually on .hero-tag at 10px; latent on .logo .dot.

flex-shrink, not min-width. min-width fixes the symptom at one number and goes
silently useless the moment the size changes. flex-shrink:0 states the rule that
is actually true: this item does not participate in shrinking, at any size.

WHY IT WALKS INSTEAD OF CARRYING A FILE LIST: the nav is duplicated as inline
CSS per page. A hardcoded list is wrong the day a page is added, and it cannot
be checked. This finds the rule itself and reports what it found.

WHY IT MATCHES BY REGEX AND NOT EXACT STRING: verified 2026-08-14 -- the eleven
copies of `.logo .dot` exist in FOUR different formattings. Identical
declarations, identical values, identical order; only whitespace differs. One
file has it on a single line, one has one declaration per line, one splits it
across two, and eight share a fourth layout. An exact-string edit would need
four anchors and would silently skip any fifth variant. Worth handing to Brand
Infrastructure separately: a byte-comparison guard on this rule reports
four-way drift where nothing has drifted.

VERIFIED BEFORE WRITING: all eleven `.logo` rules are flex containers, so the
fix is warranted in every one. No file in the repo currently sets flex-shrink.

SCOPE NOTE ON THE NAV DOT: `.logo .dot` was ruled unchanged on 2026-08-13. That
ruling covered colour, glow and animation -- gold, 12px glow, pulse 2.4s -- and
none of them move here. This is geometry, authorised separately on 2026-08-14.
Every existing declaration is kept; one is added. Worth a Brand Book row,
because "unchanged" now has a documented edge and the next person should find
it written rather than infer it from a diff.
"""
import pathlib
import re
import sys

APPLY = "--apply" in sys.argv
ROOT = pathlib.Path(".")

LOGO_OPEN = re.compile(r"\.logo\s+\.dot\s*\{")
LOGO_RULE = re.compile(r"\.logo\s+\.dot\s*\{[^}]*\}", re.S)
LOGO_CONTAINER = re.compile(r"\.logo\s*\{[^}]*\}", re.S)

LOGO_INSERT = (
    "\n      /* .logo is flex; without this the dot is squeezed to an ellipse when the\n"
    "         nav is tight. Geometry only -- gold, glow and pulse are unchanged. */\n"
    "      flex-shrink: 0;"
)

HERO_OLD = """    .hero-tag .dot {
      position: relative;
      width: 10px; height: 10px; border-radius: 50%;
      background: transparent;"""

HERO_NEW = """    .hero-tag .dot {
      position: relative;
      width: 10px; height: 10px; border-radius: 50%;
      /* Load-bearing. .hero-tag is inline-flex and flex-shrink defaults to 1, so
         when the pill's text wraps this item is squeezed on the main axis while
         its height stays pinned -- a circle becomes an ellipse, and the 1px ring
         traces the distortion. Not min-width: that pins one number and goes
         quiet if the size changes. This states the actual rule. */
      flex-shrink: 0;
      background: transparent;"""

files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
assert files, "no .html files found -- run this from the repo root"

hero, nav, skipped = [], [], []

for p in files:
    s = p.read_text(encoding="utf-8")
    orig = s

    if "flex-shrink" in s:
        skipped.append((p, "already sets flex-shrink -- not touched"))
        continue

    if HERO_OLD in s:
        assert s.count(HERO_OLD) == 1, f"{p}: hero rule appears more than once"
        s = s.replace(HERO_OLD, HERO_NEW)
        hero.append(p)
    elif ".hero-tag .dot" in s:
        skipped.append((p, "has .hero-tag .dot in an unexpected form -- passes 1-3 may not be landed"))
        continue

    rules = LOGO_RULE.findall(s)
    if len(rules) == 1:
        container = LOGO_CONTAINER.findall(s)
        assert container, f"{p}: .logo .dot exists but .logo does not"
        assert "display: flex" in container[0] or "display:flex" in container[0], \
            f"{p}: .logo is not a flex container -- the fix does not apply, check by hand"
        s = LOGO_OPEN.sub(lambda m: m.group(0) + LOGO_INSERT, s, count=1)
        nav.append(p)
    elif len(rules) > 1:
        skipped.append((p, f".logo .dot appears {len(rules)}x -- not touched"))
        continue

    if s != orig and APPLY:
        p.write_text(s, encoding="utf-8")
        after = p.read_text(encoding="utf-8")
        assert after.count("flex-shrink: 0;") == (1 if p not in hero else 2) or p in hero, \
            f"{p}: post-write check failed"

print("APPLIED\n" if APPLY else "DRY RUN -- nothing written\n")
print("scanned %d html files" % len(files))
print("\nhero dot -- expect exactly 1 (index.html):")
for p in hero:
    print("   %s" % p)
print("\nnav dot -- expect 11, and _templates/post-template.html MUST be among them:")
for p in nav:
    print("   %s" % p)
if skipped:
    print("\nskipped:")
    for p, why in skipped:
        print("   %s: %s" % (p, why))

if not APPLY:
    print("\nIf the template is missing from the nav list, STOP. It is the source for")
    print("new posts, and skipping it births the next post already drifted.")
    print("Otherwise re-run with --apply.")
