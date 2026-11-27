# Universal Translator Builder

Public automation repository for building, verifying, and publishing signed Android releases of Universal Translator.

The application source is maintained privately in [Universal-Translator](https://github.com/loudply0-eng/Universal-Translator). This repository checks out that source, prepares the Android project, runs Flutter analysis and tests, builds the APK, verifies the persistent release signature, generates SHA-256 metadata, and publishes the official release when explicitly marked.

## Current version

- Private source candidate: **0.3.4+8**
- Latest published official release before this build: **0.3.3+7**
- Android application package: `com.loudply.universaltranslator.universal_translator`
- Official release APK name: `universal-translator.apk`

## Application capabilities

The current private source includes:

- Arabic-first right-to-left interface with 49 manually selectable languages and online translation through MyMemory.
- Offline translation using downloadable Google ML Kit language models.
- Android text selection and share-sheet support for text, screenshots, and images.
- On-device OCR: bundled Arabic Tesseract model and ML Kit for supported other scripts.
- Searchable PDF, DOCX, TXT, and Markdown document extraction and translation.
- Two-person bilingual conversation mode with speech recognition and spoken translations.
- Continuous speech translation for lectures and meetings, with a copyable transcript.
- Draggable and resizable floating translation window.
- Android screen sharing through the system MediaProjection consent dialog, with live preview and user-triggered frame capture for OCR. Extracted text can be translated online or offline and displayed in the floating window.
- Local phrasebook, flashcard review, favorites, translation history, and appearance preferences.
- In-app update checks with Arabic release notes, percentage and byte progress, resumable downloads, automatic retries, and SHA-256 verification before Android's installer is opened.

Screen sharing is started only after the user approves Android's system prompt. Android displays a foreground-service notification while sharing. The user chooses when to capture a frame; the app does not silently read other apps or continuously translate screen contents. The temporary capture frame is deleted after on-device OCR finishes. Secure or DRM-protected content may not be capturable.

See the private source repository's `PRIVACY.md` for data-handling details.

## Private-source connection

The build workflow uses a fine-grained, read-only GitHub token to check out the private source. The token must be stored only as the `SOURCE_REPO_TOKEN` repository Actions secret. It must be scoped to the single private `Universal-Translator` repository with Contents: Read-only permission. Never place the token in source files, workflow logs, or chat messages.

## Persistent Android release signing

Production APKs are signed with a persistent JKS keystore. The keystore and its passwords remain in the Oracle backup and GitHub Actions secrets; they must never be committed to this repository.

The workflow refuses to publish when persistent signing is unavailable. It verifies the signing certificate before upload, computes the APK SHA-256 digest, and publishes both the APK and checksum.

**Upgrade warning:** development APKs signed with temporary CI keys cannot be updated in place by the production-signed release. Users on such builds must uninstall the development build and install the first production-signed APK. Local app data may be removed.

## Build and release procedure

Every push to `main` runs the build and security workflows. A routine push creates a verification artifact but does not publish a release.

To publish an official release:

1. Increment the version in the private source `pubspec.yaml` using `MAJOR.MINOR.PATCH+BUILD`.
2. Add a matching Arabic-only section to the top of the private source `CHANGELOG.md`.
3. Update the exact official-release marker in `.github/workflows/build-android.yml`.
4. Commit the builder change to `main` with a message containing the exact marker, for example `[official-release:v0.3.4+8]`.

The release workflow then checks out the private source, runs analysis and tests, builds and verifies the APK, creates its checksum and build manifest, and publishes the signed GitHub Release. The application updater checks this public Builder repository for the latest release.

## Security checks

The security workflow scans builder and private-source Git history for leaked secrets, checks dependencies for known vulnerabilities, runs Flutter analysis, and executes the test suite. Private-source credentials are not exposed to pull-request workflows.
