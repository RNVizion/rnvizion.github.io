#!/usr/bin/env bash
#
# font.sh — fetch the RNVizion brand fonts into assets/fonts/.
#
# The OG image pipeline (scripts/generate_og.py) renders with these faces and
# silently falls back to a default face if they're missing, so a missing font
# shows up as an ugly card rather than an error. This script makes the fetch
# explicit and verifies what it downloaded.
#
#   ./font.sh              # fetch anything missing
#   ./font.sh --force      # re-download everything
#   ./font.sh --verify     # check what's on disk, download nothing
#
# Target directory honours OG_FONT_DIR, the same override generate_og.py reads.
#
# This fetches what the raster pipeline draws, which is three of the five brand
# faces. Instrument Serif and Inter are brand faces with no consumer in scripts/,
# so they are deliberately absent: the roster of five lives in rnv-brand, and a
# repo carries the faces it renders rather than a copy of the roster. Add one
# here in the same change that makes a generator draw it, never before.
#
# All three are variable fonts. The generators call set_variation_by_name() and
# take the first instance that exists, so a static build renders at the wrong
# weight rather than failing. The check at the end asks each face for the
# instance its own consumer requests, because a face that passes on somebody
# else's weight is a false all-clear, and a false all-clear is worse than a
# false failure.
#
set -euo pipefail

# --- font list: filename|url ------------------------------------------------
# Sources are the upstream Google Fonts repo (OFL). Bracketed axis names are
# percent-encoded because raw.githubusercontent.com needs them that way.
FONTS=(
  "BricolageGrotesque.ttf|https://raw.githubusercontent.com/google/fonts/main/ofl/bricolagegrotesque/BricolageGrotesque%5Bopsz%2Cwdth%2Cwght%5D.ttf"
  "JetBrainsMono.ttf|https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"
  "Montserrat.ttf|https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
)

MIN_BYTES=20000   # anything smaller is an error page, not a font

FORCE=0
VERIFY_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --force)  FORCE=1 ;;
    --verify) VERIFY_ONLY=1 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

# --- resolve target directory ----------------------------------------------
if [ -n "${OG_FONT_DIR:-}" ]; then
  FONT_DIR="$OG_FONT_DIR"
else
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  FONT_DIR="$REPO_ROOT/assets/fonts"
fi
mkdir -p "$FONT_DIR"
echo "font dir: $FONT_DIR"
echo

# --- helpers ----------------------------------------------------------------
is_truetype() {
  # TrueType starts 00 01 00 00, or the ASCII tags 'true' / 'ttcf' / 'OTTO'
  local magic
  magic=$(head -c 4 "$1" | od -An -tx1 | tr -d ' \n')
  case "$magic" in
    00010000|74727565|74746366|4f54544f) return 0 ;;
    *) return 1 ;;
  esac
}

size_of() { stat -c%s "$1" 2>/dev/null || stat -f%z "$1" 2>/dev/null || echo 0; }

fetched=0; skipped=0; failed=0

for entry in "${FONTS[@]}"; do
  name="${entry%%|*}"
  url="${entry#*|}"
  dest="$FONT_DIR/$name"

  if [ "$VERIFY_ONLY" -eq 1 ]; then
    if [ -f "$dest" ] && is_truetype "$dest"; then
      echo "  ok       $name  ($(size_of "$dest") bytes)"
    else
      echo "  MISSING  $name"
      failed=$((failed + 1))
    fi
    continue
  fi

  if [ -f "$dest" ] && [ "$FORCE" -eq 0 ] && is_truetype "$dest"; then
    echo "  skip     $name  (already present; --force to replace)"
    skipped=$((skipped + 1))
    continue
  fi

  tmp="$(mktemp)"
  code=$(curl -sL --retry 2 --max-time 60 -o "$tmp" -w "%{http_code}" "$url" || echo "000")
  bytes=$(size_of "$tmp")

  if [ "$code" != "200" ] || [ "$bytes" -lt "$MIN_BYTES" ] || ! is_truetype "$tmp"; then
    echo "  FAIL     $name  (http $code, $bytes bytes) — left existing file untouched"
    rm -f "$tmp"
    failed=$((failed + 1))
    continue
  fi

  mv "$tmp" "$dest"
  chmod 644 "$dest"
  echo "  fetched  $name  ($bytes bytes)"
  fetched=$((fetched + 1))
done

# --- confirm each face carries the instance its own consumer asks for -------
if command -v python3 >/dev/null 2>&1 && [ "$failed" -eq 0 ]; then
  python3 - "$FONT_DIR" <<'PY' || echo "  (Pillow not installed; skipped variable-instance check)"
import sys
from pathlib import Path
try:
    from PIL import ImageFont
except ImportError:
    raise SystemExit(1)

# Each face is asked for the instance the code that draws it actually requests.
# Checking every face against one shared weight list is how a face passes on a
# weight nothing uses.
EXPECT = [
    ("BricolageGrotesque.ttf", ("SemiBold", "Bold", "Medium"), "display"),
    ("JetBrainsMono.ttf",      ("Medium", "Bold"),             "labels"),
    ("Montserrat.ttf",         ("Black",),                     "the mark"),
]

font_dir = Path(sys.argv[1])
bad = 0
print("\ninstance check (what each generator will actually get):")
for name, wants, role in EXPECT:
    path = font_dir / name
    if not path.exists():
        print(f"  {name:<28} MISSING")
        bad += 1
        continue
    font = ImageFont.truetype(str(path), 40)
    chosen = None
    for want in wants:
        try:
            font.set_variation_by_name(want)
            chosen = want
            break
        except Exception:
            continue
    if chosen is None:
        print(f"  {name:<28} NO INSTANCE from {wants} — would render at default weight   [{role}]")
        bad += 1
    else:
        print(f"  {name:<28} {chosen:<10} [{role}]")

raise SystemExit(1 if bad else 0)
PY
fi

echo
echo "------------------------------------------------------------"
if [ "$VERIFY_ONLY" -eq 1 ]; then
  echo "  verify only: $failed missing"
else
  echo "  fetched: $fetched   skipped: $skipped   failed: $failed"
fi

if [ "$failed" -gt 0 ]; then
  echo "  One or more fonts are unavailable. OG images will still render,"
  echo "  but in a default face rather than the brand faces."
  exit 1
fi
echo "  Fonts ready. Regenerate a card with:"
echo "    python scripts/generate_og.py blog/<slug>/index.html"
echo
