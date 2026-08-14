#!/usr/bin/env python3
"""font.sh header repair.

Built against rnvizion.github.io/font.sh @ main, fetched 2026-08-14 (179 lines,
6207 bytes). Fails loudly if the base has moved. Run from repo root.

Four edits. The first three are accuracy; the fourth is a latent bug the first
three would have triggered.

  1. Name all three generators. The file's argument is "a repo carries the faces
     it renders." That only holds if a reader can find out what renders. Naming
     one of three is how someone later concludes a face is unused.

  2. Say that all three read the same OG_FONT_DIR, so nobody wonders whether the
     override has to be set per-generator.

  3. Pre-empt the false finding. Grepping scripts/ for "Instrument" hits
     generate_contact_card.py and contradicts the header on its face. It is not
     a missing font -- that generator emits HTML and links Google Fonts, so the
     browser fetches the face and nothing opens a .ttf. Verified 2026-08-14:
     generate_og.py, generate_site_og.py and generate_project_card.py each load
     exactly the three files below; generate_contact_card.py opens none.

  4. --help was `sed -n '2,20p'`, a hardcoded range over a header these very
     edits lengthen. It would have started printing a truncated slice, and kept
     exiting 0 while doing it. Replaced with an awk that prints the leading
     comment block and stops at the first non-comment line -- computed, not
     counted, so the next person to add a paragraph does not silently break it.

     BEHAVIOUR CHANGE, deliberate: help now also prints the variable-font
     paragraph, which was outside the old range. It explains the instance check
     the user is about to watch run, so it belongs in help.
"""
import pathlib

P = pathlib.Path("font.sh")
s = P.read_text(encoding="utf-8")

EDITS = [
    # ------------------------------------------------ 1. all three consumers
    (
        "# The OG image pipeline (scripts/generate_og.py) renders with these faces and\n"
        "# silently falls back to a default face if they're missing, so a missing font\n"
        "# shows up as an ugly card rather than an error. This script makes the fetch\n"
        "# explicit and verifies what it downloaded.",
        "# Three generators render with these faces \u2014 scripts/generate_og.py,\n"
        "# scripts/generate_site_og.py and scripts/generate_project_card.py \u2014 and each\n"
        "# silently falls back to a default face if they're missing, so a missing font\n"
        "# shows up as an ugly card rather than an error. This script makes the fetch\n"
        "# explicit and verifies what it downloaded.",
    ),
    # ----------------------------------------------------- 2. the override
    (
        "# Target directory honours OG_FONT_DIR, the same override generate_og.py reads.",
        "# Target directory honours OG_FONT_DIR; all three generators read the same\n"
        "# override, so setting it for one and not the others is not a failure mode.",
    ),
    # --------------------------------------------- 3. pre-empt the false finding
    (
        "# here in the same change that makes a generator draw it, never before.\n"
        "#\n"
        "# All three are variable fonts.",
        "# here in the same change that makes a generator draw it, never before.\n"
        "#\n"
        "# Grepping scripts/ for \"Instrument\" hits generate_contact_card.py. That is not\n"
        "# a missing font: the card generator emits HTML and links Google Fonts, so the\n"
        "# browser fetches the face and nothing needs a .ttf on disk. Web pages take five\n"
        "# faces over the network; the raster pipeline takes three off the disk. Two\n"
        "# delivery paths, and only this one needs files.\n"
        "#\n"
        "# All three are variable fonts.",
    ),
    # ----------------------------------------- 4. --help, computed not counted
    (
        "    -h|--help) sed -n '2,20p' \"$0\" | sed 's/^# \\{0,1\\}//'; exit 0 ;;",
        "    # Prints the leading comment block and stops at the first non-comment line.\n"
        "    # Do not put a line range here: the previous version was `sed -n '2,20p'`,\n"
        "    # which quietly truncated help the moment the header grew past line 20 and\n"
        "    # still exited 0. Help that is wrong and confident is worse than no help.\n"
        "    -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/,\"\"); print; next} NR>1 {exit}' \"$0\"; exit 0 ;;",
    ),
]

for i, (old, new) in enumerate(EDITS, 1):
    n = s.count(old)
    assert n == 1, f"edit {i}: expected 1 match, found {n}. Base has moved:\n{old[:90]}"
    s = s.replace(old, new)

# ------------------------------------------------------------ post-conditions
for gen in ("generate_og.py", "generate_site_og.py", "generate_project_card.py"):
    assert gen in s, f"{gen} not named in header"
# Scoped to the executable line. The comment above it quotes `sed -n '2,20p'` as
# the thing being retired, and a whole-file check counts that mention as if it
# were still the code. Same trap as BRAND_COLORS.md line 318: assert on the line
# that DOES something, never on the file that describes it.
help_line = next(l for l in s.splitlines() if "-h|--help)" in l)
assert "sed -n" not in help_line, "the help case still counts lines"
assert "awk" in help_line, "the help case did not take the awk"
assert s.count("-h|--help)") == 1, "help case disturbed"

P.write_text(s, encoding="utf-8")
print("font.sh header repaired; --help no longer counts lines")
