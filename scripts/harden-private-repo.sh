#!/usr/bin/env bash
set -Eeuo pipefail

REPO="loudply0-eng/Universal-Translator"
BRANCH="main"

echo "== Universal Translator: private repository hardening =="
command -v gh >/dev/null 2>&1 || { echo "ERROR: GitHub CLI (gh) is not installed."; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "ERROR: gh is not authenticated on this Oracle server. Run: gh auth login"; exit 1; }

VISIBILITY="$(gh repo view "$REPO" --json isPrivate --jq '.isPrivate')"
DEFAULT_BRANCH="$(gh repo view "$REPO" --json defaultBranchRef --jq '.defaultBranchRef.name')"
[[ "$VISIBILITY" == "true" ]] || { echo "ERROR: $REPO is not private; refusing to change settings."; exit 1; }
[[ "$DEFAULT_BRANCH" == "$BRANCH" ]] || { echo "ERROR: expected default branch main, found $DEFAULT_BRANCH."; exit 1; }

api_put() {
  local endpoint="$1"
  if gh api --silent --method PUT "$endpoint" >/dev/null 2>&1; then
    echo "OK: $endpoint"
  else
    echo "NOTICE: GitHub did not enable $endpoint (permission or plan limitation may apply)."
  fi
}

# Turn on Dependabot security alerts and automatic security fixes.
api_put "repos/$REPO/vulnerability-alerts"
api_put "repos/$REPO/automated-security-fixes"

# Protect main against force-pushes and branch deletion.
# Direct pushes remain possible for the repository owner; this avoids locking out a solo maintainer.
PROTECTION='{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": { "enabled": true }
}'
if gh api --method PUT "repos/$REPO/branches/$BRANCH/protection" --input - <<<"$PROTECTION" >/dev/null 2>&1; then
  echo "OK: main branch protected against force-push and deletion."
else
  echo "NOTICE: branch protection was not accepted by GitHub. This can depend on the account plan or permissions."
fi

echo
echo "Private-repository baseline completed. No files were deleted and no secrets were printed."
echo "Next stage: harden the public builder, then configure the scoped source token and signed in-app update pipeline."
