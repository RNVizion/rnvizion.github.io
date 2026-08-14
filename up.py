#!/usr/bin/env python3
"""aiii/index.html -- stop requesting a font face this page never draws.

Built against rnvizion.github.io/aiii/index.html @ main, fetched 2026-08-14.
Fails loudly if the base has moved. Run from repo root.

WHY: this page requests Montserrat Black, defines --font-mark, and writes
var(--font-mark) zero times. It has no site nav, so there is no RNVizion
wordmark on it to set in the mark face; its own AIII wordmark is JetBrains Mono
at 700. The font file is downloaded and does nothing.

WHAT IS NOT DONE, and this is the deliberate half:

  --font-mark STAYS DEFINED. The five-token vocabulary is identical on every
  page and that is worth more than removing one unused line. Deleting it here
  would make aiii/ the one page where a developer's muscle memory silently
  produces nothing.

  Which means this page is now the site's only specimen of "defines the mark
  face, does not load it." That is not a defect left in place -- it is the
  configuration a guard should be pointed at, because the dangerous direction
  is the inverse of the one being fixed here:

    loads Montserrat, never draws it  -> wasted request, renders fine
    draws Montserrat, never loads it  -> wordmark in a fallback face, visibly wrong

  The realistic future mistake is someone building a second nav-less page,
  pasting the nav in from index.html, and not restoring this line. The comment
  added below is what they hit when they look.
"""
import pathlib

P = pathlib.Path("aiii/index.html")
s = P.read_text(encoding="utf-8")

# ------------------------------------------------------------- 1. the request
OLD_LINK = "&family=Montserrat:wght@900&display=swap"
NEW_LINK = "&display=swap"

n = s.count(OLD_LINK)
assert n == 1, f"font link: expected 1 match, found {n}. Base has moved."
s = s.replace(OLD_LINK, NEW_LINK)

# ------------------------------------------------------- 2. the standing note
OLD_TOK = "    --font-mark: 'Montserrat', system-ui, -apple-system, sans-serif;"
NEW_TOK = (
    "    /* Defined but NOT loaded on this page: the font link deliberately omits\n"
    "       Montserrat, because this page carries no site nav and therefore no\n"
    "       RNVizion wordmark to set in it. The token stays so the five-token\n"
    "       vocabulary is identical everywhere. If this page ever draws the mark,\n"
    "       restore `&family=Montserrat:wght@900` to the link IN THE SAME CHANGE --\n"
    "       using it without loading it renders the wordmark in system-ui, which\n"
    "       looks wrong on a live page rather than merely wasting a request. */\n"
    "    --font-mark: 'Montserrat', system-ui, -apple-system, sans-serif;"
)
n = s.count(OLD_TOK)
assert n == 1, f"token: expected 1 match, found {n}. Base has moved."
s = s.replace(OLD_TOK, NEW_TOK)

# ---------------------------------------------------------- post-conditions
# Scoped to the <link> element, not the file. The comment added above quotes the
# request string as the thing to restore -- a whole-file assertion counts that
# mention as if it were the request itself, which is the mention-vs-use trap
# this very change is guarding against. It caught itself here.
link_line = next(l for l in s.splitlines() if "fonts.googleapis.com/css2" in l)
assert "Montserrat" not in link_line, "the request survives in the link element"
assert "family=Inter" in link_line and "family=Bricolage" in link_line, "the link lost more than Montserrat"
assert s.count("--font-mark:") == 1, "token definition disturbed"
assert "var(--font-mark)" not in s, "this page now DRAWS the mark face it no longer loads"

P.write_text(s, encoding="utf-8")
print("aiii/index.html: Montserrat request removed, token kept and annotated")
