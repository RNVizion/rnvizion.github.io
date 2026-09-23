#!/usr/bin/env python3
"""Widen the sitemap page walk past depth 1. Three guarded edits.

    python sitemap_depth.py            # check: writes nothing
    python sitemap_depth.py --apply    # write

Run from the rnvizion.github.io repo root.

WHAT IS WRONG
  discover_static_pages() walks Path(".").glob("*/index.html") -- depth 1. It
  finds demos/index.html and never opens demos/rnv-publishing-agent/index.html
  one level below it. That page declares a valid og:url and is not a redirect
  stub, so it passes every rule the sitemap applies; the walk simply does not
  reach it. A depth-1 glob finding nothing at depth 2 is byte-indistinguishable
  from there being nothing at depth 2.

  It is the only real page affected today. card/print/index.html is also at
  depth 2 and is also absent, but for a different and correct reason: it
  declares no og:url, so the existing rule already excludes it. Widening the
  walk does not change that and should not.

THE HAZARD THE WIDENING CREATES, AND WHY tests JOINS SKIP_DIRS
  tests/fixtures/golden-post/index.html declares
  og:url = https://rnvizion.dev/blog/golden-fixture/ -- an address that does
  not exist on the live site. Deepen the walk without excluding it and the
  sitemap gains a 404. The fixture is doing its job: it is a realistic post,
  which is exactly what makes it dangerous to a walk that got wider.

  So SKIP_DIRS gains "tests". Measured before landing: the widened walk adds
  demos/rnv-publishing-agent/ and nothing else.

WHY rglob RATHER THAN A SECOND GLOB AT DEPTH 2
  A "*/*/index.html" line would fix today and go stale the day a page lands at
  depth 3, in the direction that reports clean. rglob with explicit exclusions
  is derivable rather than maintained: a new page at any depth arms itself.

  Blog posts stay out by a rule rather than by depth-1 accident -- excluded
  where blog/ is the first part and the path is deeper than blog/index.html, so
  the listing page is still picked up and the nine posts are still the feed
  pass's job.

  The root index.html stays PREPENDED rather than folded into the sort. It
  sorts after demos/ alphabetically, so a single sorted walk quietly moves
  the homepage from first to sixth in sitemap.xml -- harmless to a crawler
  and a behaviour change nobody asked for, inside a diff that claims to be
  about depth. Caught by diffing the generated file rather than reading the
  code.

WHAT IT DELIBERATELY DOES NOT DO
  It does not commit, stage, or push, and it does not run the generator. Push
  the change and build-feed.yml runs it -- scripts/build_feed.py is in that
  workflow's trigger paths, so the generator that changed is the generator that
  re-runs. A pipeline that watches its own tools does not need anyone to
  remember.

  Three edits, each asserting exactly one match, aborting the run if any is
  off. The third is the docstring: the sentence justifying the depth-1 glob
  becomes false the moment the walk deepens, and a stale caution retired in a
  later change is a caution that read as live in between.
"""

import sys
from pathlib import Path

FILE = Path("scripts/build_feed.py")

EDITS = [
    (
        "SKIP_DIRS gains tests",
        'SKIP_DIRS = {"_templates", "scripts", "assets", ".github", ".git", "node_modules"}',
        'SKIP_DIRS = {"_templates", "scripts", "assets", ".github", ".git", "node_modules",\n'
        '             "tests"}',
    ),
    (
        "page walk widened to any depth",
        '    candidates = [Path("index.html")] + [\n'
        '        f for f in sorted(Path(".").glob("*/index.html"))\n'
        '        if f.parent.name not in SKIP_DIRS\n'
        '    ]',
        '    candidates = [Path("index.html")] + [\n'
        '        f for f in sorted(Path(".").rglob("index.html"))\n'
        '        if len(f.parts) > 1\n'
        '        and not set(f.parts[:-1]) & SKIP_DIRS\n'
        '        and not (f.parts[0] == "blog" and len(f.parts) > 2)\n'
        '    ]',
    ),
    (
        "docstring: the depth-1 justification retired",
        '    Scans the repo root and every top-level directory for an index.html, then\n'
        '    keeps a page only if it declares an og:url and is NOT a redirect stub. The\n'
        "    og:url is the page's own canonical, which is the same field the feed already\n"
        '    trusts for posts; using it here keeps one definition of "this page\'s URL".\n'
        '\n'
        '    Blog posts live at blog/<slug>/index.html (depth 2) and are handled by the\n'
        '    feed pass, so this depth-1 glob never double-counts them. blog/index.html\n'
        '    itself IS picked up here, which is correct: the listing page is a real page.',
        '    Walks the repo at any depth for an index.html, then keeps a page only if it\n'
        '    declares an og:url and is NOT a redirect stub. The og:url is the page\'s own\n'
        '    canonical, which is the same field the feed already trusts for posts; using\n'
        '    it here keeps one definition of "this page\'s URL".\n'
        '\n'
        '    Blog posts are excluded by rule rather than by depth: anything under blog/\n'
        '    deeper than blog/index.html belongs to the feed pass. blog/index.html itself\n'
        '    IS picked up, which is correct -- the listing page is a real page.\n'
        '\n'
        '    The walk was depth 1 until demos/rnv-publishing-agent/ went live one level\n'
        '    below demos/, passed every rule, and was never opened. Widening it means\n'
        '    SKIP_DIRS has to carry "tests": the golden post fixture declares an og:url\n'
        '    for an address that does not exist, and a deeper walk would publish it.',
    ),
]

MARKER = 'rglob("index.html")'

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"{D}sitemap_depth.py -- widens the sitemap page walk in "
          f"scripts/build_feed.py{N}")
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
    if not FILE.is_file():
        print(f"{R}{FILE} not found. Nothing written.{N}")
        return 2

    src = FILE.read_text(encoding="utf-8")
    print(f"{C}== {FILE} =={N}")

    if MARKER in src:
        print(f"  {Y}skip{N}   the walk is already widened. Nothing to do.")
        return 0

    out = src
    for label, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            print(f"  {R}stop{N}   {label}: anchor matched {n} time(s), expected 1")
            print(f"{D}           nothing written. A widened walk with the old{N}")
            print(f"{D}           SKIP_DIRS publishes a fixture URL, so a partial{N}")
            print(f"{D}           apply is worse than none.{N}")
            return 1
        out = out.replace(old, new, 1)
        print(f"  {G}ok{N}     {label}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply to write.")
        return 0

    FILE.write_text(out, encoding="utf-8")
    print(f"\n{G}wrote{N}  {FILE}")
    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    print(f"{D}  Commit only scripts/build_feed.py. build-feed.yml regenerates{N}")
    print(f"{D}  sitemap.xml on the push and commits it itself.{N}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
