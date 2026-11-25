# Security Policy

## Reporting a vulnerability

Do not publish credentials, tokens, or exploit details in public issues. Report suspected vulnerabilities privately to the repository owner through GitHub's private reporting options when available.

## Repository boundaries

This repository contains build automation only. The application source belongs in the private `Universal-Translator` repository and must never be copied into this public repository.

## Secrets

Never commit personal access tokens, signing keys, passwords, keystores, or private application source. The `SOURCE_REPO_TOKEN` must remain an Actions secret and should be a fine-grained token restricted to the private source repository with Contents read-only permission.
