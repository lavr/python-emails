#!/usr/bin/env bash
set -euo pipefail

# --- Check for uncommitted changes ---
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: there are uncommitted changes. Commit or stash them first."
    exit 1
fi

# --- Read current version ---
VERSION_FILE="emails/__init__.py"
CHANGELOG="CHANGELOG.md"

current=$(grep -oP "^__version__ = '\K[^']+" "$VERSION_FILE")
if [[ -z "$current" ]]; then
    echo "Error: could not read version from $VERSION_FILE"
    exit 1
fi

IFS='.' read -r major minor patch <<< "$current"
patch=${patch:-0}
minor=${minor:-0}

v_patch="$major.$minor.$((patch + 1))"
v_minor="$major.$((minor + 1)).0"
v_major="$((major + 1)).0.0"

echo "Current version: $current"
echo ""
echo "  1) patch  -> $v_patch"
echo "  2) minor  -> $v_minor"
echo "  3) major  -> $v_major"
echo ""
read -rp "Choose [1/2/3]: " choice

case "$choice" in
    1) new_version="$v_patch" ;;
    2) new_version="$v_minor" ;;
    3) new_version="$v_major" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "Releasing $current -> $new_version"
echo ""

# --- Update version in emails/__init__.py ---
sed -i.bak "s/^__version__ = '${current}'/__version__ = '${new_version}'/" "$VERSION_FILE"
rm -f "${VERSION_FILE}.bak"

# --- Update CHANGELOG: add date to the release heading ---
today=$(date +%Y-%m-%d)
sed -i.bak "s/^## ${new_version}$/## ${new_version} — ${today}/" "$CHANGELOG"
# Also handle case where heading doesn't have the version yet (uses Unreleased)
sed -i.bak "s/^## Unreleased$/## ${new_version} — ${today}/" "$CHANGELOG"
rm -f "${CHANGELOG}.bak"

# --- Commit and tag ---
git add "$VERSION_FILE" "$CHANGELOG"
git commit -m "Release v${new_version}"
git tag "v${new_version}"

echo ""
echo "Done. Created commit and tag v${new_version}."
echo "Run 'git push && git push --tags' to publish."
