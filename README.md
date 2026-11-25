# Universal Translator Builder

Public automation repository for building and publishing Universal Translator Android releases.

The application source is maintained privately in [Universal-Translator](https://github.com/loudply0-eng/Universal-Translator).

## Build security
The build workflow will read the private source repository using a fine-grained, read-only GitHub token stored as the `SOURCE_REPO_TOKEN` Actions secret. Never commit that token, signing keystore, or signing passwords.

## Release requirements
- Build and test the private Flutter/Android source on GitHub-hosted Linux runners.
- Sign release APKs with a persistent Android signing key held only in Actions secrets.
- Publish versioned GitHub Releases and release metadata for in-app update checks.
- The app must ask Android to install an update; Android's installer confirmation cannot be silently bypassed on ordinary devices.

A build workflow will be enabled once the first compilable application source is committed to the private repository.
