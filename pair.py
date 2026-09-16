#!/usr/bin/env python3
"""Card template: strip it, and make the template pairing mechanical.

Built against rnvizion.github.io @ main, read 2026-09-15. Run from repo root.

    python3 pair.py            # DRY RUN
    python3 pair.py --apply

RUN _templates/post-card-template.RULES.md FIRST. Same order as last time: the
new home before the copies come out. This refuses if it is absent.

THREE CHANGES.

1. STRIP THE CARD TEMPLATE. 22 of its 36 lines are one comment block -- publish
   instructions, four sync requirements, a typography rule. It does not ship
   into a published page the way the post comments did; it ships into
   blog/index.html on every publish, which is the same problem one surface over.

   It keeps NO markers. The post template keeps four because it has sections to
   label; this is a single <article> block with nothing to navigate.

2. A GUARD FOR THE PAIRING. tests/test_template_pairing.py asserts every
   _templates/*.html has a sibling *.RULES.md, that each rules file says
   something, and that no rules file is orphaned. This is what RULES.md meant by
   the pairing being mechanical: a convention nothing checks is a convention
   until the first time someone is in a hurry.

   It would have FAILED the day it was written -- post-card-template.html had no
   pair until this change. That is the correct first result for a guard.

3. THE TRIGGER PATH THAT MAKES THE GUARD REAL. build-feed.yml fires on
   _templates/post-card-template.html and not on _templates/post-template.html,
   so a guard about templates would not run when a template changed. Widened to
   _templates/**.

   This repo has closed the same defect twice -- generate_card.py outside its own
   trigger path, then font.sh. A check that does not run is indistinguishable
   from a check that passes, and a third instance is the one that says the shape
   is worth naming rather than fixing again.
"""
import pathlib
import re
import sys

APPLY = "--apply" in sys.argv
ROOT = pathlib.Path(".")

CARD = ROOT / "_templates" / "post-card-template.html"
CARD_RULES = ROOT / "_templates" / "post-card-template.RULES.md"
WF = ROOT / ".github" / "workflows" / "build-feed.yml"
TEST = ROOT / "tests" / "test_template_pairing.py"

assert CARD_RULES.exists(), (
    "_templates/post-card-template.RULES.md is missing. It is the new home for the\n"
    "comment this removes. Land it first; this refuses rather than lose it."
)

GUARD_LINES = [
    '#!/usr/bin/env python3',
    '"""Every template in _templates/ has a paired .RULES.md beside it.',
    '',
    'The template is the skeleton; the rules file is the brain. Templates carry no',
    'comment that explains or instructs, because everything in a template is copied',
    'wherever that template goes -- so the reasoning lives in a sibling file.',
    '',
    'That pairing is a convention, and a convention nothing checks is a convention',
    'until the first time someone is in a hurry. This is the check.',
    '',
    'Run: python tests/test_template_pairing.py',
    '"""',
    'import pathlib',
    'import sys',
    '',
    'ROOT = pathlib.Path(__file__).resolve().parent.parent',
    'TEMPLATES = ROOT / "_templates"',
    '',
    '# A stub that exists only to satisfy the guard is not a pair.',
    'MIN_BYTES = 400',
    '',
    'failures = []',
    'templates = sorted(TEMPLATES.glob("*.html"))',
    '',
    'if not templates:',
    '    failures.append("no templates found in _templates/ -- has the folder moved?")',
    '',
    'for t in templates:',
    '    rules = t.with_suffix(".RULES.md")',
    '    if not rules.exists():',
    '        failures.append("%s has no %s" % (t.name, rules.name))',
    '        continue',
    '    size = rules.stat().st_size',
    '    if size < MIN_BYTES:',
    '        failures.append(',
    '            "%s is %d bytes; a pair that says nothing is not a pair" % (rules.name, size))',
    '',
    '# A rules file with no template is the other direction of the same drift.',
    'for r in sorted(TEMPLATES.glob("*.RULES.md")):',
    '    stem = r.name[: -len(".RULES.md")]',
    '    if not (TEMPLATES / (stem + ".html")).exists():',
    '        failures.append("%s has no template" % r.name)',
    '',
    'if failures:',
    '    print("TEMPLATE PAIRING FAILED")',
    '    print()',
    '    for f in failures:',
    '        print("  " + f)',
    '    print()',
    '    print("Every _templates/*.html needs a sibling *.RULES.md carrying the")',
    '    print("reasoning that is not allowed to live in the template itself.")',
    '    sys.exit(1)',
    '',
    'print("template pairing OK: %d template(s), each paired" % len(templates))',
]
GUARD = "\n".join(GUARD_LINES) + "\n"

card = CARD.read_text(encoding="utf-8")
card_out = re.sub(r"[ \t]*<!--.*?-->[ \t]*\n?", "", card, flags=re.S)
card_out = re.sub(r"\n{3,}", "\n\n", card_out).lstrip("\n")

wf = WF.read_text(encoding="utf-8")
OLD_PATH = '      - "_templates/post-card-template.html"     # the card definition'
NEW_PATH = '      - "_templates/**"                          # every template and its paired RULES'
OLD_STEP = """      - name: Card renderer contract test
        run: python tests/test_card_contract.py"""
NEW_STEP = """      - name: Card renderer contract test
        run: python tests/test_card_contract.py

      - name: Template pairing
        run: python tests/test_template_pairing.py"""

problems = []
if "<!--" not in card:
    problems.append("card template already has no comments")
if card_out == card:
    problems.append("the strip removed nothing -- check the pattern")
if wf.count(OLD_PATH) != 1:
    problems.append("build-feed.yml: trigger-path anchor not found exactly once")
if wf.count(OLD_STEP) != 1:
    problems.append("build-feed.yml: test-step anchor not found exactly once")
if TEST.exists():
    problems.append("tests/test_template_pairing.py already exists")

if problems:
    print("REFUSING -- nothing written.")
    print()
    for p in problems:
        print("  " + p)
    sys.exit(1)

print("card template : %d bytes -> %d  (%d comment removed)"
      % (len(card), len(card_out), card.count("<!--")))
print("guard         : tests/test_template_pairing.py  (new)")
print("trigger path  : _templates/post-card-template.html -> _templates/**")
print("workflow step : Template pairing, after the card contract test")

if not APPLY:
    print()
    print("DRY RUN -- nothing written. Re-run with --apply.")
    sys.exit(0)

CARD.write_text(card_out, encoding="utf-8")
TEST.parent.mkdir(exist_ok=True)
TEST.write_text(GUARD, encoding="utf-8")
WF.write_text(wf.replace(OLD_PATH, NEW_PATH).replace(OLD_STEP, NEW_STEP), encoding="utf-8")

c = CARD.read_text(encoding="utf-8")
assert "<!--" not in c, "a comment survives in the card template"
assert '<article class="post-card">' in c, "the card block was damaged"
assert "[POST-SLUG]" in c and "[POST TITLE]" in c, "placeholders were eaten"
assert c.count("</article>") == 1, "the card block was truncated"
w = WF.read_text(encoding="utf-8")
assert '"_templates/**"' in w, "trigger path not widened"
assert "test_template_pairing.py" in w, "workflow step not added"
assert TEST.exists(), "guard not written"

print()
print("written. Run the guard now -- it should pass, and would not have before.")
