#!/usr/bin/env python3
"""card.py -- the contact card reads its line and kicker from the manifest.

Built against rnvizion.github.io @ main 2b8ea3a, and rnv-brand @ 292e498, where
profile.json first carries facts.card_line and facts.discipline_kicker.

ONE FILE MOVES: scripts/generate_contact_card.py. Seven guarded edits:
  1. PATHS gains "line" and "kicker", read from facts.card_line.value and
     facts.discipline_kicker.value.
  2. the ADAPTER comment stops describing an override table.
  3. CARD_OVERRIDES is deleted, not emptied. An override left in place after
     its fact lands wins over the manifest silently -- the file said so itself.
  4-6. load_facts and main stop passing an overrides list around.
  7. the "NOT YET IN THE MANIFEST" message goes. It was true until the manifest
     carried both values, and false after, printed on every run.

WHAT IT PROVES BEFORE WRITING ANYTHING, --check included: it runs the current
generator and the edited one against the same manifest into two temp folders
and compares all five outputs byte for byte. This change must not move a
single byte of the card; if it would, nothing is written. It then says
whether the committed card/ already matches, which is a separate question.

The card/ files are not touched. If the outputs match, there is nothing to
regenerate and nothing to commit there.

The generator needs qrcode and Pillow (the devcontainer installs qrcode) and
reads the manifest from ../rnv-brand/profile.json, or from main if that isn't
there -- exactly as it always does.

Refuses on any unexpected base and writes nothing. Re-running is a no-op.
  python card.py --check   # prove it and report, write nothing
  python card.py           # prove it, then apply
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, check=True).stdout.strip())
REL = "scripts/generate_contact_card.py"
TARGET = ROOT / REL
OUTPUTS = ("index.html", "rnvizion.vcf", "print/index.html",
           "card-qr.png", "card-qr-print.png")

EDITS = json.loads(r"""[["PATHS reads the card line and kicker from the manifest", "    \"brand_phone_e164\":    (\"identity\", \"brand_phone\", \"e164\"),\n}\n", "    \"brand_phone_e164\":    (\"identity\", \"brand_phone\", \"e164\"),\n    # The card line and the discipline kicker. Their registry status lives in\n    # Brand Book §5 and is not restated here. The kicker is stored in its web\n    # form; build_vcard downgrades the dots for the vCard NOTE, consumer-side.\n    \"line\":     (\"facts\", \"card_line\", \"value\"),\n    \"kicker\":   (\"facts\", \"discipline_kicker\", \"value\"),\n}\n"], ["ADAPTER comment: no override table any more", "# Facts this surface needs that the manifest does not carry yet come from\n# CARD_OVERRIDES below, and the script says so on every run. How they get\n# encoded is the Brand Infrastructure project's dispatch call, not this\n# script's. When one lands, delete the override and point the path at the\n# real key; the brand number made that trip in manifest v1.3.0. An override\n# left in place after its fact lands wins over the manifest, silently.\n", "# Every fact on this surface comes from the manifest, and there is no override\n# table. A fact the manifest does not carry yet goes to the Brand\n# Infrastructure project first, since how it is encoded is their call, and\n# until it lands this script refuses rather than hardcoding it. The table\n# that used to sit below held the card line and the kicker until the manifest\n# carried them; it was deleted, not emptied, because an override left in\n# place after its fact lands wins over the manifest, silently.\n"], ["delete the override table", "CARD_OVERRIDES = {\n    # PENDING MANIFEST: the card line. Its registry status lives in Brand Book\n    # §5 and is not restated here.\n    \"line\": \"Vizion, built not borrowed.\",\n    # PENDING MANIFEST: the discipline kicker.\n    \"kicker\": \"AI · SOFTWARE · WEB · BRAND\",\n}\n\n", ""], ["load_facts signature: no overrides list", "               offline: bool = False) -> tuple[dict, list[str], str]:", "               offline: bool = False) -> tuple[dict, str]:"], ["load_facts return: no overrides applied", "    facts.update(CARD_OVERRIDES)\n    return facts, sorted(CARD_OVERRIDES), source\n", "    return facts, source\n"], ["main: unpack two values", "    facts, overrides, source = load_facts(Path(args.profile), args.profile_url,\n                                          args.offline)", "    facts, source = load_facts(Path(args.profile), args.profile_url,\n                               args.offline)"], ["main: the NOT YET IN THE MANIFEST message goes", "\n    if overrides:\n        print(\"\\nNOT YET IN THE MANIFEST — these came from CARD_OVERRIDES:\")\n        for key in overrides:\n            print(f\"  {key} = {CARD_OVERRIDES[key]!r}\")\n        print(\"  Encoding is the Brand Infrastructure project's call. Until it\\n\"\n              \"  lands, this surface is outside drift detection.\")\n", ""]]""")


def state(text, old, new):
    """applied / pending / moved, judged on the edit's own text."""
    if new and new in text:
        return "applied"
    if not new and old not in text:
        return "applied"
    if text.count(old) == 1:
        return "pending"
    return "moved"


