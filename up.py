#!/usr/bin/env python3
"""Restore the registry form of row 18 in the post description. Reports by
default; writes only with --apply.

    python3 fix_aphorism_punctuation.py            # check: writes nothing
    python3 fix_aphorism_punctuation.py --apply    # write

Run from the rnvizion.github.io repo root.

WHAT IS WRONG
  Brand Book section 5, row 18, registers the line as:

      Gate what you're judging -- warn about what you're waiting on.

  Capital G, em dash, lowercase "warn" after it. The post body carries that
  form. The post's description does not -- it lowercases the G and uses a
  comma:

      ...warns instead of blocking: gate what you're judging, warn about
      what you're waiting on.

  Both differences are restored in one edit, because they are one quotation.
  The dash is the point of the line: it reverses, and the writing profile
  reserves the dash for exactly that rupture. A comma makes it a list of two
  chores.

WHY THE CAPITAL SURVIVES A COLON
  Written out, it looks like a mistake -- ordinary prose lowercases after a
  colon, which is presumably how it drifted. A registered line is quoted, not
  absorbed: it keeps its own capitalization wherever it appears, or the
  register is describing something the surfaces do not say. Recorded here so
  the next reader does not helpfully lowercase it back.

WHY ONLY ONE FILE IS WRITTEN
  The old form appears three times: twice in this post's <head>
  (name="description" and og:description, byte-identical) and once in
  feed.xml. feed.xml is not a source -- scripts/build_feed.py line 121 reads
  og:description and writes it into <description>, and build-feed.yml runs on
  any push touching blog/**. Editing the post regenerates the feed on its own,
  and a hand edit to feed.xml is a change the next build overwrites.

  A generated surface and its generator are two artifacts and either can be
  the stale one. Here the post is the source; everything else is output.

WHAT IS NOT AFFECTED, CHECKED BY RUNNING THE GENERATOR, NOT BY READING IT
  blog/index.html, sitemap.xml and robots.txt rebuild byte-identical: the
  blog-index card reads card:summary, which this post declares, and
  generate_card.py falls back to og:description only when that tag is absent.
  generate_og.py wraps the title only, so no share image changes.

WHAT IT DELIBERATELY DOES NOT DO
  It does not commit, stage, or push. It writes one named file and reports
  every other occurrence in the repo without touching it, so a derived surface
  that appears later shows up in the report instead of being silently patched.
"""

import sys
from pathlib import Path

POST = Path("blog/the-warning-not-the-gate/index.html")

# The edit anchor carries the colon, so there is no doubt which "gate" is being
# recapitalised, and the entity form of the apostrophe, because that is what
# this file uses throughout. Both halves of the registry form -- the capital
# and the dash -- move in one replacement: they are one quotation, and fixing
# half of it is a third variant rather than a repair.
OLD = ": gate what you&#8217;re judging, warn about"
NEW = ": Gate what you&#8217;re judging &#8212; warn about"

# The report anchor has no apostrophe in it, so it matches whether a file
# writes the apostrophe as &#8217; (the post) or as a literal (the feed).
FIND = "judging, warn about"

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
    loose = src.count(FIND)

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
        if FIND in s:
            others.append((p, s.count(FIND)))

    print(f"{C}== source =={N}")
    if n == 0 and loose == 0 and NEW in src:
        print(f"  {Y}{POST}{N}\n      already carries the registry form. Nothing to do.")
    elif n != EXPECTED:
        # Not a silent pass. The loose count is printed alongside, because
        # "my specific anchor missed" and "the string is not there" are
        # different findings and only one of them means the work is done.
        print(f"  {R}{POST}{N}")
        print(f"      exact anchor matched {n} time(s), expected {EXPECTED}.")
        print(f"      loose match ('{FIND}') found {loose} time(s).")
        if loose and not n:
            print(f"      The line is present but worded differently than this")
            print(f"      script expects -- check the colon and the entity form.")
        print(f"      Nothing written; this needs a human.")
        return 1
    else:
        print(f"  {G}{POST}{N}  {n} occurrence(s) -> capital G + em dash")

    if others:
        print(f"\n{Y}== carries the old form, not written ({len(others)}) =={N}")
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
        assert FIND not in out, "an old-form occurrence survived the replace"
        POST.write_text(out, encoding="utf-8")
        print(f"\n{G}wrote{N}  {POST}")

    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
