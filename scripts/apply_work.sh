#!/usr/bin/env bash
set -euo pipefail

# Download and checkout the latest version of this repo's "work" branch.
# Useful when the IDE "Apply" button fails and you want to test the pending changes locally.

REMOTE=${REMOTE:-origin}
BRANCH=${BRANCH:-work}
TARGET_BRANCH=${TARGET_BRANCH:-apply-work}

# Ensure we are inside the repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run inside a git repository." >&2
  exit 1
fi

# Fetch and create/update the local branch that mirrors REMOTE/BRANCH
echo "Fetching ${BRANCH} from ${REMOTE} ..."
git fetch "${REMOTE}" "${BRANCH}:${TARGET_BRANCH}"

# Switch to the target branch so you can inspect or merge it
if git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  git checkout "${TARGET_BRANCH}"
else
  echo "Failed to create local branch ${TARGET_BRANCH}." >&2
  exit 1
fi

echo
echo "Checked out ${TARGET_BRANCH}. If everything looks good, merge it into your main branch, e.g.:"
echo "  git checkout main"
echo "  git merge ${TARGET_BRANCH}"
