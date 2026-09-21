#!/usr/bin/env python3
"""Two repairs, one walk. Reports by default; writes only with --apply.

    python3 fix_grain_and_aphorism.py            # check: writes nothing
    python3 fix_grain_and_aphorism.py --apply    # write

Run from the rnvizion.github.io repo root.

1. The grain filter's feColorMatrix carries 19 values where type="matrix"
   requires exactly 20 -- four rows of five. Two zeros ran together into `00`
   and the alpha row lost one. An invalid matrix does not apply, so the rect
   renders raw fractalNoise: full-colour RGB fuzz at 0.5 opacity instead of
   the faint monochrome grain the CSS meant.

2. The closing aphorism carries a semicolon where the registry has an em dash.
   The dash is the point; the line reverses, and the writing profile reserves
   the dash for exactly that.

HELD BACK RATHER THAN FIXED, and named in the output:
  Golden fixtures and anything under a tests path -- a fixture is a recorded
  expectation, not a surface, and changing one changes what a test asserts.
  The aphorism outside demos/ -- published prose is a call about the post.
  Generators -- repairing output while its generator still emits the broken
  string means the next page it writes is born wrong.

IT DOES NOT commit, stage, or push. It matches the broken token run, never the
whole data URI, whose surrounding percent-encoded bytes vary per file. It
enumerates by walking the repo, never from a list.
"""

import sys
from pathlib import Path

BROKEN = "0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0 0.55 00 0 0.04 0"
FIXED  = "0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0 0.55 0 0 0 0.04 0"

# Anchored across the punctuation and clear of every apostrophe, so it matches
# whether the file uses a curly quote or a straight one. The dash is written as
# an escape rather than a literal, so this file survives being pasted through a
# phone keyboard without the dash turning into a hyphen on the way. That keeps
# the whole script ASCII, which is the same reason the DNS record lost its
# curly quotes: where a machine parses the file, the file's character set wins.
OLD = "judging; warn about"
NEW = "judging \u2014 warn about"

SURFACE = (".html", ".vtt")
SOURCE  = (".py", ".js", ".mjs", ".ts", ".sh", ".css", ".yml", ".yaml",
           ".json", ".md", ".txt", ".svg")

assert len(BROKEN.split()) == 19, "broken form should have 19 tokens"
assert len(FIXED.split()) == 20, "fixed form must have exactly 20"
assert BROKEN not in FIXED and FIXED not in BROKEN, "markers must not nest"

G, R, Y, C, D, N = ("\033[32m", "\033[31m", "\033[33m",
                    "\033[36m", "\033[2m", "\033[0m")


def held(p: Path) -> str:
    """Reason this path is reported instead of repaired, or '' to repair."""
    parts = {s.lower() for s in p.parts}
    if parts & {"tests", "test", "fixtures", "__snapshots__"} or "golden" in p.name.lower():
        return "recorded expectation, not a surface"
    return ""


def main() -> int:
    apply = "--apply" in sys.argv
    if not Path(".git").is_dir():
        print(f"{R}Run this from the rnvizion.github.io repo root.{N}")
        return 2

    plan, hold, source, stop, already = [], [], [], [], []
    walked = 0

    # This file carries both broken strings in its own docstring, because it
    # documents what it repairs. Searching for a value finds the sentence that
    # describes it as readily as the line that uses it; skip self, or the
    # script reports itself as a generator forever.
    me = Path(__file__).resolve()

    for p in sorted(Path(".").rglob("*")):
        if not p.is_file() or ".git" in p.parts or p.resolve() == me:
            continue
        suf = p.suffix.lower()
        if suf not in SURFACE and suf not in SOURCE:
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        walked += 1

        m, a = s.count(BROKEN), s.count(OLD)
        if not m and not a:
            if FIXED in s or NEW in s:
                already.append(p)
            continue

        # A generator is named, never written: its output is a second artifact.
        if suf in SOURCE:
            source.append((p, m, a))
            continue

        # Exactly one, or a human looks at it. Two copies in one file means
        # the page is not shaped the way this script believes it is.
        if m > 1:
            stop.append((p, f"broken matrix found {m} times, expected 1"))
            continue

        reason = held(p)
        if reason:
            hold.append((p, m, a, reason))
            continue

        # The aphorism is fixed on the demo surfaces. Elsewhere it is prose.
        if a and "demos" not in p.parts:
            if m:
                plan.append((p, m, 0))
            hold.append((p, 0, a, "published prose; a call about the post, not a typo"))
            continue

        plan.append((p, m, a))

    # ---------- report ----------
    print(f"{C}== walked {walked} text file(s) =={N}\n")
    if plan:
        print(f"{'FILE':<52}MATRIX  APHORISM")
        for p, m, a in plan:
            print(f"  {G}{str(p):<50}{N}{m:^6d}  {a:^8d}")
        print(f"\n  files to change : {len(plan)}")
        print(f"  matrices        : {sum(m for _, m, _ in plan)}")
        print(f"  aphorisms       : {sum(a for _, _, a in plan)}")
    else:
        print(f"  {G}nothing to change.{N}")

    if already:
        print(f"\n{D}  already repaired ({len(already)}):{N}")
        for p in already:
            print(f"{D}    {p}{N}")

    if hold:
        print(f"\n{Y}== held back, not written ({len(hold)}) =={N}")
        for p, m, a, why in hold:
            what = ", ".join(x for x in (f"{m} matrix" if m else "",
                                         f"{a} aphorism" if a else "") if x)
            print(f"  {Y}{p}{N}\n      {what} -- {why}")

    if source:
        print(f"\n{Y}== carries the broken string but is not a surface ({len(source)}) =={N}")
        for p, m, a in source:
            print(f"  {Y}{p}{N}  matrix x{m}  aphorism x{a}")
        print(f"{D}      A generator is fixed in its own change. Repairing only its{N}")
        print(f"{D}      output means the next page it writes is born broken.{N}")

    if stop:
        print(f"\n{R}== stopped ({len(stop)}) =={N}")
        for p, why in stop:
            print(f"  {R}{p}{N} -- {why}")
        # Scoped to the file, not the run. Each edit carries its own assert, so
        # one surprising page does not cancel seven correct repairs -- and a
        # guard that cancels unrelated work is a guard that gets loosened,
        # which is how the failure it was written for gets through later.
        # The exit code stays non-zero so nothing here passes quietly.
        print(f"{D}      Excluded from the run. The files above are untouched;{N}")
        print(f"{D}      everything in the first table is handled normally.{N}")

    if not apply:
        print(f"\n{Y}Check only. Nothing written.{N}")
        print("  Re-run with --apply once the list above is the list you expect.")
        return 1 if stop else 0

    # ---------- apply ----------
    print(f"\n{C}== writing =={N}")
    for p, m, a in plan:
        s = p.read_text(encoding="utf-8")
        # Re-assert against the file as it is now, not as it was during the
        # walk: these pages are also written by the OG workflow, so something
        # moving between the read and the save is routine here.
        if s.count(BROKEN) != m or s.count(OLD) != a:
            print(f"  {R}skip{N}   {p} -- changed since the check; re-run.")
            continue
        out = s.replace(BROKEN, FIXED).replace(OLD, NEW)
        p.write_text(out, encoding="utf-8")
        print(f"  {G}ok{N}     {p}")

    print(f"\n{G}Nothing staged, nothing committed.{N}")
    print("  git diff --stat")
    if stop or hold or source:
        print(f"{Y}  Held-back and stopped files above are unchanged.{N}")
    return 1 if stop else 0


if __name__ == "__main__":
    raise SystemExit(main())
