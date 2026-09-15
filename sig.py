#!/usr/bin/env python3
"""index.html: rename --signal-down to --signal-standby, and say why it exists.

Built against rnvizion.github.io/index.html @ main, read 2026-09-15.
Run from repo root. Two edits, both in the :root token block.

    python3 sig.py            # DRY RUN
    python3 sig.py --apply

RENAME, NOT DELETE. A note proposed deleting the token on the grounds that the
page has no standby state and nothing consumes it. Both facts are true and the
conclusion does not follow, for three reasons:

  THE TOKEN WAS DELIBERATE. The 2026-08-13 handoff that added all three wrote:
  "Only --signal-live is used today. The other two are there so the next use does
  not hardcode." Deleting it reverses a recorded decision rather than tidying an
  oversight.

  THE REVALUATION ARGUMENT COMPARED THE WRONG TOKENS. That note held that a
  rename would leave a correctly-named token with the wrong value, citing
  BRAND_STANDBY_GOLD #ae986f. That is `signal-ring-standby`, the RING. The FILL
  is `signal-standby` = #ffd166 -- exactly what this page already carries. The
  rename is correct on name and value, and needs no revaluation.

  DELETING CREATES THE COLLAPSE THE REGISTER FORBIDS. --accent-warm is #ffd166
  four lines above. Remove the signal token and that value survives on the page
  only as a decorative one; the next person adding a standby state finds it
  declared and reaches for it. engine/brand.py: "THE MATCH IS INCIDENTAL AND THE
  SEAM IS DELIBERATE ... Do not 'de-duplicate' these."

THE COMMENT NOW SAYS WHY THE TOKEN IS UNUSED, which is the part that was
missing. The declaration was correct and silent, so a later reader observed
accurately that nothing consumed it and proposed removing it. That round trip
was avoidable:

  **A declaration kept for a future consumer has to say so. Otherwise someone
  will correctly observe it has no consumer, and correctly conclude the wrong
  thing.** An unexplained placeholder is indistinguishable from a leftover.

NOT TOUCHED, deliberately: --signal-offline and --accent-warm are also declared
and unconsumed here. Same class, same reasoning, out of scope for a rename.
"""
import pathlib
import sys

APPLY = "--apply" in sys.argv
P = pathlib.Path("index.html")

assert P.exists(), "run from the repo root"
s = P.read_text(encoding="utf-8")
assert "--signal-standby" not in s, "already renamed"

EDITS = [
    (
        "         signal-offline/-down equal --text-faint/--accent-warm by coincidence;\n"
        "         the seam is deliberate. Do not de-duplicate. Source: engine/brand.py. */",

        "         signal-offline/-standby equal --text-faint/--accent-warm by coincidence;\n"
        "         the seam is deliberate. Do not de-duplicate. Source: engine/brand.py.\n"
        "\n"
        "         Only --signal-live is consumed on this page: the hero dot has one\n"
        "         state and is always live. The other two are declared so a future use\n"
        "         does not hardcode -- kept on purpose, not left behind. Renamed from\n"
        "         --signal-down 2026-09-15, following the register's 2026-08-23 rename;\n"
        "         the value is unchanged because signal-standby IS #ffd166. Deleting\n"
        "         --signal-standby would leave #ffd166 on this page only as\n"
        "         --accent-warm, which is the de-duplication the line above forbids. */",
    ),
    (
        "      --signal-live: #a5034e; --signal-offline: #5a5a72; --signal-down: #ffd166;",
        "      --signal-live: #a5034e; --signal-offline: #5a5a72; --signal-standby: #ffd166;",
    ),
]

for i, (old, new) in enumerate(EDITS, 1):
    n = s.count(old)
    assert n == 1, f"edit {i}: expected 1 anchor, found {n}. Base has moved."

if not APPLY:
    print("both anchors found. DRY RUN -- nothing written.")
    print("re-run with --apply.")
    sys.exit(0)

for old, new in EDITS:
    s = s.replace(old, new)

P.write_text(s, encoding="utf-8")
after = P.read_text(encoding="utf-8")
assert "--signal-standby: #ffd166;" in after, "rename did not land"
assert "--signal-down" not in after.split("Renamed from")[0], "old token survives outside the history note"
# The two DECLARATIONS, not the file. The comment above quotes the value twice
# while explaining the seam, so a whole-file count measures the prose. Ninth
# time this has fired here: any .count() against a whole file is wrong by
# default -- check a full declaration line, or count inside an extracted slice.
assert after.count("--accent-warm: #ffd166;") == 1, "accent-warm disturbed"
assert after.count("--signal-standby: #ffd166;") == 1, "signal token disturbed"
assert "var(--signal-live)" in after, "the consumed token was disturbed"
print("index.html: --signal-down -> --signal-standby, value unchanged.")
print("            comment now states why the token is declared and unconsumed.")
