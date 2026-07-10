# DocuStruct Constitution

## Purpose
DocuStruct is an offline-first, CPU-only document intelligence pipeline. Every design
decision must preserve that constraint.

## Core Principles

1. **Offline-only.** No network calls at runtime — no external APIs, no telemetry.
2. **CPU-only.** No hard dependency on GPU acceleration.
3. **Deterministic where possible.** Rule-based extraction is preferred; the optional
   local LLM extractor must be swappable, not required.
4. **Testable.** Every pipeline stage (ingest, extract, validate, store) must have
   corresponding tests in `tests/`.
5. **Minimal dependencies.** New third-party packages require justification in the PR
   description and must pass `pip-audit`.

## Spec-Driven Development

New features are proposed as a spec under `specs/<feature-name>/spec.md`, broken into a
`plan.md` and `tasks.md` using the templates in `.specify/templates/` before
implementation begins.
