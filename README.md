# Universal Translator Builder

Public automation repository for building, verifying, and publishing signed Android releases of Universal Translator.

The application source is maintained privately in [Universal-Translator](https://github.com/loudply0-eng/Universal-Translator). This repository checks out that source, prepares Android files, runs Flutter analysis and tests, builds the APK, verifies its production signature and bundled OCR assets, and publishes the official release when the exact version marker is present.

## Current candidate

- Source version: **0.3.5+9**
- Previous official release: **0.3.4+8**
- Application ID: `com.loudply.universaltranslator.universal_translator`
- Published APK: `universal-translator.apk`

## Current features

- Arabic-first translation with online and on-device offline modes.
- 49 online language choices, voice input and spoken translation.
- Live lecture translation with independent speaker and target language selectors, plus optional automatic spoken output.
- Compact, adjustable screen preview with user-approved Android MediaProjection capture.
- Local OCR with an accuracy-focused Arabic Tesseract model, image orientation correction, enlargement, contrast tuning, and editable text review.
- Translation of searchable PDF, DOCX, TXT and Markdown documents.
- Two-person conversation, phrasebook, history, favorites and floating translation overlay.
- Image export that preserves the original picture and adds a translated-text panel; it is shared only after the user presses the share action.
- Arabic release notes, resumable update downloads, SHA-256 verification, and explicit Android installer confirmation.

## OCR asset verification

The Arabic OCR file is pinned to the Tesseract `tessdata_best` upstream Git blob. The workflow verifies its exact size and Git blob SHA-1 before building and verifies the packaged asset again inside the APK. The Apache-2.0 license is fetched from the separately pinned `tessdata_fast` license path because the best-model repository does not contain a license file at that revision.

## Private source and secrets

The build workflow uses the `SOURCE_REPO_TOKEN` Actions secret to check out the private source. It must be a fine-grained, read-only token scoped only to the `Universal-Translator` repository.

The persistent Android JKS keystore and its passwords remain exclusively in Actions secrets and the user's secure backups. Never commit or print the signing key, passwords, tokens, or Oracle credentials. The workflow refuses to publish if persistent signing is unavailable.

## Build and release procedure

Every push to `main` runs the build and security workflows. To publish an official release:

1. Increment `version` in the private source `pubspec.yaml`.
2. Add a matching Arabic-only section at the top of the private source `CHANGELOG.md`.
3. Update both exact release markers in `.github/workflows/build-android.yml`.
4. Commit the builder change with a message containing the marker, for example `[official-release:v0.3.5+9]`.

The release workflow runs dependency resolution, Flutter analysis, tests, APK build, certificate verification, OCR asset checks, SHA-256 generation and release publication. The app's updater checks this public Builder repository.
