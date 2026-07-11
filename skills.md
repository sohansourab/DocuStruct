# Skills

This repository uses a skill-based structure to guide AI assistants toward the right domain knowledge and source files.

## Existing skills

- `.agents/skills/developing-with-streamlit/SKILL.md`
  - Use for all Streamlit-related development, debugging, UI design, layout changes, component work, and app configuration.

## What a skill is

A skill is a directory under `.agents/skills/` containing a `SKILL.md` file. The `SKILL.md` file defines:

- the skill name
- the task scope and trigger phrases
- how to identify and route relevant work
- the workflow for editing and validating code
- references for deeper domain knowledge

## When to add a new skill

Create a new skill when a request falls outside the existing Streamlit scope and has a clear domain:

- a different frontend framework or UI toolkit
- a specialized backend subsystem
- a distinct integration or infrastructure workflow

The new skill should live under `.agents/skills/<skill-name>/` and include a `SKILL.md` file.

## How to use skills

1. Read `AGENTS.md` first for repository-wide constraints and goals.
2. If the user request matches a skill trigger, use the corresponding `SKILL.md`.
3. If the request is broader or cross-cutting, use `AGENTS.md` plus one or more skill docs.

## Why this matters

Skills help maintain consistent behavior across agents and ensure changes follow repository conventions. They also make it easier to keep domain-specific guidance close to the relevant code.
