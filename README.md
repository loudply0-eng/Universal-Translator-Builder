# Universal Translator Builder

Public automation repository for building and publishing Universal Translator Android releases.

The application source is maintained privately in [Universal-Translator](https://github.com/loudply0-eng/Universal-Translator).

## One-time connection to the private source

Create a **fine-grained personal access token** in GitHub:
1. Open GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens.
2. Set the resource owner to `loudply0-eng`.
3. Grant access to **only** `Universal-Translator`.
4. Under Repository permissions, set **Contents: Read-only**.
5. Generate the token, then open this public repository's Settings → Secrets and variables → Actions → New repository secret.
6. Set the secret name to `SOURCE_REPO_TOKEN` and paste the token as its value. Never put it in a file or message.

Then open Actions → **Build Universal Translator APK** → Run workflow. The workflow checks out the private source, generates the Android platform folder, declares and verifies network/package-installer permissions, runs analysis/tests, and uploads the APK, checksum, and source/build manifest as a workflow artifact.

## One-time Android production signing

The APK can be built without signing secrets for development, but that output uses a temporary CI debug key and cannot be used as a reliable upgrade target.

Before the first production release, clone this repository on a machine with a JDK and GitHub CLI, authenticate with `gh auth login`, then run from the repository root:

```bash
bash scripts/setup-android-signing.sh
```

The script creates a persistent JKS keystore locally and uploads these four secrets to this repository without printing their values:
- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

It refuses to overwrite an existing keystore. Back up `universal-translator-release.jks` and its password securely in more than one place. Losing either means future APKs cannot be signed as compatible updates. Never commit, email, or paste the keystore or passwords into chat.

After the secrets are present, open Actions → **Build Universal Translator APK** → Run workflow. Keep `publish_release` disabled for a test build. To publish a production update, first increment `version` in the private source `pubspec.yaml` (format `MAJOR.MINOR.PATCH+BUILD`), then run the workflow with `publish_release` enabled. The workflow refuses to publish if persistent signing is unavailable or that version's release tag already exists.

**Upgrade warning:** the earlier development APKs use temporary CI debug certificates. Android will not let a production-signed APK update one of those installs. Before moving to the first persistent-key release, uninstall the development build and install the signed release; local app data may be removed.

## Release security
- Keep the source repository private.
- Keep the source token read-only and scoped to the one private repository.
- Release signing keys and passwords must be stored only as Actions secrets.
- Publish signed, versioned releases for in-app update checks.
- Android requires the user to confirm installation of an update on ordinary non-rooted devices.

## Current application capabilities

The private application currently includes:
- Arabic-first text translation through a provider interface, currently backed by the MyMemory HTTPS API.
- On-device source-language detection before sending translation requests.
- Local translation history and favorites, stored on the device (up to 100 records).
- Persistent device-local source and target language preferences.
- A history privacy switch to stop saving new records and disable cache reuse without deleting existing records.
- Exact-match local translation cache to reuse saved results and reduce repeat API usage.
- Provider-injection contract tests plus automated Flutter analysis and unit/widget tests before an APK is uploaded.
- Each build artifact includes a SHA-256 checksum and a build manifest recording the exact private-source commit.

Implemented in the app: release-update checking, explicit user approval, APK SHA-256 verification, and Android installer handoff. Not yet production-ready: stable release signing and publishing a signed GitHub Release containing `universal-translator.apk` with a SHA-256 asset digest. Voice translation, OCR/screen capture, and floating translation overlay are also not implemented. The current APK is a development artifact, not a production-ready release.

See the private source repository's `PRIVACY.md` for current text-processing and local-storage behavior.

The first build workflow is at `.github/workflows/build-android.yml`.
