#!/usr/bin/env bash
set -euo pipefail

REPO="loudply0-eng/Universal-Translator-Builder"
KEY_ALIAS="universal-translator"
KEYSTORE_PATH="${KEYSTORE_PATH:-./universal-translator-release.jks}"

command -v keytool >/dev/null 2>&1 || {
  echo "keytool is required. Install a JDK (Java 17 or newer) first." >&2
  exit 1
}
command -v gh >/dev/null 2>&1 || {
  echo "GitHub CLI (gh) is required." >&2
  exit 1
}
gh auth status --hostname github.com >/dev/null

if [[ -e "$KEYSTORE_PATH" ]]; then
  echo "Refusing to overwrite existing keystore: $KEYSTORE_PATH" >&2
  exit 1
fi

read -r -s -p "Choose a strong signing password (at least 20 characters): " SIGNING_PASSWORD
printf '\n'
read -r -s -p "Re-enter signing password: " SIGNING_PASSWORD_CONFIRM
printf '\n'

if [[ ${#SIGNING_PASSWORD} -lt 20 || "$SIGNING_PASSWORD" != "$SIGNING_PASSWORD_CONFIRM" ]]; then
  echo "Passwords must match and contain at least 20 characters." >&2
  unset SIGNING_PASSWORD SIGNING_PASSWORD_CONFIRM
  exit 1
fi
unset SIGNING_PASSWORD_CONFIRM

export SIGNING_PASSWORD
umask 077
mkdir -p "$(dirname "$KEYSTORE_PATH")"

keytool -genkeypair -v \
  -keystore "$KEYSTORE_PATH" \
  -storetype JKS \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -alias "$KEY_ALIAS" \
  -storepass:env SIGNING_PASSWORD \
  -keypass:env SIGNING_PASSWORD \
  -dname "CN=Universal Translator, OU=Android, O=loudply0-eng, C=IQ" \
  -noprompt

chmod 600 "$KEYSTORE_PATH"

KEYSTORE_BASE64="$(base64 -w0 "$KEYSTORE_PATH")"
printf '%s' "$KEYSTORE_BASE64" | gh secret set ANDROID_KEYSTORE_BASE64 --repo "$REPO"
printf '%s' "$SIGNING_PASSWORD" | gh secret set ANDROID_KEYSTORE_PASSWORD --repo "$REPO"
printf '%s' "$KEY_ALIAS" | gh secret set ANDROID_KEY_ALIAS --repo "$REPO"
printf '%s' "$SIGNING_PASSWORD" | gh secret set ANDROID_KEY_PASSWORD --repo "$REPO"

echo
echo "All four Android signing secrets were uploaded to $REPO."
echo "Keystore backup: $KEYSTORE_PATH"
echo "Keep this keystore and its password in two secure backups. Never commit or send them."
keytool -list -v -keystore "$KEYSTORE_PATH" -storepass:env SIGNING_PASSWORD -alias "$KEY_ALIAS" \
  | grep -E 'Alias name:|SHA256:'
unset SIGNING_PASSWORD KEYSTORE_BASE64
