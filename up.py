#!/usr/bin/env python3
"""Track the wordmark in the three raster generators. BRAND_TYPE.md rev 3.

Built against rnvizion.github.io @ main, all three generators fetched and read
2026-08-16. Fails loudly if any base has moved. Run from repo root.

THE RULING (BRAND_TYPE.md rev 3, 2026-08-15): raster marks carry an absolute
1.8px gap. The web keeps its em values. All three generators drew the mark with
a single draw.text() call, which is zero tracking, while every web surface
tracks it -- so the same wordmark had two letterforms depending on where someone
met it, and the OG image is the highest-reach artifact in the ecosystem.

PIL has no letter-spacing, so tracking is drawn per glyph. That has one real
consequence worth stating: per-glyph drawing loses kerning pairs. Measured
against the shipped Montserrat variable font at weight 900, the mark's advance
sum exceeds its kerned single-call width by 0.20px at 20px and 0.30px at 30px.
Both are under a third of a pixel and neither is worth defeating; they are
recorded so the next person measuring does not treat the gap as a bug.

WIDTHS, MEASURED RATHER THAN DERIVED (real font, weight 900, 7 gaps):

    20px   98.55px -> 111.35px   (+13.0%)
    30px  147.81px -> 160.71px   (+8.7%)

The handoff's width table gave the 30px row as 148 -> 167. That is 0.09em
arithmetic (30 x 0.09 = 2.7px x 7 = 18.9), but the ruling puts both 30px
generators at the 0.06em equivalent. Corrected here to the measured value.
Reported back rather than silently fixed.

NOTHING NEEDS RE-MEASURING BESIDE THE MARK. The handoff cautioned that a 12%
width change moves anything laid out against it. Checked in all three: every
right-aligned element anchors to the canvas edge (W - MARGIN - dw), and nothing
measures the mark. The caution is sound in general and has no consumer here.

WHY THE CONSTANT IS LOCAL: these generators mirror brand values rather than
importing them -- BG, GOLD and TEXT are already local constants carrying their
source token in a comment. The tracking constant follows the same pattern and
names its source the same way.
"""
import pathlib
import re

ROOT = pathlib.Path("scripts")

HELPER = '''

# Mark tracking: 1.8px absolute, ruled for all raster surfaces in
# BRAND_TYPE.md rev 3 (2026-08-15). Absolute rather than em because an em value
# exists so tracking scales with type size, and a raster mark has no type size
# to scale with -- the generator fixes it and the image renders at that size
# forever. Expressed as 0.09em at 20px and 0.06em at 30px, which is how each
# generator happens to reach the same optical gap, not the reason for it.
MARK_TRACK = 1.8


def draw_tracked(d, xy, text, font, fill, gap=MARK_TRACK):
    """Draw text with an absolute per-gap tracking value; return drawn width.

    PIL has no letter-spacing, so each glyph is placed and advanced by hand.
    This loses kerning pairs: measured on Montserrat Black, the advance sum runs
    0.20px wide of the kerned single-call width at 20px and 0.30px at 30px.
    Under a third of a pixel, recorded so it is not mistaken for a defect.
    """
    x, y = xy
    last = len(text) - 1
    for i, ch in enumerate(text):
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font)
        if i < last:
            x += gap
    return x - xy[0]
'''

TARGETS = [
    (
        "generate_site_og.py",
        '    d.text((MARGIN + 2 * dot_r + 12, MARGIN), "RNVizion", font=mark_f, fill=GOLD)',
        '    draw_tracked(d, (MARGIN + 2 * dot_r + 12, MARGIN), "RNVizion", mark_f, GOLD)',
    ),
    (
        "generate_og.py",
        '    d.text((MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", font=mark, fill=TEXT)',
        '    draw_tracked(d, (MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", mark, TEXT)',
    ),
    (
        "generate_project_card.py",
        '    d.text((MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", font=mark, fill=TEXT)',
        '    draw_tracked(d, (MARGIN + 2 * dot_r + 14, MARGIN), "RNVizion", mark, TEXT)',
    ),
]

# The wrong comment in generate_site_og.py. Replaced rather than amended: both
# of its sentences are false, and the second is false in a way that would
# survive a patch -- it dismisses a figure that was never the ruled one.
OLD_COMMENT = '''    # wordmark: gold dot + RNVizion (Montserrat Black, Brand Book #15).
    # Case and tracking match the nav and /card/; the old " ".join() ran ~0.6em
    # against the ruled +0.033em, which at 20px is sub-pixel, so no tracking.'''

NEW_COMMENT = '''    # wordmark: gold dot + RNVizion (Montserrat Black, Brand Book #15).
    # Case AND tracking match the web surfaces as of BRAND_TYPE.md rev 3: 1.8px
    # absolute, which at this 20px mark is the 0.09em the nav carries.
    #
    # The comment replaced here claimed the ruled value was +0.033em and that it
    # was sub-pixel at 20px, so no tracking was applied. The ruled value was
    # 0.09em; +0.033em had already been superseded. The conclusion outlived its
    # reasoning because the reasoning read confident and cited a real number --
    # what found it was checking the value the comment NAMED against the value
    # actually ruled, not re-deriving the conclusion.'''


def patch(name, old, new):
    p = ROOT / name
    s = p.read_text(encoding="utf-8")
    assert "def draw_tracked" not in s, f"{name}: helper already present"

    n = s.count(old)
    assert n == 1, f"{name}: expected 1 mark-drawing call, found {n}. Base has moved."
    s = s.replace(old, new)

    # place the helper after the last module-level constant block, before the
    # first def -- matched structurally so it survives reordering above it
    m = re.search(r"^def ", s, re.M)
    assert m, f"{name}: no module-level def to anchor the helper above"
    s = s[: m.start()].rstrip("\n") + "\n" + HELPER + "\n\n" + s[m.start() :]

    # Checked as two specific things rather than as a count: a count is
    # perturbed by any prose that mentions the name, which is the trap that
    # bit three separate guards on 2026-08-14.
    assert "def draw_tracked(" in s, f"{name}: helper definition did not land"
    assert new in s, f"{name}: tracked call did not land"
    assert "MARK_TRACK = 1.8" in s, f"{name}: constant did not land"
    p.write_text(s, encoding="utf-8")
    return name


done = [patch(*t) for t in TARGETS]

# the comment, only in generate_site_og.py
p = ROOT / "generate_site_og.py"
s = p.read_text(encoding="utf-8")
n = s.count(OLD_COMMENT)
assert n == 1, f"comment: expected 1 match, found {n}. Base has moved."
s = s.replace(OLD_COMMENT, NEW_COMMENT)
assert "+0.033em, which at 20px is sub-pixel" not in s, "the wrong claim survives as an assertion"
assert "claimed the ruled value was +0.033em" in s, "the correction did not land"
p.write_text(s, encoding="utf-8")

for name in done:
    print(f"tracked: scripts/{name}")
print("comment replaced in scripts/generate_site_og.py")
