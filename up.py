#!/usr/bin/env python3
"""Restore the registry punctuation in the post description. Reports by
default; writes only with --apply.

    python3 fix_aphorism_punctuation.py            # check: writes nothing
    python3 fix_aphorism_punctuation.py --apply    # write

Run from the rnvizion.github.io repo root.

WHAT IS WRONG
  The registered aphorism is live in three punctuations. The post body and the
  demo surfaces carry the em dash, which is the registry form. The post's
  description carries a comma:

      ...warns instead of blocking: gate what you're judging, warn about
      what you're waiting on.

  The dash is the whole point of the line -- it reverses, and the writing
  profile reserves the dash for exactly that rupture. A comma makes it a list
  of two chores.

WHY ONLY ONE FILE IS WRITTEN
  The comma appears three times: twice in this post's <head> (name="description"
  and og:description, byte-identical) and once in feed.xml. feed.xml is not a
  source -- scripts/build_feed.py line 121 reads og:description and writes it
  into <description>, and .github/workflows/build-feed.yml runs on any push
  touching blog/**. So editing the post regenerates the feed on its own, and a
  hand edit to feed.xml would be a change the next build overwrites.

  A generated surface and its generator are two artifacts and either can be the
  stale one. Here the post is the source; everything else is output.

WHAT IS NOT AFFECTED, CHECKED RATHER THAN ASSUMED
  The blog-index card reads card:summary, which this post declares, and
  generate_card.py only falls back to og:description when that tag is absent.
  The card keeps its own teaser.
  generate_og.py wraps the title only; the share image carries no description
  text, so no image needs regenerating.
  sitemap.xml carries no descriptions.

WHAT IT DELIBERATELY DOES NOT DO
  It does not commit, stage, or push. It writes one named file and reports
  every other occurrence in the repo without touching it, so a derived surface
  that appears later shows up in the report instead of being silently patched.
"""

import sys
from pathlib import Path

POST = Path("blog/the-warning-not-the-gate/index.html")

# No apostrophe in the anchor, so it matches whether the file writes the
# apostrophe as &#8217; (the post) or as a literal (the feed).
OLD = "judging, warn about"

# &#8212; rather than a literal em dash: this post already writes its closing
# aphorism that way, and its apostrophes as &#8217;. Where a file has a house
# encoding, the file's encoding wins over what looks nicer in an editor.
NEW = "judging &#8212; warn about"

EXPECTED = 2   # name="description" and og:description, byte-identical

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


def main() -> int:
    apply = "--apply" in sys.argv
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
    if not POST.is_file():
        print(f"{R}{POST} not found. Nothing written.{N}")
        return 2

    me = Path(__file__).resolve()
    src = POST.read_text(encoding="utf-8")
    n = src.count(OLD)

    # Everything else that carries the string, named and left alone.
    others = []
    for p in sorted(Path(".").rglob("*")):
        if not p.is_file() or ".git" in p.parts or p.resolve() == me or p == POST:
            continue
        if p.suffix.lower() not in (".html", ".xml", ".vtt", ".json", ".md", ".txt"):
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if OLD in s:
            others.append((p, s.count(OLD)))

    print(f"{C}== source =={N}")
    if NEW in src and n == 0:
        print(f"  {Y}{POST}{N}\n      already carries the registry form. Nothing to do.")
    elif n != EXPECTED:
        # Not a silent pass. If the count moved, the file is not shaped the way
        # this script believes it is, and a blind replace would be guessing.
        print(f"  {R}{POST}{N}")
        print(f"      found {n} occurrence(s), expected {EXPECTED}.")
        print(f"      The head should carry it twice: name=\"description\" and")
        print(f"      og:description. Nothing written; this needs a human.")
        return 1
    else:
        print(f"  {G}{POST}{N}  {n} occurrence(s) -> em dash")

    if others:
        print(f"\n{Y}== carries the string, not written ({len(others)}) =={N}")
        for p, c in others:
            print(f"  {Y}{p}{N}  x{c}")
        print(f"{D}      Generated from the post by scripts/build_feed.py. The{N}")
        print(f"{D}      build-feed workflow runs on any push under blog/**, so{N}")
        print(f"{D}      these rebuild themselves once the post lands.{N}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply to write.")
        return 0

    if n == EXPECTED:
        out = src.replace(OLD, NEW)
        assert out.count(NEW) == src.count(NEW) + EXPECTED, "replacement count moved"
        POST.write_text(out, encoding="utf-8")
        print(f"\n{G}wrote{N}  {POST}")

    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
