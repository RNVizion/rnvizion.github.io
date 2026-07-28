#!/usr/bin/env python3
"""
refresh_posts.py — sweep every published post for stale standing copy.

Run from the root of the rnvizion.github.io checkout.

    python refresh_posts.py            # dry run: shows every change, writes nothing
    python refresh_posts.py --write    # applies the changes
    python refresh_posts.py --write --only-bio

What it does
------------
1. Replaces the contents of the standing <div class="bio"> block on every post
   with the canonical bio. Idempotent: posts already current are reported and
   skipped, so it is safe to re-run.
2. Rewrites stale GitHub repo URLs left over from the rnv- prefix rename.
   Hugging Face Space IDs are deliberately NOT touched.
3. Renames "MCP Publishing Agent" to "RNV Publishing Agent" in post prose.
4. FLAGS ONLY (never edits) retired AIII framing. Rewriting an essay's prose
   needs judgment, so these are listed for manual review.

Run it on a clean git tree so `git diff` shows exactly what moved.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Canonical standing bio. Keep in sync with /bio/ and the post template.
# --------------------------------------------------------------------------
CANONICAL_BIO = (
    '\n          <strong>Christian Smith</strong> (RNVizion) is a Python developer '
    'building production AI systems on the Claude API, an AR/VR Sales &amp; Support '
    'Specialist at Meta, and a self-described modern-day Renaissance man. He ships '
    'retrieval systems, LLM agents, and the developer tools they run on; he also '
    'writes fiction, makes art, builds things by hand, and is figuring out the rest '
    'as he goes. Find his work at <a href="https://rnvizion.dev">rnvizion.dev</a>.\n        '
)

BIO_BLOCK = re.compile(r'(<div class="bio">)(.*?)(</div>)', re.DOTALL)

# Straight string swaps. Order matters: longest/most specific first.
REPLACEMENTS: list[tuple[str, str, str]] = [
    # (label, find, replace)
    ("repo rename: ask-the-corpus",
     "github.com/RNVizion/ask-the-corpus",
     "github.com/RNVizion/rnv-ask-the-corpus"),
    ("repo rename: publishing-agent",
     "github.com/RNVizion/publishing-agent",
     "github.com/RNVizion/rnv-publishing-agent"),
    ("product rename: publishing agent",
     "MCP Publishing Agent",
     "RNV Publishing Agent"),

    # --- Hotbox wording: settled decision, unambiguous swap ---
    ("Hotbox wording", "regulated cannabis startup", "regulated startup"),
    ("Hotbox wording", "regulated cannabis start-up", "regulated start-up"),
    ("Hotbox wording", "Regulated cannabis startup", "Regulated startup"),

    # --- AIII: retired standard framing, self-referential phrasings only ---
    # These name AIII or its identity work as the subject, so the swap is safe.
    # Anything NOT matched here stays put and gets flagged in context below,
    # because "open standard" is legitimate prose when discussing OIDF, the
    # IETF, or the Linux Foundation.
    ("AIII framing",
     "an open standard for AI agent identity with a reference implementation",
     "an Apache-2.0 reference implementation for AI agent identity"),
    ("AIII framing",
     "an open standard for AI agent identity",
     "an Apache-2.0 reference implementation for AI agent identity"),
    ("AIII framing",
     "an open standard for agent identity",
     "an Apache-2.0 reference implementation for agent identity"),
    ("AIII framing",
     "Open proposal and Apache-2.0 reference implementation",
     "Apache-2.0 reference implementation"),
    ("AIII framing",
     "open proposal and Apache-2.0 reference implementation",
     "Apache-2.0 reference implementation"),
    ("AIII framing", "an open proposal", "an Apache-2.0 reference implementation"),
    ("AIII framing", "Read the proposal", "Read the build record"),
    ("AIII framing", "read the proposal", "read the build record"),
]

# Residual detection. Runs AFTER the swaps above, so anything still matching
# did not fit a known self-referential pattern and needs a human read.
FLAG_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("unresolved AIII framing",
     re.compile(r"open standard|open proposal|standards initiative", re.I)),
    ("unresolved Hotbox wording", re.compile(r"cannabis", re.I)),
]

# Guard: these must never be rewritten by this script.
PROTECTED = [
    "huggingface.co/spaces/RNVizion/ask-the-corpus",
    "rnvizion-ask-the-corpus.hf.space",
]


def normalise(html: str) -> str:
    """Collapse whitespace so cosmetic indentation differences don't count as changes."""
    return re.sub(r"\s+", " ", html).strip()


