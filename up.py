#!/usr/bin/env python3
"""gi.py -- retire a stale clause in rnvizion.github.io's .gitignore.

Built against rnvizion.github.io @ main d5a9d06. One file, one guarded edit.

The comment says the publishing agent's import writes __pycache__ into a site
checkout. That was true when it was written and is false now: the agent wraps
its import in sys.dont_write_bytecode (server.py:325-341 at agent c9579a8).
Verified on two clean clones -- with the guard no directory appears, without it
one does.

The rule itself stays and is not in question. This repo's own test imports the
library, so running the guard writes bytecode here. Only the clause about the
other repo went stale, and the replacement records what retired it so the wrong
reason does not get re-added by someone reasoning from first principles.

Nothing else moves. A .gitignore comment and anything else found in the same
hour are separate commits.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())
TARGET = ROOT / ".gitignore"

OLD = """# Bytecode. tests/test_post_shape.py imports scripts/post_shape.py, so running
# the guard writes __pycache__ into both folders; the publishing agent importing
# the same file does it again in whatever checkout it holds.
"""

NEW = """# Bytecode. tests/test_post_shape.py imports scripts/post_shape.py, so running
# the guard writes __pycache__ into both folders. This covers THIS repo's own
# runs. The publishing agent imports that same file from its own checkout and
# does not write one -- it wraps the import in sys.dont_write_bytecode, on the
# grounds that a publish is not entitled to create files in somebody else's
# repository. Verified 2026-09-20 at agent c9579a8: with their guard no
# directory appears, without it one does.
"""

DONE = "does not write one -- it wraps the import"


def main():
    if not TARGET.exists():
        sys.exit(".gitignore not found at %s -- wrong repo? This script is for "
                 "rnvizion.github.io." % TARGET)

    text = TARGET.read_text(encoding="utf-8")

    if DONE in text:
        print("already applied -- nothing to do.")
        return 0

    count = text.count(OLD)
    assert count == 1, (
        "the comment block this replaces appears %d time(s) in .gitignore, "
        "expected 1. The file has moved; re-cut this script against live."
        % count)

    # Check the RULE before touching the comment. This edit is prose about a
    # rule, so the rule's state is the same before and after -- and checking
    # first means a broken one refuses rather than leaving a dirty tree with a
    # freshly-written comment describing something that is no longer there.
    check = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-q", "scripts/__pycache__/x.pyc"])
    if check.returncode != 0:
        sys.exit("git does not ignore scripts/__pycache__/, so the rule this "
                 "comment explains is gone or has moved. Nothing written -- "
                 "fix the rule before rewording the reason for it.")

    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("patched .gitignore")
    print("rule verified live before the edit: scripts/__pycache__/ is ignored")
    print()

    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--name-only"],
        capture_output=True, text=True, check=True).stdout.split()
    print("files changed: %s" % (", ".join(tracked) or "none"))
    print()
    print('  git add .gitignore')
    print('  git commit -m "chore: retire a stale clause in the bytecode ignore"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
