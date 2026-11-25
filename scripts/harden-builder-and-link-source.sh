#!/usr/bin/env bash
set -Eeuo pipefail

BUILDER="loudply0-eng/Universal-Translator-Builder"
SOURCE="loudply0-eng/Universal-Translator"
BRANCH="main"

echo "== Universal Translator: builder hardening + private source link =="

command -v gh >/dev/null 2>&1 || { echo "ERROR: GitHub CLI (gh) is missing."; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "ERROR: gh is not authenticated. Run gh auth login first."; exit 1; }

BUILDER_PRIVATE="$(gh repo view "$BUILDER" --json isPrivate --jq '.isPrivate')"
SOURCE_PRIVATE="$(gh repo view "$SOURCE" --json isPrivate --jq '.isPrivate')"
[[ "$BUILDER_PRIVATE" == "false" ]] || { echo "ERROR: builder must remain PUBLIC."; exit 1; }
[[ "$SOURCE_PRIVATE" == "true" ]] || { echo "ERROR: source repository is not PRIVATE; stopping."; exit 1; }

echo "[1/4] Restricting GitHub Actions permissions on public builder..."
if gh api --method PUT "repos/$BUILDER/actions/permissions/workflow" -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false >/dev/null 2>&1; then
  echo "OK: workflow default token is read-only."
else
  echo "NOTICE: could not set workflow token policy (check GitHub permissions)."
fi
if gh api --method PUT "repos/$BUILDER/actions/permissions" -F enabled=true -f allowed_actions=all >/dev/null 2>&1; then
  echo "OK: GitHub Actions enabled."
else
  echo "NOTICE: could not update Actions repository policy."
fi
if gh api --silent --method PUT "repos/$BUILDER/vulnerability-alerts" >/dev/null 2>&1; then
  echo "OK: builder vulnerability alerts enabled."
fi
if gh api --silent --method PUT "repos/$BUILDER/automated-security-fixes" >/dev/null 2>&1; then
  echo "OK: builder automated security fixes enabled."
fi

echo "[2/4] Attempting main branch protection..."
PROTECTION='{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'
if gh api --method PUT "repos/$BUILDER/branches/$BRANCH/protection" --input - <<<"$PROTECTION" >/dev/null 2>&1; then
  echo "OK: builder main protected against force-push and deletion."
else
  echo "NOTICE: GitHub rejected branch protection (plan or permission limitation)."
fi

echo "[3/4] Securely configuring SOURCE_REPO_TOKEN..."
echo "Create a fine-grained token at:"
echo "https://github.com/settings/personal-access-tokens/new"
echo "Set resource owner: loudply0-eng"
echo "Repository access: Only select repositories -> Universal-Translator"
echo "Repository permissions: Contents = Read-only (no other permissions)."
echo "Create the token, then paste it at the hidden prompt below."
read -r -s -p "Fine-grained token (input hidden): " SOURCE_TOKEN
echo
[[ -n "$SOURCE_TOKEN" ]] || { echo "ERROR: no token supplied. Hardening completed; secret not configured."; exit 2; }

echo "$SOURCE_TOKEN" | GH_TOKEN="$SOURCE_TOKEN" gh api "repos/$SOURCE" >/dev/null 2>&1 || {
  unset SOURCE_TOKEN
  echo "ERROR: token cannot read the private source repository. Recreate it with Contents: Read-only."
  exit 3
}
if ! printf '%s' "$SOURCE_TOKEN" | gh secret set SOURCE_REPO_TOKEN --repo "$BUILDER" 2>/dev/null; then
  unset SOURCE_TOKEN
  echo "ERROR: could not save SOURCE_REPO_TOKEN as an Actions secret."
  exit 4
fi
unset SOURCE_TOKEN
echo "OK: SOURCE_REPO_TOKEN saved as an encrypted Actions secret; token was not printed."

echo "[4/4] Starting Android build..."
gh workflow run build-android.yml --repo "$BUILDER" --ref main
echo "OK: build workflow dispatched."
echo
echo "Check build status with:"
echo "gh run list --repo $BUILDER --workflow build-android.yml --limit 3"
echo "If successful, download the APK artifact from the Actions run page."
echo
echo "NOTE: this stage does not yet create Android signing keys or in-app updater."
