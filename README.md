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

Then open Actions → **Build Universal Translator APK** → Run workflow. The workflow checks out the private source, generates the Android platform folder, runs analysis/tests, and uploads the release APK as a workflow artifact.

## Release security
- Keep the source repository private.
- Keep the source token read-only and scoped to the one private repository.
- Release signing keys and passwords must be stored only as Actions secrets.
- Publish signed, versioned releases for in-app update checks.
- Android requires the user to confirm installation of an update on ordinary non-rooted devices.

## Current application capabilities

The private application currently includes:
- Arabic-first text translation through the MyMemory HTTPS API.
- On-device source-language detection before sending translation requests.
- Local translation history and favorites, stored on the device (up to 100 records).
- Exact-match local translation cache to reuse saved results and reduce repeat API usage.
- Automated Flutter analysis and unit/widget tests before an APK is uploaded.
- Each build artifact includes a SHA-256 checksum and a build manifest recording the exact private-source commit.

Not yet implemented: voice translation, OCR/screen capture, floating translation overlay, signed production releases, and in-app update installation. The current APK is a development artifact, not a production-ready release.

See the private source repository's `PRIVACY.md` for current text-processing and local-storage behavior.

The first build workflow is at `.github/workflows/build-android.yml`.
