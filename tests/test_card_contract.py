#!/usr/bin/env python3
"""
test_card_contract.py — smoke test for the shared card renderer.

WHY THIS EXISTS
  scripts/generate_card.py is a library, not just a CLI. Three consumers import
  or invoke it: build_feed.py (bulk index regeneration), the MCP publishing
  agent (single-card insert), and the CLI (manual). Nothing in Python warns you
  when a function signature or a template token changes underneath them; the
  card just comes out different, or silently unfilled, and the blog index drifts.

  This test pins the contract: the public functions exist, they still accept the
  keyword arguments build_feed.py passes, and rendering a frozen fixture post
  produces a byte-identical card.

WHAT IT CHECKS
  1. generate_card imports the way build_feed.py imports it (scripts/ on path)
  2. Every public function build_feed.py calls is still present and callable
  3. fill_card() still accepts exactly: slug, date, minutes, title, summary
  4. The card template still contains every token fill_card replaces
  5. Rendering the fixture is byte-identical to tests/fixtures/golden-card.html
  6. No unfilled [PLACEHOLDER] survives the render

DELIBERATELY NO PYTEST. This repo carries no test framework and the workflow
installs only what the generators need; a plain script keeps CI dependency-free
and runs the same way in a phone Codespace. Right-sized for one smoke test.

USAGE (from the repo root)
  python tests/test_card_contract.py            # run the checks
  python tests/test_card_contract.py --bless    # re-record the golden card

RE-BLESSING
  Only bless when you changed the card contract ON PURPOSE. Read the diff the
  failure prints first; an unexpected diff is the test doing its job.

Exit code 0 = pass, 1 = fail. CI fails the build on non-zero.
"""

from __future__ import annotations

import difflib
import inspect
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
FIXTURE_POST = REPO_ROOT / "tests" / "fixtures" / "golden-post" / "index.html"
GOLDEN_CARD = REPO_ROOT / "tests" / "fixtures" / "golden-card.html"

# The exact keyword arguments build_feed.py passes to fill_card().
REQUIRED_FILL_KWARGS = {"slug", "date", "minutes", "title", "summary"}

# The functions build_feed.py reaches into generate_card for.
REQUIRED_FUNCS = (
    "read",
    "find_template",
    "fill_card",
    "extract_slug",
    "extract_title",
    "pretty_date",
    "read_minutes",
    "pick_summary",
)

# Tokens fill_card() substitutes; the template must still contain them.
REQUIRED_TEMPLATE_TOKENS = (
    "[POST-SLUG]",
    "[Month Day, Year]",
    "[X]",
    "[POST TITLE]",
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> bool:
    if condition:
        print(f"  PASS  {label}")
        return True
    print(f"  FAIL  {label}")
    if detail:
        for line in detail.rstrip().splitlines():
            print(f"        {line}")
    failures.append(label)
    return False


def render_fixture(gc) -> str:
    """Render the fixture exactly the way build_feed.write_index() does."""
    template = gc.read(gc.find_template(None))
    post_html = gc.read(str(FIXTURE_POST))
    return gc.fill_card(
        template,
        slug=gc.extract_slug(post_html),
        date=gc.pretty_date(post_html),
        minutes=gc.read_minutes(post_html, 200),
        title=gc.extract_title(post_html),
        summary=gc.pick_summary(post_html, None),
    )


def main() -> int:
    bless = "--bless" in sys.argv
    print("Card renderer contract test")
    print(f"  repo root: {REPO_ROOT}")

    # --- 1. import path -------------------------------------------------------
    sys.path.insert(0, str(SCRIPTS))
    try:
        import generate_card as gc
    except Exception as exc:  # noqa: BLE001 - we want the reason, whatever it is
        print(f"  FAIL  generate_card imports from scripts/\n        {exc}")
        print("\nFAILED: the renderer could not be imported; build_feed.py would "
              "fail the same way.")
        return 1
    check(True, "generate_card imports from scripts/")

    if not check(FIXTURE_POST.is_file(), f"fixture post exists ({FIXTURE_POST.name})"):
        return 1

    # --- 2. public functions present -----------------------------------------
    missing = [f for f in REQUIRED_FUNCS if not callable(getattr(gc, f, None))]
    check(
        not missing,
        "all required public functions present",
        "missing or not callable: " + ", ".join(missing) if missing else "",
    )

    # --- 3. fill_card signature ----------------------------------------------
    if callable(getattr(gc, "fill_card", None)):
        params = inspect.signature(gc.fill_card).parameters
        accepted = {n for n, p in params.items()
                    if p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD)}
        missing_kw = REQUIRED_FILL_KWARGS - accepted
        check(
            not missing_kw,
            "fill_card() accepts the kwargs build_feed.py passes",
            f"missing: {', '.join(sorted(missing_kw))}\n"
            f"current signature: fill_card{inspect.signature(gc.fill_card)}"
            if missing_kw else "",
        )

    # --- 4. template tokens ---------------------------------------------------
    try:
        template_path = gc.find_template(None)
        template = gc.read(template_path)
        absent = [t for t in REQUIRED_TEMPLATE_TOKENS if t not in template]
        check(
            not absent,
            "card template still contains every token fill_card replaces",
            f"absent from {template_path}: {', '.join(absent)}" if absent else "",
        )
    except SystemExit as exc:
        check(False, "card template is discoverable", str(exc))
        return 1

    # --- 5 & 6. render and compare -------------------------------------------
    rendered = render_fixture(gc)

    leftover = re.findall(r"\[[A-Z][^\]]*\]", rendered)
    check(
        not leftover,
        "no unfilled placeholders survive the render",
        "leftover: " + ", ".join(leftover) if leftover else "",
    )

    if bless:
        GOLDEN_CARD.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_CARD.write_text(rendered + "\n", encoding="utf-8")
        print(f"\nBLESSED: wrote {GOLDEN_CARD.relative_to(REPO_ROOT)}")
        print("Commit it, and make sure the diff was intentional.")
        return 0

    if not GOLDEN_CARD.is_file():
        print(f"  FAIL  golden card exists ({GOLDEN_CARD.relative_to(REPO_ROOT)})")
        print("        Run: python tests/test_card_contract.py --bless")
        return 1

    expected = GOLDEN_CARD.read_text(encoding="utf-8").rstrip("\n")
    actual = rendered.rstrip("\n")
    if expected == actual:
        check(True, "rendered card is byte-identical to the golden")
    else:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(), actual.splitlines(),
                fromfile="golden-card.html (expected)",
                tofile="rendered now (actual)",
                lineterm="",
            )
        )
        check(False, "rendered card is byte-identical to the golden", diff)

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed.")
        print("The card contract changed. If that was deliberate, re-bless with:")
        print("  python tests/test_card_contract.py --bless")
        return 1
    print("PASSED: card contract intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