def sentence_around(text: str, start: int, end: int) -> str:
    """Return the flagged phrase inside its sentence, tags stripped, match marked."""
    left = max(text.rfind(".", 0, start), text.rfind(">", 0, start)) + 1
    right = text.find(".", end)
    right = right + 1 if right != -1 else min(end + 160, len(text))
    fragment = text[left:right]
    marked = fragment[:start - left] + ">>" + fragment[start - left:end - left] + "<<" + fragment[end - left:]
    clean = re.sub(r"<[^>]+>", "", marked)
    return re.sub(r"\s+", " ", clean).strip()


def process(path: Path, only_bio: bool) -> dict:
    original = path.read_text(encoding="utf-8")
    text = original
    actions: list[str] = []
    flags: list[str] = []

    # --- 1. bio block ---
    match = BIO_BLOCK.search(text)
    if not match:
        flags.append("NO <div class=\"bio\"> BLOCK FOUND — check this post by hand")
    elif normalise(match.group(2)) == normalise(CANONICAL_BIO):
        actions.append("bio already current")
    else:
        text = text[:match.start(2)] + CANONICAL_BIO + text[match.end(2):]
        actions.append("bio REPLACED")

    # --- 2/3. string swaps ---
    if not only_bio:
        for label, find, repl in REPLACEMENTS:
            n = text.count(find)
            if n:
                text = text.replace(find, repl)
                shown = find if len(find) <= 46 else find[:43] + "..."
                actions.append(f'{label} ({n}x): "{shown}"')

    # --- 4. residuals: flag with sentence context, never auto-edit ---
    for label, pattern in FLAG_PATTERNS:
        for m in pattern.finditer(text):
            flags.append(f"{label}: {sentence_around(text, m.start(), m.end())}")

    # --- safety: protected strings must be untouched ---
    for guard in PROTECTED:
        if original.count(guard) != text.count(guard):
            raise SystemExit(
                f"ABORT: {path} — protected string '{guard}' was altered. No files written."
            )

    return {
        "path": path,
        "original": original,
        "text": text,
        "changed": text != original,
        "actions": actions,
        "flags": flags,
    }


def show_diff(path: Path, before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}", n=1,
    )
    for line in diff:
        print("   " + line.rstrip("\n"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh standing copy across published posts.")
    ap.add_argument("--write", action="store_true", help="apply changes (default is dry run)")
    ap.add_argument("--only-bio", action="store_true", help="skip the string swaps, bio only")
    ap.add_argument("--root", default="blog", help="posts directory (default: blog)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"error: '{root}' not found. Run this from the site repo root.", file=sys.stderr)
        return 2

    posts = sorted(p for p in root.glob("*/index.html"))
    if not posts:
        print(f"error: no posts found under {root}/*/index.html", file=sys.stderr)
        return 2

    results = [process(p, args.only_bio) for p in posts]

    changed = [r for r in results if r["changed"]]
    flagged = [r for r in results if r["flags"]]

    mode = "WRITING" if args.write else "DRY RUN (nothing written)"
    print(f"\n{mode} — {len(posts)} post(s) scanned under {root}/\n")

    for r in results:
        status = "CHANGED" if r["changed"] else "ok"
        print(f"[{status:>7}] {r['path']}")
        for a in r["actions"]:
            print(f"           · {a}")
        for f in r["flags"]:
            print(f"           ! {f}")
        if r["changed"] and not args.write:
            show_diff(r["path"], r["original"], r["text"])
        print()

    if args.write:
        for r in changed:
            r["path"].write_text(r["text"], encoding="utf-8")

    print("-" * 60)
    print(f"  posts scanned : {len(posts)}")
    print(f"  posts changed : {len(changed)}{'' if args.write else ' (would change)'}")
    print(f"  posts flagged : {len(flagged)}")
    if flagged:
        print("\n  Flagged posts need a human read; this script never edits prose:")
        for r in flagged:
            print(f"    - {r['path']}")
    if not args.write and changed:
        print("\n  Re-run with --write to apply.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