def run_generator(source, out):
    """Run one copy of the generator from the repo root, into `out`."""
    r = subprocess.run([sys.executable, str(source), "--out", str(out)],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def prove(original, staged):
    """Both generators, same manifest, byte-compared. Returns (ok, message)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "old.py").write_text(original, encoding="utf-8")
        (tmp / "new.py").write_text(staged, encoding="utf-8")
        results = {}
        for tag in ("old", "new"):
            code, log = run_generator(tmp / f"{tag}.py", tmp / tag)
            if code != 0:
                return False, ("the %s generator did not run, so nothing could be "
                               "proved:\n%s" % (tag, log[-800:]))
            results[tag] = log
        moved = [f for f in OUTPUTS
                 if (tmp / "old" / "card" / f).read_bytes()
                 != (tmp / "new" / "card" / f).read_bytes()]
        if moved:
            return False, "the edit would change the card: " + ", ".join(moved)
        stale = [f for f in OUTPUTS
                 if not (ROOT / "card" / f).exists()
                 or (ROOT / "card" / f).read_bytes()
                 != (tmp / "new" / "card" / f).read_bytes()]
        src = next((l for l in results["new"].splitlines()
                    if l.startswith(("manifest:", "version:"))), "")
        msg = ["all five outputs byte-identical, old generator vs new (%s)" % src.strip()]
        if stale:
            msg.append("NOTE, separate from this change: the committed card/ differs "
                       "from what the manifest now produces (%s). Regenerating is "
                       "its own decision." % ", ".join(stale))
        else:
            msg.append("the committed card/ already matches: nothing to regenerate")
        return True, "\n  ".join(msg)


def main():
    check = "--check" in sys.argv[1:]
    if not TARGET.exists():
        sys.exit("%s not found -- wrong repo? This is for rnvizion.github.io." % REL)
    original = TARGET.read_text(encoding="utf-8")

    states = [state(original, old, new) for _, old, new in EDITS]
    if all(s == "applied" for s in states):
        print("already applied -- %s reads both values from the manifest. "
              "Nothing to do." % REL)
        return 0
    if any(s != "pending" for s in states):
        bad = [name for (name, _, _), s in zip(EDITS, states) if s != "pending"]
        sys.exit("REFUSED: %s is partly changed or has moved since 2b8ea3a (%s).\n"
                 "Nothing was written; re-cut this against live." % (REL, "; ".join(bad)))

    staged = original
    for _, old, new in EDITS:
        staged = staged.replace(old, new, 1)

    ok, message = prove(original, staged)
    print("proof: " + message)
    if not ok:
        sys.exit("\nREFUSED: nothing was written.")

    print()
    for name, _, _ in EDITS:
        print("  %s %s" % ("would" if check else "done ", name))
    print()
    print("Left alone, deliberately:")
    print("  - card/ itself. The outputs don't change, so there is nothing to commit there.")
    print("  - whether CI runs this generator. It stays hand-run; that's a separate call.")
    if check:
        print("\n--check: nothing written.")
        return 0

    TARGET.write_text(staged, encoding="utf-8")
    print()
    print("  git add %s" % REL)
    print('  git commit -m "contact card: read the line and kicker from the manifest"')
    print("Then delete this runner rather than committing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
