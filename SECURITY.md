# Security Policy

## Supported Versions

Only the latest commit on `main` is actively supported with security fixes.

## Reporting a Vulnerability

If you discover a security vulnerability in DocuStruct, please **do not** open a public issue.

Instead, report it privately by emailing the maintainer or opening a confidential issue on
the project's GitLab repository (Issues → New Issue → mark as "Confidential").

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, including any proof-of-concept code.
- Affected file(s)/commit hash, if known.

You can expect an initial response within 5 business days. We will keep you updated as the
issue is triaged and fixed, and credit you in the release notes unless you prefer otherwise.

## Scope

DocuStruct is an offline, local-only pipeline (no external API calls). Reports of interest
include, but are not limited to:

- Path traversal or unsafe file handling in `ingest/`, `storage/`, or upload handling.
- SQL injection in `storage/db.py`.
- Arbitrary code execution via crafted receipt images or cached OCR artifacts.
- Dependency vulnerabilities flagged by `pip-audit`.
