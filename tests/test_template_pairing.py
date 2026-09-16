#!/usr/bin/env python3
"""Every template in _templates/ has a paired .RULES.md beside it.

The template is the skeleton; the rules file is the brain. Templates carry no
comment that explains or instructs, because everything in a template is copied
wherever that template goes -- so the reasoning lives in a sibling file.

That pairing is a convention, and a convention nothing checks is a convention
until the first time someone is in a hurry. This is the check.

Run: python tests/test_template_pairing.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "_templates"

# A stub that exists only to satisfy the guard is not a pair.
MIN_BYTES = 400

failures = []
templates = sorted(TEMPLATES.glob("*.html"))

if not templates:
    failures.append("no templates found in _templates/ -- has the folder moved?")

for t in templates:
    rules = t.with_suffix(".RULES.md")
    if not rules.exists():
        failures.append("%s has no %s" % (t.name, rules.name))
        continue
    size = rules.stat().st_size
    if size < MIN_BYTES:
        failures.append(
            "%s is %d bytes; a pair that says nothing is not a pair" % (rules.name, size))

# A rules file with no template is the other direction of the same drift.
for r in sorted(TEMPLATES.glob("*.RULES.md")):
    stem = r.name[: -len(".RULES.md")]
    if not (TEMPLATES / (stem + ".html")).exists():
        failures.append("%s has no template" % r.name)

if failures:
    print("TEMPLATE PAIRING FAILED")
    print()
    for f in failures:
        print("  " + f)
    print()
    print("Every _templates/*.html needs a sibling *.RULES.md carrying the")
    print("reasoning that is not allowed to live in the template itself.")
    sys.exit(1)

print("template pairing OK: %d template(s), each paired" % len(templates))
