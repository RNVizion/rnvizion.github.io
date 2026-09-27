#!/usr/bin/env python3
"""
edit_generate_contact_card_rewire.py — guarded exact-string edit script.

Run from the rnvizion.github.io repo root:
    python3 edit_generate_contact_card_rewire.py

Target: scripts/generate_contact_card.py
Built from: scripts/generate_contact_card.py on main, fetched 2026-09-27
            (the August 11, 2026 build; unchanged since except mark tracking)
Manifest:   profile.json v1.3.2 (2026-09-02) — identity.brand_phone exists

What this changes, and why each one:
  1. The brand routing number moves from a hardcoded override to the manifest
     key that now owns it (identity.brand_phone.display / .e164). The override
     was applied AFTER the manifest read, so it won and the manifest's copy was
     decorative; a change there would never have reached the card.
  2. The forbidden-key guard becomes a refusal. The August version set a flag
     that nothing read; the card was protected only because PATHS never named
     the key. Now: a forbidden path wired into PATHS fails at import, and a
     forbidden key present in the manifest fails the run.
  3. A comment carrying part of a personal-layer value is retired. The rule
     names the layer, never the value.
  4. The docstring's hardcoded manifest version is replaced with a pointer at
     the run-time print, which reads the version from the file and cannot go
     stale.
  5. Stale PENDING MANIFEST cautions retired; the two that are still true stay.

Every edit asserts its target occurs exactly once. Any assert failing means
the file is not the base this was built from: stop, re-fetch, do not force.

Expected result after `bash test.sh`: the regenerated card/ is byte-identical
to the committed one. The value did not change, only where it is read from.
A diff means something is wrong.
"""

from pathlib import Path
import py_compile
import sys

TARGET = Path("scripts/generate_contact_card.py")

