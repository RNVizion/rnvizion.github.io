#!/usr/bin/env python3
"""Point the resume at the publishing-agent demo. Two guarded edits.

    python resume_demo.py            # check: writes nothing
    python resume_demo.py --apply    # write

Run from the rnvizion.github.io repo root.

WHAT IT CHANGES
  1. The nav gains a Demos link, after Work. Every other page carrying a nav
     already has one; resume/index.html is the only one that does not, because
     its nav block is `<div class="nav-links">` with no id and the earlier pass
     matched on the id. That pass named this file in its no-nav list and the
     file was never fixed -- printing a finding is not applying one.

  2. The RNV Publishing Agent entry gains the demo URL, in the same shape the
     AIII entry already uses for a second link: url-as-text, `proj-url` class,
     at the end of the prose.

THE SENTENCE IS YOURS. It is a named constant below, on its own line. Reword it
before running; the guards do not depend on its content. The entry already uses
the word "demo" for the self-contained chain test that runs in CI, so this one
says "walkthrough" -- two things called demo in one paragraph is a name
collision, not a style question.

WHAT IT DELIBERATELY DOES NOT DO
  It does not commit, stage, or push. Each edit asserts exactly one match and
  aborts otherwise. It is idempotent by a marker unique to the patched form,
  never by an anchor that survives the patch.

  It does not touch the resume's missing mobile layout. That page carries zero
  @media queries and no nav toggle where every other page has both, so the nav
  it is gaining will sit unwrapped on a phone. Reported, not fixed: it is a
  different change and it is not what was asked for.
"""

import sys
from pathlib import Path

PAGE = Path("resume/index.html")
URL = "https://rnvizion.dev/demos/rnv-publishing-agent/"

# --- edit 1: nav -----------------------------------------------------------
NAV_ANCHOR = '        <a href="/#work">Work</a>\n'
NAV_ADD = '        <a href="/demos/">Demos</a>\n'

# --- edit 2: the project entry ---------------------------------------------
PROSE_ANCHOR = "and CI runs both on every push."

# Reword this freely. It is appended to the sentence that already ends the
# entry, matching the AIII entry's "Source at <url>" shape.
PROSE_ADD = (
    ' Recorded walkthrough at <a class="proj-url" href="'
    + URL
    + '">rnvizion.dev/demos/rnv-publishing-agent</a>.'
)

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


def main() -> int:
    apply = "--apply" in sys.argv
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2
    if not PAGE.is_file():
        print(f"{R}{PAGE} not found. Nothing written.{N}")
        return 2

    src = PAGE.read_text(encoding="utf-8")
    out = src
    did = []
    print(f"{C}== {PAGE} =={N}")

    # 1. nav ----------------------------------------------------------------
    if 'href="/demos/"' in out:
        print(f"  {Y}skip{N}   nav already carries Demos")
    else:
        n = out.count(NAV_ANCHOR)
        if n != 1:
            print(f"  {R}stop{N}   nav Work link found {n} time(s), expected 1")
            print(f"{D}           the nav is not shaped the way this script believes;{N}")
            print(f"{D}           nothing written.{N}")
            return 1
        out = out.replace(NAV_ANCHOR, NAV_ANCHOR + NAV_ADD, 1)
        did.append("nav: Demos added after Work")

    # 2. project entry ------------------------------------------------------
    if URL in out:
        print(f"  {Y}skip{N}   entry already links the demo")
    else:
        n = out.count(PROSE_ANCHOR)
        if n != 1:
            print(f"  {R}stop{N}   entry anchor found {n} time(s), expected 1")
            print(f"{D}           the RNV Publishing Agent prose has moved;{N}")
            print(f"{D}           nothing written.{N}")
            return 1
        out = out.replace(PROSE_ANCHOR, PROSE_ANCHOR + PROSE_ADD, 1)
        did.append("entry: demo URL appended to the prose")

    if not did:
        print(f"\n  {G}nothing to change.{N}")
        return 0

    for d in did:
        print(f"  {G}ok{N}     {d}")

    # Show both edits as they will read, so the wording is reviewed before it
    # is written rather than after it is pushed.
    a = out.find('<div class="nav-links"')
    b = out.find("</div>", a)
    print(f"\n{D}  nav, after:{N}")
    for ln in out[a:b].splitlines():
        if ln.strip():
            print(f"{D}    {ln.rstrip()}{N}")

    print(f"\n{D}  entry, after:{N}")
    i = out.find(PROSE_ANCHOR)
    print(f"{D}    ...{out[i:i + 170]}{N}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply once the wording above is what you want.")
        return 0

    PAGE.write_text(out, encoding="utf-8")
    print(f"\n{G}wrote{N}  {PAGE}")
    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
