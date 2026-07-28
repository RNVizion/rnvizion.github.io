#!/usr/bin/env bash
#
# rename_assets.sh — bring project card images in line with the rnv- repo names.
#
# Renames every project screenshot in assets/ to match its repo slug, and
# rewrites every reference to it across all tracked text files (not just
# index.html), so nothing ends up pointing at a file that moved.
#
#   ./rename_assets.sh             # show the plan, confirm, then do it
#   ./rename_assets.sh --yes       # skip the confirmation
#   ./rename_assets.sh --dry-run   # show the plan and stop
#   ./rename_assets.sh --no-push   # commit locally, don't push
#
# NOT touched, deliberately:
#   assets/og/*            generated per-post OG images, keyed to post slugs
#   assets/og-image.png    site-wide default OG image, not a project card
#   assets/brand/*         brand marks, a different category
#
set -euo pipefail

# old|new — project screenshots only
RENAMES=(
  "ask-the-corpus.png|rnv-ask-the-corpus.png"
  "color-mcp.png|rnv-color-mcp.png"
  "color-mixer.png|rnv-color-mixer.png"
  "color-palette-manager.png|rnv-color-palette-manager.png"
  "color-picker.png|rnv-color-picker.png"
  "icon-builder.png|rnv-icon-builder.png"
  "text-transformer.png|rnv-text-transformer.png"
  "publishing-agent.png|rnv-publishing-agent.png"
)

ASSUME_YES=0; DO_PUSH=1; DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y)  ASSUME_YES=1 ;;
    --no-push) DO_PUSH=0 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not inside a git repository."
cd "$(git rev-parse --show-toplevel)"
say "repo: $(pwd)"
say ""

# --- plan -------------------------------------------------------------------
say "plan"
say "----"
TO_MOVE=(); MISSING=()
for entry in "${RENAMES[@]}"; do
  old="${entry%%|*}"; new="${entry#*|}"
  if [ -f "assets/$old" ]; then
    refs=$(git grep -l -F "assets/$old" -- . 2>/dev/null | wc -l | tr -d ' ')
    say "  rename   assets/$old  ->  assets/$new   ($refs file(s) reference it)"
    TO_MOVE+=("$entry")
  elif [ -f "assets/$new" ]; then
    say "  done     assets/$new already in place"
  else
    say "  ABSENT   assets/$old  (no image yet; references will still be rewritten)"
    MISSING+=("$new")
    TO_MOVE+=("$entry")   # rewrite refs even with no file, so they point at the new name
  fi
done

if [ "$DRY_RUN" -eq 1 ]; then
  say ""; say "dry run — nothing changed."; exit 0
fi

if [ "$ASSUME_YES" -eq 0 ]; then
  say ""; printf 'proceed? [y/N] '; read -r reply
  case "$reply" in [yY]*) ;; *) say "aborted."; exit 0 ;; esac
fi

# --- move files -------------------------------------------------------------
say ""
moved=0
for entry in "${TO_MOVE[@]}"; do
  old="${entry%%|*}"; new="${entry#*|}"
  if [ -f "assets/$old" ]; then
    git mv "assets/$old" "assets/$new"
    say "  moved    assets/$new"
    moved=$((moved + 1))
  fi
done

# --- rewrite references across every tracked text file ----------------------
say ""
touched=0
for entry in "${TO_MOVE[@]}"; do
  old="${entry%%|*}"; new="${entry#*|}"
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    # portable in-place edit, works with both GNU and BSD sed
    tmp="$(mktemp)"
    sed "s|assets/${old}|assets/${new}|g" "$f" > "$tmp" && mv "$tmp" "$f"
    git add "$f"
    say "  updated  $f  (assets/$old -> assets/$new)"
    touched=$((touched + 1))
  done < <(git grep -l -F "assets/$old" -- . 2>/dev/null || true)
done

# --- verify no stale references survive -------------------------------------
say ""
stale=0
for entry in "${RENAMES[@]}"; do
  old="${entry%%|*}"
  if git grep -q -F "assets/$old" -- . 2>/dev/null; then
    say "  STALE    assets/$old still referenced:"
    git grep -n -F "assets/$old" -- . | sed 's/^/           /'
    stale=$((stale + 1))
  fi
done
[ "$stale" -eq 0 ] && say "  verified: no stale references remain."

# --- commit -----------------------------------------------------------------
if git diff --cached --quiet; then
  say ""; say "nothing staged — already in the desired state."; exit 0
fi

say ""
say "staged:"
git diff --cached --name-status | sed 's/^/  /'

git commit --quiet -m "chore: prefix project card assets with rnv- to match repo names

Asset filenames now mirror their repository slugs. Generated OG images
(assets/og/), the site-wide og-image.png, and assets/brand/ are unchanged."
say ""
say "committed: $(git rev-parse --short HEAD)"

if [ "${#MISSING[@]}" -gt 0 ]; then
  say ""
  say "still needed — these are referenced but have no image yet:"
  for m in "${MISSING[@]}"; do say "  assets/$m"; done
  say "The card falls through to its placeholder until you add one."
fi

if [ "$DO_PUSH" -eq 1 ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    git push origin "$(git rev-parse --abbrev-ref HEAD)" && say "" && say "pushed."
  else
    say "no 'origin' remote; skipping push."
  fi
else
  say ""; say "not pushed. When ready:  git push"
fi