EDITS = [
    # 1. docstring provenance: hardcoded version -> pointer at the run-time print
    (
        "Built against profile.json v1.2.7 (fetched 2026-08-10). If the manifest has moved\n"
        "past that, re-read it before trusting the key paths in the ADAPTER block below.",

        "The manifest version this ran against is printed on every run, read from the\n"
        "file itself; nothing here restates it. A version written into a docstring is\n"
        "stale the day the manifest moves, and it reads as checked.",
    ),

    # 2. ADAPTER comment: four pending facts became two; the mechanism is unchanged
    (
        "# Two of the facts this surface needs are NOT in the manifest yet, and how they\n"
        "# get encoded is the Brand Infrastructure project's dispatch call, not this\n"
        "# script's. Until they land, they come from CARD_OVERRIDES below and the script\n"
        "# says so loudly on every run. When they land, delete the override and point the\n"
        "# path at the real key. Nothing else in this file changes.",

        "# Facts this surface needs that the manifest does not carry yet come from\n"
        "# CARD_OVERRIDES below, and the script says so on every run. How they get\n"
        "# encoded is the Brand Infrastructure project's dispatch call, not this\n"
        "# script's. When one lands, delete the override and point the path at the\n"
        "# real key; the brand number made that trip in manifest v1.3.0. An override\n"
        "# left in place after its fact lands wins over the manifest, silently.",
    ),

    # 3. PATHS: the brand number is read from the manifest
    (
        "    # Public inbound address. Lives under identity.role_emails as a key.\n"
        "    \"email\":    (\"identity\", \"role_emails\", \"inquiries@rnvizion.dev\"),\n"
        "}",

        "    # Public inbound address. Lives under identity.role_emails as a key.\n"
        "    \"email\":    (\"identity\", \"role_emails\", \"inquiries@rnvizion.dev\"),\n"
        "    # Brand routing number. Both forms are carried in the manifest, not derived:\n"
        "    # the card face takes display, tel: and the vCard TEL take e164.\n"
        "    \"brand_phone_display\": (\"identity\", \"brand_phone\", \"display\"),\n"
        "    \"brand_phone_e164\":    (\"identity\", \"brand_phone\", \"e164\"),\n"
        "}",
    ),

    # 4. forbidden-key guard: name the layer, not the value; make it a real guard
    (
        "# NEVER read identity.phone. That is the personal cell (301). The card carries\n"
        "# the brand routing number and nothing else. This is enforced, not advised.\n"
        "FORBIDDEN_PATHS = [(\"identity\", \"phone\")]",

        "# Personal-layer contact facts never reach a brand surface. identity.phone\n"
        "# held one until manifest v1.3.0 removed it; the key stays forbidden so its\n"
        "# return is a loud failure rather than a quiet one. Two checks, both read:\n"
        "# a forbidden path wired into PATHS fails at import, and a forbidden key\n"
        "# present in the manifest fails the run. The August version set a flag\n"
        "# nothing consumed, which is not a guard.\n"
        "FORBIDDEN_PATHS = [(\"identity\", \"phone\")]\n"
        "for _name, _path in PATHS.items():\n"
        "    assert _path not in FORBIDDEN_PATHS, f\"PATHS[{_name!r}] reads a forbidden key\"",
    ),

    # 5. CARD_OVERRIDES: the number leaves; line and kicker stay, cautions tightened
    (
        "CARD_OVERRIDES = {\n"
        "    # PENDING MANIFEST: brand routing number (Google Voice, created 2026-08-10).\n"
        "    # Distinct fact from identity.phone. Suggested shape only; dispatch is theirs.\n"
        "    \"brand_phone_display\": \"(202) 987-9948\",\n"
        "    \"brand_phone_e164\": \"+12029879948\",\n"
        "    # PENDING MANIFEST: the card line. Registry row Banked until the card ships.\n"
        "    \"line\": \"Vizion, built not borrowed.\",\n"
        "    # PENDING MANIFEST: the discipline kicker.\n"
        "    \"kicker\": \"AI · SOFTWARE · WEB · BRAND\",\n"
        "}",

        "CARD_OVERRIDES = {\n"
        "    # PENDING MANIFEST: the card line. Its registry status lives in Brand Book\n"
        "    # §5 and is not restated here.\n"
        "    \"line\": \"Vizion, built not borrowed.\",\n"
        "    # PENDING MANIFEST: the discipline kicker.\n"
        "    \"kicker\": \"AI · SOFTWARE · WEB · BRAND\",\n"
        "}",
    ),

    # 6. the flag nobody read becomes a refusal
    (
        "    for path in FORBIDDEN_PATHS:\n"
        "        if dig(data, path) is not None:\n"
        "            facts.setdefault(\"_forbidden_present\", True)",

        "    present = [\".\".join(p) for p in FORBIDDEN_PATHS if dig(data, p) is not None]\n"
        "    if present:\n"
        "        sys.exit(\"REFUSED: the manifest carries a personal-layer key this surface \"\n"
        "                 f\"must never see: {', '.join(present)}. The card does not read \"\n"
        "                 \"it, but its presence means something upstream went wrong; \"\n"
        "                 \"resolve that before building a brand surface from this file.\")",
    ),
]


def main() -> None:
    if not TARGET.is_file():
        sys.exit(f"REFUSED: {TARGET} not found. Run from the repo root.")
    src = TARGET.read_text(encoding="utf-8")

    # Guard every edit before applying any: a half-applied file is worse than none.
    for i, (old, _new) in enumerate(EDITS, 1):
        n = src.count(old)
        assert n == 1, (f"edit {i}: expected exactly 1 occurrence, found {n}. "
                        "The file is not the base this script was built from.")

    out = src
    for old, new in EDITS:
        out = out.replace(old, new, 1)

    # The value must not survive anywhere in the file once it is read from the manifest.
    assert "987-9948" not in out and "12029879948" not in out, \
        "brand number still hardcoded somewhere; refusing to write"
    assert "(301)" not in out, "personal-layer fragment still present; refusing to write"

    TARGET.write_text(out, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)
    print(f"applied {len(EDITS)} edits to {TARGET}; compiles clean")
    print("next: bash test.sh  -> expect card/ byte-identical to the committed copy")


if __name__ == "__main__":
    main()
